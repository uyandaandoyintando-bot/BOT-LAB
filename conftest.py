import os
os.environ["DATABASE_URL"] = "sqlite:///botlab_test.db"
os.environ["BOT_API_KEY"] = "test-key"
from database.database import Base, engine, SessionLocal
import pytest
from backend.app import create_app
@pytest.fixture()
def client():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    app = create_app({"TESTING": True, "BOT_API_KEY": "test-key", "ADMIN_ROLE_ID": "admin"})
    with app.test_client() as c: yield c
def auth(): return {"X-Bot-Api-Key": "test-key"}