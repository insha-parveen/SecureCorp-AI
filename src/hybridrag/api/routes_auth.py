"""Auth routes: ``POST /api/auth/token`` and ``GET /api/auth/me``."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from hybridrag.api.auth import (
    current_user_from_cookie,
    issue_token,
    list_demo_users,
    verify_token,
)
from hybridrag.api.rate_limit import rate_limit
from hybridrag.api.schemas import TokenRequest, TokenResponse
from hybridrag.authorization.models import UserContext
from hybridrag.config import Settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/users")
def get_demo_users() -> dict[str, object]:
    """Public directory of demo users. Used by the login picker.

    No sensitive info: only ``user_id``, ``roles``, ``department``.
    """
    return {"users": list_demo_users()}


@router.post("/token")
def post_token(
    body: TokenRequest,
    request: Request,
    _: None = Depends(rate_limit()),
) -> Response:
    """Issue a JWT for a demo user and set the ``sc_auth`` httpOnly cookie.

    The token body is rejected as 401 if ``user_id`` is unknown — the
    frontend cannot escalate by guessing.
    """
    settings: Settings = request.app.state.settings
    token, ttl = issue_token(body.user_id, settings)
    # The demo entry we issued for.
    from hybridrag.api.auth import DEMO_USERS  # local import to avoid a top cycle

    entry = DEMO_USERS[body.user_id]

    response = JSONResponse(
        content=TokenResponse(
            user_id=entry["user_id"],
            roles=list(entry["roles"]),
            department=entry["department"],
            tenant_id=entry["tenant_id"],
            expires_in=ttl,
        ).model_dump()
    )
    # httpOnly: frontend JS cannot read it; SameSite=Lax: survives top-level nav.
    # Secure is off in dev (HTTP); in production it must be set via the proxy.
    # ``domain=None`` in Starlette means the *exact* host the cookie was set
    # from — which (for the dev FastAPI on :8000 talking to the dev Next.js
    # on :3000) would scope the cookie to port 8000 and block the
    # cross-origin POST to /api/chat. ``localhost`` here lets the browser
    # attach the cookie to any localhost port, which is exactly what we want
    # for the local MVP. In production behind a single proxy origin, this is
    # a no-op.
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=ttl,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        domain=settings.auth_cookie_domain or None,
    )
    return response


@router.post("/logout")
def post_logout(request: Request) -> Response:
    """Clear the auth cookie. Idempotent."""
    settings: Settings = request.app.state.settings
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
    return response


@router.get("/me", response_model=TokenResponse)
def get_me(
    request: Request,
    user: UserContext = Depends(current_user_from_cookie()),
) -> TokenResponse:
    """Return the current ``UserContext`` (from the verified JWT)."""
    settings: Settings = request.app.state.settings
    # We don't return the raw expiry, but the configured TTL is a fair proxy.
    return TokenResponse(
        user_id=user.user_id,
        roles=list(user.roles),
        department=user.department,
        tenant_id=user.tenant_id,
        expires_in=settings.jwt_ttl_seconds,
    )


# Re-export for routers that want to verify a raw token (e.g., tests).
__all__ = ["router", "verify_token"]
