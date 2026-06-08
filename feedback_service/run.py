from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    host = os.getenv("FEEDBACK_PORTAL_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8890"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
