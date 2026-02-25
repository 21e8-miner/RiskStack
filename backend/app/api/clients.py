from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..deps import get_db
from ..models import Client, AuditEvent
from ..schemas import ClientCreate, ClientOut
from ._security import current_user

router = APIRouter()

@router.post("/clients", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), u=Depends(current_user)):
    c = Client(owner_user_id=u.id, name=payload.name, email=payload.email)
    db.add(c)
    db.flush()
    db.add(AuditEvent(user_id=u.id, action="create", entity_type="client", entity_id=str(c.id), payload={"name": c.name}))
    db.commit()
    db.refresh(c)
    return c

@router.get("/clients", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), u=Depends(current_user)):
    return db.query(Client).filter(Client.owner_user_id == u.id).order_by(Client.id.desc()).all()
