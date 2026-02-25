from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from ..deps import get_db
from ..auth import decode_token
from ..models import User

bearer = HTTPBearer()

def current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = decode_token(cred.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=401, detail="invalid_user")
    return u
