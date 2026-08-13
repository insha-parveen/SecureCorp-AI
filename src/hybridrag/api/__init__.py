"""Public API surface for SecureCorp AI (Phase 9 MVP).

The MVP slice exposes:

- ``app`` — the FastAPI application instance.
- ``create_app`` — the app factory (for tests that need a fresh app).
"""

from hybridrag.api.app import app, create_app

__all__ = ["app", "create_app"]
