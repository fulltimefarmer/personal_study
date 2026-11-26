"""Integration tests for FastAPI endpoints — 需要启动服务器"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"), override=True)

from fastapi.testclient import TestClient

from app.api.server import create_app


pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestAPIEndpoints:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_list_sessions(self, client):
        response = client.get("/sessions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_sessions_empty_returns_list(self, client):
        response = client.get("/sessions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAPISchemas:
    def test_session_info_model(self):
        from app.api.schemas import SessionInfo
        s = SessionInfo(session_id="test123", created_at="2026-01-01T00:00:00", message_count=5)
        assert s.session_id == "test123"
        assert s.message_count == 5

    def test_session_info_defaults(self):
        from app.api.schemas import SessionInfo
        s = SessionInfo(session_id="test", created_at="2026-01-01T00:00:00", message_count=0)
        assert s.session_id == "test"
        assert s.message_count == 0
