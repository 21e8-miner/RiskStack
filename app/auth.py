from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from .settings import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALG = "HS256"

def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)

def create_token(user_id: int, hours: int = 24) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": int(now.timestamp()), "exp": int((now + timedelta(hours=hours)).timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALG)

def decode_token(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALG])
    return int(payload["sub"])
