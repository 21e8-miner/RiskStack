from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from ..deps import get_db
from ..models import Portfolio, Client, ProposalRun, ProposalArtifact, AuditEvent
from ..schemas import ProposalOut
from ..marketdata.prices import load_prices
from ..risk.engine import _to_returns, portfolio_returns, risk_signature, risk_score_from_signature
from ..risk.monte_carlo import simulate_mc, MonteCarloConfig, MonteCarloOutput # Assuming some MC logic here
from ..proposals.renderer import ProposalInputs, render_pdf, inputs_hash
from ._security import current_user

router = APIRouter()

def _get_portfolio_owned(db: Session, u, portfolio_id: int) -> tuple[Portfolio, Client]:
    p = db.query(Portfolio).join(Client, Client.id == Portfolio.client_id).filter(Portfolio.id == portfolio_id, Client.owner_user_id == u.id).one()
    return p, p.client

@router.post("/proposals/{portfolio_id}/generate", response_model=ProposalOut)
def generate(portfolio_id: int, db: Session = Depends(get_db), u=Depends(current_user)):
    p, c = _get_portfolio_owned(db, u, portfolio_id)
    weights = [{"ticker": x.ticker, "weight": x.weight, "kind": x.kind} for x in p.positions]
    w_map = {x["ticker"]: x["weight"] for x in weights if x["kind"] != "cash" and x["weight"] > 0}

    px = load_prices(db, list(w_map.keys()))
    rets = _to_returns(px)
    port_r = portfolio_returns(rets, w_map)

    sig = risk_signature(port_r)
    score, comps = risk_score_from_signature(sig)
    risk = {
        "risk_score": score,
        "components": comps,
        "max_drawdown": sig["max_drawdown"],
        "vol_annual": sig["vol_annual"],
        "downside_vol_annual": sig["downside_vol_annual"],
        "skew": sig["skew"],
        "kurtosis_excess": sig["kurtosis_excess"],
    }
    
    # Simple MC for proposal (using bootstrap default)
    # Note: Using the simulate_mc from risk.monte_carlo
    cfg = MonteCarloConfig(horizon_years=10.0, n_paths=10000)
    # need to convert rets to numpy for simulate_mc
    R = rets.to_numpy(dtype="float64")
    # sort w_map to match R columns if necessary, but load_prices handles that
    tickers = list(rets.columns)
    w = np.array([w_map[t] for t in tickers], dtype="float64")
    
    import numpy as np
    mc_out = simulate_mc(R, w, cfg=cfg)
    mc = {
        "horizon_years": 10.0,
        "n_paths": 10000,
        "p10_terminal": mc_out.p10_terminal,
        "p50_terminal": mc_out.p50_terminal,
        "p90_terminal": mc_out.p90_terminal,
        "prob_shortfall": mc_out.prob_shortfall,
        "worst_path_drawdown_p05": mc_out.worst_path_drawdown_p05,
    }

    as_of = datetime.now(timezone.utc)
    assumptions = {"mc": {"method": "bootstrap", "horizon_years": 10.0, "n_paths": 10000}, "prices": {"source": "price_bars"}}

    inp_obj = {
        "portfolio_id": p.id,
        "as_of": as_of.isoformat(),
        "positions": weights,
        "risk": risk,
        "mc": mc,
        "assumptions": assumptions,
    }
    h = inputs_hash(inp_obj)

    run = ProposalRun(
        portfolio_id=p.id,
        user_id=u.id,
        as_of=as_of,
        inputs_hash=h,
        assumptions=assumptions,
    )
    db.add(run)
    db.flush()

    pdf = render_pdf(
        template_dir="app/proposals/templates",
        inputs=ProposalInputs(
            portfolio_name=p.name,
            client_name=c.name,
            as_of=as_of.date().isoformat(),
            positions=weights,
            risk=risk,
            mc=mc,
            assumptions=assumptions,
        ),
    )

    art = ProposalArtifact(
        proposal_run_id=run.id,
        mime="application/pdf",
        filename=f"proposal_{p.id}_{as_of.date().isoformat()}.pdf",
        content=pdf,
    )
    db.add(art)
    db.add(AuditEvent(user_id=u.id, action="generate", entity_type="proposal", entity_id=str(run.id), payload={"portfolio_id": p.id, "artifact": art.filename}))
    db.commit()
    db.refresh(art)

    return ProposalOut(proposal_run_id=run.id, artifact_id=art.id, filename=art.filename)

@router.get("/proposals/artifacts/{artifact_id}")
def download_artifact(artifact_id: int, db: Session = Depends(get_db), u=Depends(current_user)):
    art = db.query(ProposalArtifact).filter(ProposalArtifact.id == artifact_id).one()
    run = db.query(ProposalRun).filter(ProposalRun.id == art.proposal_run_id, ProposalRun.user_id == u.id).one()
    return Response(content=art.content, media_type=art.mime, headers={"Content-Disposition": f'inline; filename="{art.filename}"'})
