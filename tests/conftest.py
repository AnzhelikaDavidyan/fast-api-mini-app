import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app.database import init_db, make_engine
from app.main import app
from app.store import BonusStore, get_store


@pytest.fixture
def client():
    # Fresh in-memory database for every test; StaticPool shares one connection across threads.
    engine = make_engine("sqlite://", poolclass=StaticPool)
    store = BonusStore(init_db(engine))
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()
