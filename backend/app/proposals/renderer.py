from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

@dataclass(frozen=True)
class ProposalInputs:
    portfolio_name: str
    client_name: str
    as_of: str
    positions: list[dict]
    risk: dict
    mc: dict
    assumptions: dict

def inputs_hash(obj: dict) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def render_pdf(template_dir: str, inputs: ProposalInputs) -> bytes:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
    )
    tpl = env.get_template("proposal.html")
    html = tpl.render(**inputs.__dict__)
    return HTML(string=html).write_pdf()
