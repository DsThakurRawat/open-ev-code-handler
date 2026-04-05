import pytest
import os
os.environ["TESTING"] = "true"
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app import app
from codelens_env.database import get_session
from codelens_env.env import CodeLensEnv
from codelens_env.models import TaskId, Action, ActionType, Severity, Category, Verdict

@pytest.fixture(name="session")
def session_fixture():
    """In-memory SQLite session for tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    """TestClient with DB dependency override."""
    def get_session_override():
        yield session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def env():
    return CodeLensEnv()

@pytest.fixture
def approve_action():
    return Action(action_type=ActionType.APPROVE, body="LGTM", verdict=Verdict.LGTM)

@pytest.fixture
def request_changes_action():
    return Action(action_type=ActionType.REQUEST_CHANGES, body="Issues found",
                  verdict=Verdict.REQUEST_CHANGES)
