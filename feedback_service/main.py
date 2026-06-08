from __future__ import annotations

import hmac
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _db_path() -> Path:
    raw = os.getenv("FEEDBACK_PORTAL_DB_PATH", "feedback_portal.sqlite").strip()
    return Path(raw).resolve()


def _connection() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables() -> None:
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL DEFAULT 'portal',
                phone_number TEXT,
                feedback_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _now_iso() -> str:
    return datetime.now().isoformat()


def _is_authenticated(request: Request) -> bool:
    return bool(request.session.get("feedback_auth"))


def _render_login(error: str | None = None) -> str:
    message = f"<p style='color:#b00020'>{error}</p>" if error else ""
    return f"""
<!doctype html>
<html>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Tech Restore Feedback Login</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(120deg,#f7f8ff,#eefaf7); min-height: 100vh; margin: 0; display:flex; align-items:center; justify-content:center; }}
    .card {{ width:min(440px,92vw); background:#fff; border-radius:16px; padding:24px; box-shadow:0 8px 32px rgba(0,0,0,.08); }}
    h1 {{ margin:0 0 8px; font-size:1.4rem; }}
    p {{ margin:0 0 16px; color:#475569; }}
    input {{ width:100%; padding:12px; border:1px solid #cbd5e1; border-radius:10px; margin-bottom:12px; font-size:1rem; }}
    button {{ width:100%; border:none; background:#0f766e; color:white; padding:12px; border-radius:10px; font-size:1rem; cursor:pointer; }}
  </style>
</head>
<body>
  <form class='card' method='post' action='/login'>
    <h1>Feedback Portal</h1>
    <p>Enter the shared access password.</p>
    {message}
    <input type='password' name='password' placeholder='Portal password' required />
    <button type='submit'>Sign In</button>
  </form>
</body>
</html>
"""


def _render_dashboard(rows: list[dict]) -> str:
    row_html = "".join(
        f"<tr><td>{row['id']}</td><td>{row['source']}</td><td>{row.get('phone_number') or '-'}</td><td>{row['feedback_text']}</td><td>{row['created_at']}</td></tr>"
        for row in rows
    )
    return f"""
<!doctype html>
<html>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Tech Restore Feedback</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; margin:0; background:#f8fafc; }}
    header {{ padding:16px 20px; background:#111827; color:#fff; display:flex; justify-content:space-between; align-items:center; }}
    main {{ padding:20px; }}
    table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:12px; overflow:hidden; }}
    th, td {{ padding:10px; border-bottom:1px solid #e5e7eb; text-align:left; vertical-align:top; }}
    th {{ background:#f3f4f6; font-weight:600; }}
    .actions {{ display:flex; gap:8px; align-items:center; }}
    .logout {{ color:#111827; background:#fff; padding:8px 10px; border-radius:8px; text-decoration:none; }}
    form.add {{ margin:0 0 16px; background:#fff; padding:12px; border-radius:12px; display:grid; gap:8px; }}
    textarea, input {{ border:1px solid #cbd5e1; border-radius:8px; padding:8px; font:inherit; }}
    button {{ width:fit-content; border:none; background:#0f766e; color:#fff; padding:8px 12px; border-radius:8px; cursor:pointer; }}
  </style>
</head>
<body>
  <header>
    <strong>Tech Restore Feedback</strong>
    <div class='actions'>
      <a class='logout' href='/logout'>Log out</a>
    </div>
  </header>
  <main>
    <form class='add' method='post' action='/add'>
      <input name='phone_number' placeholder='Optional phone number' />
      <textarea name='feedback_text' rows='3' placeholder='Feedback text' required></textarea>
      <button type='submit'>Add Feedback</button>
    </form>
    <table>
      <thead>
        <tr><th>ID</th><th>Source</th><th>Phone</th><th>Feedback</th><th>Created</th></tr>
      </thead>
      <tbody>{row_html}</tbody>
    </table>
  </main>
</body>
</html>
"""


app = FastAPI(title="Tech Restore Feedback Portal")
app.add_middleware(SessionMiddleware, secret_key=_required_env("FEEDBACK_PORTAL_SESSION_SECRET"), same_site="lax")


@app.on_event("startup")
def startup() -> None:
    _ensure_tables()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    if not _is_authenticated(request):
        return HTMLResponse(_render_login())

    with _connection() as connection:
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT id, source, phone_number, feedback_text, created_at FROM feedback_entries ORDER BY id DESC LIMIT 500"
            ).fetchall()
        ]
    return HTMLResponse(_render_dashboard(rows))


@app.post("/login")
def login(request: Request, password: str = Form(...)) -> RedirectResponse:
    expected = _required_env("FEEDBACK_PORTAL_PASSWORD")
    if not hmac.compare_digest(password, expected):
        return HTMLResponse(_render_login(error="Invalid password."), status_code=401)

    request.session["feedback_auth"] = True
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.post("/add")
def add_feedback(
    request: Request,
    feedback_text: str = Form(...),
    phone_number: str = Form(default=""),
) -> RedirectResponse:
    if not _is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    text = feedback_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Feedback text is required")

    with _connection() as connection:
        connection.execute(
            "INSERT INTO feedback_entries(source, phone_number, feedback_text, created_at) VALUES (?, ?, ?, ?)",
            ("portal", phone_number.strip() or None, text, _now_iso()),
        )
        connection.commit()

    return RedirectResponse(url="/", status_code=303)


@app.post("/ingest")
def ingest_feedback(
    feedback_text: str = Form(...),
    phone_number: str | None = Form(default=None),
    source: str = Form(default="sms"),
    x_feedback_token: str | None = Header(default=None, alias="X-Feedback-Token"),
) -> dict:
    expected_token = os.getenv("FEEDBACK_PORTAL_INGEST_TOKEN", "").strip()
    if expected_token and not hmac.compare_digest(x_feedback_token or "", expected_token):
        raise HTTPException(status_code=403, detail="Forbidden")

    text = feedback_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Feedback text is required")

    with _connection() as connection:
        cursor = connection.execute(
            "INSERT INTO feedback_entries(source, phone_number, feedback_text, created_at) VALUES (?, ?, ?, ?)",
            ((source or "sms").strip() or "sms", (phone_number or "").strip() or None, text, _now_iso()),
        )
        connection.commit()

    return {"id": int(cursor.lastrowid), "status": "ok"}
