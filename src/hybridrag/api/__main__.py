"""Module entrypoint: ``uvicorn hybridrag.api.app:app`` is the canonical way.

This ``__main__`` is for convenience (``python -m hybridrag.api``).
"""

from __future__ import annotations

import uvicorn

from hybridrag.api.app import app  # noqa: F401  (re-exported)

if __name__ == "__main__":
    uvicorn.run("hybridrag.api.app:app", host="0.0.0.0", port=8000, reload=True)
