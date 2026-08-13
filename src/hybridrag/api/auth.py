"""JWT auth + demo-user table for the Phase 9 MVP.

The frontend never sends ``user_id``/``roles`` in request bodies — those
arrive in the verified JWT (CLAUDE.md §5, hard invariant).

The demo-user table is hard-coded: one entry per canonical role from
CLAUDE.md §11. No signup, no password flow, no real provisioning.
"""

from __future__ import annotations

import time
from typing import Any

import jwt
from fastapi import Cookie, HTTPException, status

from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings, get_settings

# Pre-seeded demo users. The ``user_id`` is the login identifier; the
# rest of the UserContext is what the assistant sees server-side.
DEMO_USERS: dict[str, dict[str, Any]] = {
    "alice": {
        "user_id": "alice",
        "roles": ("hr", "employee"),
        "department": "HR",
        "tenant_id": "nexacore_main",
    },
    "bob": {
        "user_id": "bob",
        "roles": ("finance", "employee"),
        "department": "Finance",
        "tenant_id": "nexacore_main",
    },
    "carol": {
        "user_id": "carol",
        "roles": ("it", "employee"),
        "department": "IT and Security",
        "tenant_id": "nexacore_main",
    },
    "dave": {
        "user_id": "dave",
        "roles": ("manager", "employee"),
        "department": "Engineering",
        "tenant_id": "nexacore_main",
    },
    "eve": {
        "user_id": "eve",
        "roles": ("employee",),
        "department": "Operations",
        "tenant_id": "nexacore_main",
    },
    "admin": {
        "user_id": "admin",
        "roles": ("admin",),
        "department": "IT and Security",
        "tenant_id": "nexacore_main",
    },
}

DEFAULT_DEV_SECRET = "dev-only-insecure-jwt-secret-change-me"


def list_demo_users() -> list[dict[str, object]]:
    """Return the public demo-user directory (login picker payload).

    Roles are surfaced so the picker can render role badges; no sensitive
    information is exposed.
    """
    return [
        {
            "user_id": entry["user_id"],
            "roles": [str(r) for r in entry["roles"]],
            "department": entry["department"] or "",
        }
        for entry in DEMO_USERS.values()
    ]


def issue_token(user_id: str, settings: Settings | None = None) -> tuple[str, int]:
    """Sign a JWT for ``user_id`` and return ``(token, expires_in_seconds)``.

    Raises :class:`HTTPException` 401 if ``user_id`` is not in the demo table.
    """
    cfg = settings or get_settings()
    entry = DEMO_USERS.get(user_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown demo user",
        )

    now = int(time.time())
    exp = now + cfg.jwt_ttl_seconds
    roles: list[str] = [str(r) for r in entry["roles"]]
    payload: dict[str, object] = {
        "sub": entry["user_id"],
        "roles": roles,
        "department": entry["department"],
        "tenant_id": entry["tenant_id"],
        "iat": now,
        "exp": exp,
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm="HS256")
    return token, cfg.jwt_ttl_seconds


def verify_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Verify a JWT and return its claims. Raises 401 on any failure.

    The token is the only source of identity the application trusts.
    """
    cfg = settings or get_settings()
    try:
        return dict(jwt.decode(token, cfg.jwt_secret, algorithms=["HS256"]))
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


def current_user_from_cookie(
    settings: Settings | None = None,
) -> Any:  # FastAPI dependency factory return type
    """FastAPI dependency that returns the verified ``UserContext``.

    The cookie name is configurable via ``Settings.auth_cookie_name``.
    Use as: ``user: UserContext = Depends(current_user_from_cookie())``.
    """
    cfg = settings or get_settings()

    def _dependency(sc_auth: str | None = Cookie(default=None)) -> UserContext:
        if not sc_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        claims = verify_token(sc_auth, cfg)
        return UserContext(
            user_id=claims["sub"],
            roles=tuple(claims.get("roles") or ()),
            department=claims.get("department"),
            tenant_id=claims.get("tenant_id", "nexacore"),
        )

    return _dependency
