import pytest
from backend.app.database import Base, sync_engine
import backend.app.models

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=sync_engine)
    yield
