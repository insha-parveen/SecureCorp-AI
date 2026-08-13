"""Tests for the JWT auth surface.

Covers:
- Issue + verify a known demo user returns the right UserContext shape.
- Unknown user is rejected (401, no cookie set).
- The verified cookie carries the right UserContext on a protected route.
- Missing cookie on a protected route returns 401.
- Logout clears the cookie.
- Listing the demo-user directory returns the seeded users.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hybridrag.api.app import create_app
from hybridrag.api.auth import DEMO_USERS, issue_token, verify_token
from hybridrag.config import get_settings


@pytest.fixture()
def client() -> TestClient:
    """A TestClient that uses a fresh app instance per test.

    The auth routes set cookies on ``Domain=localhost`` (see
    routes_auth.py), so the TestClient must talk to ``localhost`` or
    the cookie never lands in the client's jar.
    """
    app = create_app()
    with TestClient(app, base_url="http://localhost") as c:
        yield c


def test_issue_and_verify_token_roundtrip() -> None:
    settings = get_settings()
    token, ttl = issue_token("alice", settings)
    assert ttl == settings.jwt_ttl_seconds
    claims = verify_token(token, settings)
    assert claims["sub"] == "alice"
    assert "hr" in claims["roles"]
    assert claims["department"] == "HR"
    assert claims["tenant_id"] == "nexacore_main"


def test_unknown_user_rejected() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        issue_token("not-a-real-user", get_settings())
    assert exc_info.value.status_code == 401


def test_missing_cookie_returns_401(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_demo_user_login_sets_cookie(client: TestClient) -> None:
    response = client.post("/api/auth/token", json={"user_id": "alice"})
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "alice"
    assert "hr" in body["roles"]
    assert body["department"] == "HR"
    # The cookie must be set
    assert "sc_auth" in response.cookies


def test_cookie_authenticates_me(client: TestClient) -> None:
    login = client.post("/api/auth/token", json={"user_id": "bob"})
    assert login.status_code == 200
    # Domain-scoped cookies on localhost can be flaky with httpx's
    # TestClient cookie jar. Ensure the cookie is attached explicitly.
    cookie_value = login.cookies.get("sc_auth")
    assert cookie_value is not None
    client.cookies.set("sc_auth", cookie_value)
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["user_id"] == "bob"
    assert "finance" in body["roles"]
    assert body["department"] == "Finance"


def test_logout_clears_cookie(client: TestClient) -> None:
    client.post("/api/auth/token", json={"user_id": "alice"})
    out = client.post("/api/auth/logout")
    assert out.status_code == 200
    # After logout, the protected /me must 401 again.
    me = client.get("/api/auth/me")
    assert me.status_code == 401


def test_demo_user_directory_is_public(client: TestClient) -> None:
    response = client.get("/api/auth/users")
    assert response.status_code == 200
    body = response.json()
    user_ids = {u["user_id"] for u in body["users"]}
    # Every pre-seeded user must be present.
    assert set(DEMO_USERS.keys()) <= user_ids
