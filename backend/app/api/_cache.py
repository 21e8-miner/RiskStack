import json
import hashlib
from redis import Redis
from ..settings import settings

r = Redis.from_url(settings.redis_url, decode_responses=True)

def cache_key(prefix: str, payload: dict) -> str:
    b = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    h = hashlib.sha256(b).hexdigest()
    return f"{prefix}:{h}"

def cache_get(key: str):
    v = r.get(key)
    return json.loads(v) if v else None

def cache_set(key: str, obj: dict, ttl_s: int):
    r.setex(key, ttl_s, json.dumps(obj, separators=(",", ":")))
