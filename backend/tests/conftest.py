import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import SessionLocal, Base, engine

@pytest.fixture(scope="session", autouse=True)
def _db_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

@pytest.fixture()
def client():
    return TestClient(app)
