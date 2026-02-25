from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..deps import get_db
from ..models import Portfolio, Position, Client, AuditEvent
from ..schemas import PortfolioCreate, PortfolioOut, PositionIn
from ._security import current_user

router = APIRouter()

@router.post("/portfolios", response_model=PortfolioOut)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db), u=Depends(current_user)):
    client = db.query(Client).filter(Client.id == payload.client_id, Client.owner_user_id == u.id).one()
    p = Portfolio(client_id=client.id, name=payload.name, base_ccy=payload.base_ccy)
    db.add(p)
    db.flush()
    for pos in payload.positions:
        db.add(Position(portfolio_id=p.id, ticker=pos.ticker.upper(), weight=pos.weight, kind=pos.kind))
    db.add(AuditEvent(user_id=u.id, action="create", entity_type="portfolio", entity_id=str(p.id), payload={"name": p.name}))
    db.commit()
    db.refresh(p)
    return PortfolioOut(
        id=p.id,
        client_id=p.client_id,
        name=p.name,
        base_ccy=p.base_ccy,
        positions=[PositionIn(ticker=x.ticker, weight=x.weight, kind=x.kind) for x in p.positions],
    )

@router.get("/portfolios", response_model=list[PortfolioOut])
def list_portfolios(db: Session = Depends(get_db), u=Depends(current_user)):
    ps = db.query(Portfolio).join(Client, Client.id == Portfolio.client_id).filter(Client.owner_user_id == u.id).order_by(Portfolio.id.desc()).all()
    return [
        PortfolioOut(
            id=p.id,
            client_id=p.client_id,
            name=p.name,
            base_ccy=p.base_ccy,
            positions=[PositionIn(ticker=x.ticker, weight=x.weight, kind=x.kind) for x in p.positions],
        )
        for p in ps
    ]

@router.get("/portfolios/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db), u=Depends(current_user)):
    p = db.query(Portfolio).join(Client, Client.id == Portfolio.client_id).filter(Portfolio.id == portfolio_id, Client.owner_user_id == u.id).one()
    return PortfolioOut(
        id=p.id,
        client_id=p.client_id,
        name=p.name,
        base_ccy=p.base_ccy,
        positions=[PositionIn(ticker=x.ticker, weight=x.weight, kind=x.kind) for x in p.positions],
    )
