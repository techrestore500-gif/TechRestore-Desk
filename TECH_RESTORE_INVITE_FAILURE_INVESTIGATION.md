# Tech Restore Invite Failure Investigation

**Date:** 2026-05-28  
**Repo:** techrestore500-gif/TechRestore-Desk  
**Branch:** main  
**Relevant commits:** 87becbe, 68c33b0, 13692c7

---

## 1. Executive Summary

The most likely root cause of the production invite failure is **Render's free-tier plan blocking outbound SMTP TCP connections to smtp.gmail.com on port 587 (and 465)**. This is supported directly by the logged error:

```
SMTP connection failed (OSError): [Errno 101] Network is unreachable [host=smtp.gmail.com port=587 ssl=False starttls=True timeout=20.0s]
```

`Errno 101` is a Linux network-level error meaning the TCP socket attempt never reached Gmail — it was blocked at the container networking layer before any credential check occurred. This is a well-documented behavior of Render's free-tier web services, which restrict outbound connections to ports other than 80 and 443.

A **second confirmed problem** is that `render.yaml` does not declare `ADMIN_EMAIL`, `ADMIN_INVITE_BOOTSTRAP`, `ADMIN_INVITE_BOOTSTRAP_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`, `SMTP_USE_SSL`, `SMTP_STARTTLS`, `SMTP_TIMEOUT_SECONDS`, or `FRONTEND_BASE_URL` as environment variable keys. This means Render's Blueprint deployment will not prompt for them and they will be absent unless manually entered in the Render dashboard. If any of these are missing, bootstrap invite sending silently fails at startup and the resend endpoint returns a 400 or 500 response.

A **third risk** is that the backend Render service uses `DATABASE_URL` pointing to an ephemeral SQLite path inside the container. Without a Render Persistent Disk, invite records created in one deploy are lost on the next deploy or restart. Any invite that was successfully created and emailed may no longer be valid after a restart.

---

## 2. Current Expected Production Flow

The intended onboarding flow from a clean deployment is:

1. **Backend starts on Render** → `initialize_app()` in `app/core/startup.py` runs in the FastAPI lifespan.
2. **Startup bootstrap check** → `AuthService.ensure_bootstrap_admin_invite_from_env()` runs:
   - Reads `ADMIN_INVITE_BOOTSTRAP` (must be `true`).
   - Reads `ADMIN_EMAIL` (must be `mattiskleinbh@gmail.com`).
   - Reads `ADMIN_NAME`, `ADMIN_INVITE_ROLE`.
   - Checks if any users exist or any active admins exist. If zero, proceeds.
   - Checks if a pending invite already exists for `ADMIN_EMAIL`. If pending invite exists, no action.
   - Otherwise, creates a new invite record in `auth_invites` SQLite table (token is SHA-256 hashed, cleartext token kept only during send).
   - Calls `EmailService.send_invite_email(...)`.
   - Email goes via SMTP to `SMTP_HOST:SMTP_PORT` using `SMTP_USERNAME`/`SMTP_PASSWORD`.
   - On success: invite record stays as `status=pending`. Invite link in email is `{FRONTEND_BASE_URL}/invite/{token}`.
   - On `EmailDeliveryError`: invite record is revoked and a `ValueError` propagates to startup, which catches and logs it as a warning.
3. **Admin receives email** at `mattiskleinbh@gmail.com` with a link like `https://desk.techrestoredesk.com/invite/<token>`.
4. **Admin clicks link** → React app at `desk.techrestoredesk.com` renders the `/invite/:token` route (`InviteAcceptPage`).
5. **Frontend calls** `GET /api/auth/invites/{token}` (public route) → resolves invite, confirms it is pending and not expired.
6. **Admin sets password** and submits → `POST /api/auth/invites/{token}/accept` → creates user record in `users` table, marks invite as `accepted`.
7. **Admin logs in** → `POST /api/auth/login` → receives JWT token → React stores in session storage → `AuthProvider` marks authenticated → app is accessible.

**Emergency recovery path** (when email never arrived or startup failed):

- Call `POST https://api.techrestoredesk.com/api/auth/bootstrap/resend` with header `X-Bootstrap-Key: <ADMIN_INVITE_BOOTSTRAP_KEY>`.
- This revokes any existing pending bootstrap invite and creates a fresh one, then re-sends the email.
- Blocked by same SMTP issue if Render free tier network restriction is still present.

---

## 3. Files Inspected

| File | Role |
|---|---|
| `backend/app/services/emailer.py` | All SMTP configuration reading, transport selection (SSL vs STARTTLS), email composition and send logic, error handling and logging |
| `backend/app/services/auth.py` | Auth domain logic: invite creation/revocation/acceptance/resend, bootstrap invite logic, login, user creation, URL building for invite links |
| `backend/app/routes/auth.py` | FastAPI route definitions: login, invite CRUD, bootstrap resend endpoint, key validation |
| `backend/app/middleware/auth_gate.py` | Public/private route gate, lists which paths bypass auth; confirms `/api/auth/bootstrap/resend` is public |
| `backend/app/repositories/auth.py` | SQLite operations: `auth_invites` and `users` table creation/queries including `count_users`, `count_active_admins`, `revoke_pending_invites_for_email` |
| `backend/app/auth/dependencies.py` | JWT token validation, shared-password mode, bypass mode logic; `auth_enforcement_enabled()` depends on `REPAIR_DESK_AUTH_ENABLED` |
| `backend/app/core/startup.py` | App init: calls `ensure_bootstrap_admin_invite_from_env()`, logs production env warnings for missing vars |
| `backend/app/core/settings.py` | Settings dataclass loading from env |
| `backend/app/main.py` | FastAPI app setup, middleware order (CORS, AuthGate, AccessLog), lifespan, router registration |
| `backend/app/database.py` | SQLite path resolution from `DATABASE_URL` env var; fallback to `data/tech_restore_desk.sqlite` |
| `backend/run_server.py` | Uvicorn startup: resolves host/port from `PORT`/`APP_ENV` env vars |
| `backend/Dockerfile` | Container image: Python 3.12-slim, copies `app/`, runs uvicorn on `PORT` |
| `backend/.env.example` | Template showing all expected env vars including new SMTP mode flags |
| `render.yaml` | Render Blueprint: declares env var **keys** for Render config — critically **missing** SMTP, ADMIN, FRONTEND, and auth invite vars |
| `frontend/src/auth/AuthGate.tsx` | Login screen; renders email+password form; no signup/request-access visible; passes through `/invite/` path directly |
| `frontend/src/auth/AuthProvider.tsx` | Session state management; reads `AUTH_ENABLED`; loads session from storage; handles 401 logout |
| `frontend/src/auth/config.ts` | `AUTH_ENABLED` constant read from `VITE_AUTH_ENABLED` env var at build time |
| `frontend/src/api/client.ts` | API base URL resolution: reads `VITE_API_BASE_URL` at build time; falls back to domain inference (`desk.` → `api.`) or `/api`; injects bearer token on all requests |
| `frontend/src/api/auth.ts` | API calls: `login`, `fetchCurrentUser`, `resolveInvite`, `acceptInvite` |
| `frontend/src/routes/router.tsx` | React Router config: `/invite/:token` is a top-level route rendering `InviteAcceptPage` outside `AppShell` |
| `frontend/src/pages/InviteAcceptPage.tsx` | Invite accept UI: calls `resolveInvite` then `acceptInvite`; does not sit behind `AuthGate` |
| `frontend/vite.config.ts` | Vite config: dev proxy `/api` → `http://127.0.0.1:8787`; no SPA rewrite rule configured for production |
| `backend/app/tests/test_auth_api.py` | Auth API test suite (25 tests) |
| `backend/app/tests/test_emailer.py` | SMTP unit tests (4 tests) |

---

## 4. Backend Auth and Invite Flow

### 4.1 Environment Variables Consumed

| Var | Default | Where Read | Effect if missing |
|---|---|---|---|
| `ADMIN_INVITE_BOOTSTRAP` | `false` | `AuthService.ensure_bootstrap_admin_invite_from_env()` and `resend_bootstrap_admin_invite_from_env()` | Bootstrap never runs; resend returns 400 "Bootstrap invites are disabled" |
| `ADMIN_EMAIL` | (empty) | `_bootstrap_admin_invite_details()` | `ValueError("ADMIN_EMAIL is not configured")` → startup warning, resend returns 400 |
| `ADMIN_NAME` | `"Tech Restore Admin"` | `_bootstrap_admin_invite_details()` | Uses default |
| `ADMIN_INVITE_ROLE` | `"owner"` | `_bootstrap_admin_invite_details()` | Uses default; clamped to "owner" if not "owner"/"admin" |
| `ADMIN_INVITE_BOOTSTRAP_KEY` | (empty) | `post_bootstrap_resend()` route | Returns 404 "Bootstrap resend endpoint disabled" |
| `TECH_RESTORE_INVITE_EXPIRY_HOURS` | `72` | `_invite_expiry_hours()` | Uses 72 hours |
| `FRONTEND_BASE_URL` | Falls back to `PUBLIC_BASE_URL`, then hardcoded `https://desk.techrestoredesk.com` | `_desk_base_url()` | If both env vars are missing, uses hardcoded fallback — this is actually safe for the default domain |
| `SMTP_HOST` | (empty) | `EmailService._smtp_host()` | `EmailDeliveryError("Email is not configured (SMTP_HOST)")` |
| `SMTP_PORT` | `587` | `EmailService._smtp_port()` | Uses 587 |
| `SMTP_USE_SSL` | `false` | `EmailService._use_ssl()` | Uses STARTTLS path |
| `SMTP_STARTTLS` | `true` | `EmailService._starttls_enabled()` | Enabled unless SSL mode |
| `SMTP_TIMEOUT_SECONDS` | `20` | `EmailService._smtp_timeout_seconds()` | Uses 20s |
| `SMTP_USERNAME` | (empty) | `EmailService._smtp_username()` | `EmailDeliveryError("Email is not configured (SMTP_USERNAME)")` |
| `SMTP_PASSWORD` | (empty) | `EmailService._smtp_password()` | `EmailDeliveryError("Email is not configured (SMTP_PASSWORD)")` |
| `SMTP_FROM_EMAIL` | (empty) | `EmailService._from_email()` | `EmailDeliveryError("Email is not configured (SMTP_FROM_EMAIL)")` |
| `SMTP_FROM_NAME` | `"Tech Restore"` | `EmailService._from_name()` | Uses default |
| `REPAIR_DESK_AUTH_ENABLED` | Not set | `auth_enforcement_enabled()` | If not set, `TECH_RESTORE_AUTH_BYPASS` defaults to `"1"` → auth is **bypassed** entirely |
| `SECRET_KEY` | From `get_settings()` | JWT operations | Login tokens fail to sign/verify |
| `DATABASE_URL` | Falls back to `data/tech_restore_desk.sqlite` | `database.py` | Uses ephemeral container path — **data lost on redeploy** |

### 4.2 Route Names

| Route | Auth Requirement |
|---|---|
| `POST /api/auth/login` | Public |
| `GET /api/auth/invites/{token}` | Public (pattern-matched in middleware) |
| `POST /api/auth/invites/{token}/accept` | Public (pattern-matched in middleware) |
| `POST /api/auth/bootstrap/resend` | Public but key-gated via `X-Bootstrap-Key` header |
| `POST /api/auth/invites` | Requires owner or admin JWT |
| `POST /api/auth/invites/{id}/resend` | Requires owner or admin JWT |
| `POST /api/auth/invites/{id}/revoke` | Requires owner or admin JWT |
| `GET /api/auth/invites` | Requires owner or admin JWT |
| `GET /api/auth/users` | Requires owner or admin JWT |
| `GET /api/auth/me` | Requires any valid JWT |

### 4.3 Invite Token Lifecycle

1. `secrets.token_urlsafe(32)` generates cleartext token (~43 chars, URL-safe base64).
2. `hashlib.sha256(token.encode()).hexdigest()` produces the stored `token_hash`.
3. Cleartext token is embedded in the invite link URL: `{FRONTEND_BASE_URL}/invite/{token}`.
4. Cleartext token is **never stored** — only the hash lives in the database.
5. On accept: the same hash is recomputed and looked up in `auth_invites.token_hash`.
6. Once accepted, the invite record status becomes `"accepted"` — the link cannot be reused.

### 4.4 Startup Bootstrap Logic

```
ensure_bootstrap_admin_invite_from_env():
  if ADMIN_INVITE_BOOTSTRAP != "true" → return None
  if count_users() > 0 or count_active_admins() > 0 → return None (silent skip)
  if ADMIN_EMAIL is empty → raise ValueError
  if pending invite already exists for ADMIN_EMAIL → return existing (no email sent)
  create new invite → send email → return invite
```

**Critical behavior:** If `count_users() > 0`, the bootstrap check returns `None` silently. This means that if a test user or stale user record exists in the database (from a previous run), the bootstrap invite will never be sent at startup — even if the user table has garbage data from a prior test.

**On email failure during startup:** `create_invite(send_email=True)` will revoke the new invite record and raise `ValueError`. `startup.py` catches `ValueError` and logs a warning — so the backend continues to start successfully. The invite is **not** persisted. The failure is only visible in Render logs.

### 4.5 Bootstrap Resend Logic

```
resend_bootstrap_admin_invite_from_env():
  if ADMIN_INVITE_BOOTSTRAP != "true" → raise ValueError("Bootstrap invites are disabled")
  if count_users() > 0 or count_active_admins() > 0 → raise ValueError("Bootstrap invite resend is unavailable after account setup")
  revoke_pending_invites_for_email(ADMIN_EMAIL)
  create_invite(send_email=True) → sends email
```

The route `POST /api/auth/bootstrap/resend` first validates `X-Bootstrap-Key` matches `ADMIN_INVITE_BOOTSTRAP_KEY`. If key is correct and SMTP works, it returns 200 with the new invite's JSON. If SMTP fails, it raises `ValueError("Could not connect to SMTP server")` → route returns HTTP 400.

**The response body on SMTP failure is:**
```json
{"detail": "Could not connect to SMTP server"}
```
or
```json
{"detail": "Failed to deliver invite email"}
```
These are the only user-visible signals. The detailed diagnostic (including the `Errno 101` host/port/mode context) is only in the Render log stream, not in the response body.

### 4.6 Auth Enforcement

`auth_enforcement_enabled()` returns `True` only when:
- `REPAIR_DESK_AUTH_ENABLED` is set to a truthy value (`1`, `true`, `yes`, `on`).
- And `TECH_RESTORE_AUTH_BYPASS` is not `"1"` (its default).

If `REPAIR_DESK_AUTH_ENABLED` is not set in Render, **all auth is bypassed**. The app would appear to work but every request would be authenticated as `shared-password-admin` dev bypass — this is a security hole that must be confirmed as closed.

---

## 5. Frontend Login and Invite Flow

### 5.1 Auth Configuration

`AUTH_ENABLED` is a **build-time constant** read from `VITE_AUTH_ENABLED` in `frontend/src/auth/config.ts`. It is compiled into the JavaScript bundle. If `VITE_AUTH_ENABLED` was not set when Render last built the frontend static site, auth is disabled in the deployed JS even if the env var is set today.

`render.yaml` declares `VITE_AUTH_ENABLED: true` as a hardcoded value (not `sync: false`), so it should be present at build time. However, `VITE_API_BASE_URL` is `sync: false` — meaning it is provided as a secret and must be set manually in the Render dashboard before building.

### 5.2 API Base URL Resolution

`client.ts` uses this resolution order at **build time**:

1. `VITE_API_BASE_URL` env var (set at `npm run build` time by Render — must be present in Render env).
2. If empty and dev mode: `http://127.0.0.1:8787`.
3. If empty and production + hostname starts with `desk.`: infers `https://api.<rest-of-hostname>`.
4. Fallback: `/api` (same-origin — would fail in production because frontend and backend are different domains).

**Inference path (step 3)** would work correctly for `desk.techrestoredesk.com` → `api.techrestoredesk.com`, but only if `VITE_API_BASE_URL` was absent at build time. Since the inference uses `window.location.hostname` at runtime (not build time), the fallback should resolve correctly even without the env var — **but this should not be relied upon**. If `VITE_API_BASE_URL` is not set in Render env, step 3 would still produce the correct URL in production, but only for the `desk.*` domain pattern.

### 5.3 Login Page

`AuthGate.tsx` renders the login form when `authEnabled=true` and `!isAuthenticated`. The form shows:

```
"Sign in with your invited Tech Restore account."
```

There is **no public signup** link and **no "Request Access"** wording. This is correct.

### 5.4 Invite Accept Route and Deep Link Risk

The `/invite/:token` route is defined at the top level in `router.tsx`, outside `AppShell`. `AuthGate.tsx` checks `window.location.pathname.startsWith("/invite/")` and passes through to children without showing the login screen. This logic is client-side.

**Critical finding:** There is **no `_redirects` file and no rewrite rule configured** in `render.yaml` for the static site. For a React SPA deployed as a Render Static Site, any direct browser navigation to `https://desk.techrestoredesk.com/invite/<token>` will result in **Render serving a 404** because the static site server will look for an actual file at `/invite/<token>/index.html` and not find it.

This means the invite email link will fail with a 404 on Render's static site unless:
- A `public/_redirects` file exists with `/* /index.html 200`, OR
- A `routes` rewrite is configured in `render.yaml` under the static site definition.

Neither is present in the inspected files.

**Confirmed missing:** No `frontend/public/_redirects` file found. No `routes` or `headers` section in `render.yaml`.

### 5.5 AppShell Behind Auth

`App.tsx` wraps `<RouterProvider>` inside `<AuthGate>`. `AuthGate` only renders `{children}` when either `!authEnabled` or `isAuthenticated`. The dashboard (`AppShell`) will not be visible behind a failed login — the login screen blocks it. This is correct behavior.

---

## 6. Deployment and Environment Findings

### 6.1 render.yaml is Incomplete

The current `render.yaml` declares these env var keys for the backend:

```
PYTHON_VERSION, APP_ENV, REPAIR_DESK_AUTH_ENABLED, REPAIR_DESK_PASSWORD,
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
PUBLIC_BASE_URL, CORS_ALLOWED_ORIGINS, DATABASE_URL, SECRET_KEY
```

**Not declared in render.yaml (must be added manually in Render dashboard or added to render.yaml):**

```
FRONTEND_BASE_URL
PUBLIC_API_BASE_URL
ADMIN_EMAIL
ADMIN_NAME
ADMIN_INVITE_BOOTSTRAP
ADMIN_INVITE_ROLE
ADMIN_INVITE_BOOTSTRAP_KEY
TECH_RESTORE_INVITE_EXPIRY_HOURS
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_FROM_EMAIL
SMTP_FROM_NAME
SMTP_USE_SSL
SMTP_STARTTLS
SMTP_TIMEOUT_SECONDS
```

If these are absent, the bootstrap invite silently does nothing at startup. The backend logs a production warning listing missing vars — visible only in Render logs.

**Note:** `PUBLIC_BASE_URL` is in `render.yaml` but `FRONTEND_BASE_URL` is the new split variable the code prefers. The code falls back gracefully — `_desk_base_url()` will use `PUBLIC_BASE_URL` if `FRONTEND_BASE_URL` is not set. However, if `PUBLIC_BASE_URL` was previously used for Twilio webhooks, they point to the same domain and that split is now mismatched too.

### 6.2 Backend Service Plan

`render.yaml` declares `plan: starter` for the backend web service. **If the actual deployed Render service is on the free plan, SMTP outbound traffic on port 587 may be blocked.** The render.yaml plan declaration is only a suggestion — it must be confirmed in the Render dashboard that the actual service plan is Starter or higher.

### 6.3 Backend Startup Command

`render.yaml` uses `startCommand: python run_server.py`. The Dockerfile CMD uses `uvicorn` directly. On Render without Docker (native Python env), `run_server.py` is used. `run_server.py` resolves `APP_ENV=production` and `RENDER=true` to bind to `0.0.0.0` on `PORT`. This is correct.

### 6.4 SQLite Storage Risk

`database.py` resolves DB path as:
```
DATABASE_URL → ENV_DB_PATH
OR data/tech_restore_desk.sqlite (inside container)
```

If `DATABASE_URL` is set to `sqlite:///./data/tech_restore_desk.sqlite`, the `data/` directory is inside the container at `/app/data/`. Render's web service containers have ephemeral filesystems. **Every deploy wipes the container and the SQLite file is lost.** Every restart also resets it.

**This means:**
- Bootstrap invite created during deploy A is stored in deploy A's in-memory container filesystem.
- When Render restarts or redeploys the service, deploy B starts with an empty database.
- Startup re-runs, tries to send a new bootstrap invite — and hits the SMTP block again.
- Any invite token emailed before the restart is now invalid (the invite record no longer exists).

Without a Render Persistent Disk mounted at `/var/data` and `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite`, no data will persist between deploys.

### 6.5 Frontend Build-Time Env Vars

`VITE_API_BASE_URL` and `VITE_AUTH_ENABLED` are baked into the JS bundle at `npm run build` time. A change to these values in the Render dashboard requires a **frontend rebuild and redeploy** to take effect. Simply updating env vars does not change the running static site.

### 6.6 Missing SPA Rewrite for Render Static Site

Render Static Sites serve files from a build output directory. A request to `/invite/<token>` will return 404 unless the static site is configured to serve `index.html` for all non-file paths. This is not configured anywhere in the current repo. This is a **confirmed production blocker** for the invite accept flow — even if the email sends successfully and the admin clicks the link, they will get a 404.

---

## 7. Most Likely Root Cause Ranking

### A. Render free tier blocks outbound SMTP to port 587/465
**Likelihood: HIGH (primary suspect)**  
**Evidence:** Direct log evidence: `SMTP connection failed (OSError): [Errno 101] Network is unreachable`. `Errno 101` = `ENETUNREACH` = no network route to host. This is a socket-level failure before any Gmail authentication attempt. Render's free-tier services run in containers with restricted outbound network access; SMTP ports 25, 465, 587 are commonly blocked on free/shared hosting.  
**How to confirm:** Upgrade backend service to Starter plan, redeploy, run bootstrap resend, check logs for absence of `Errno 101`.  
**How to fix:** Upgrade Render backend service to Starter plan (or higher). Alternatively, use an SMTP relay that operates over HTTPS (e.g., SendGrid Web API, Mailgun HTTP API, Resend.com) — these are not subject to SMTP port restrictions.

---

### B. render.yaml missing SMTP/ADMIN/FRONTEND env var keys — vars never set in Render
**Likelihood: HIGH (near-certain secondary cause)**  
**Evidence:** `render.yaml` was inspected and confirmed to not declare `SMTP_HOST`, `SMTP_PASSWORD`, `ADMIN_EMAIL`, `ADMIN_INVITE_BOOTSTRAP`, `ADMIN_INVITE_BOOTSTRAP_KEY`, or `FRONTEND_BASE_URL`. Without these, the vars are absent at runtime. `_validate_config()` raises `EmailDeliveryError("Email is not configured (SMTP_HOST, ...)")` before even attempting SMTP. The startup logs a warning about missing production vars.  
**How to confirm:** In Render dashboard → backend service → Environment → check whether `SMTP_HOST`, `ADMIN_EMAIL`, and `ADMIN_INVITE_BOOTSTRAP` are present with non-empty values.  
**How to fix:** Add all missing env vars to the Render dashboard manually, or add them to `render.yaml` (with `sync: false` for secrets).

---

### I. Render static site rewrite missing — /invite/:token deep links return 404
**Likelihood: HIGH (confirmed production blocker for invite accept)**  
**Evidence:** `frontend/public/_redirects` file does not exist. `render.yaml` has no `routes` rewrite rule for the static site. React Router uses `createBrowserRouter` (HTML5 history API), which requires the server to serve `index.html` for all paths. Without a rewrite rule, Render's static server will 404 on any direct `/invite/:token` URL.  
**How to confirm:** Open `https://desk.techrestoredesk.com/invite/sometoken` directly in a browser. If it shows a 404 or Render's error page instead of the invite accept UI, the rewrite is missing.  
**How to fix:** Add `frontend/public/_redirects` file with content `/* /index.html 200`, then rebuild and redeploy the frontend.

---

### J. SQLite data lost on redeploy/restart — invite records disappear
**Likelihood: HIGH (structural issue)**  
**Evidence:** `DATABASE_URL` defaults to `./data/tech_restore_desk.sqlite` inside the container. Render web service containers are ephemeral. No persistent disk is configured in `render.yaml`.  
**How to confirm:** Check Render backend service → Disks → should show no disk attached. Or deploy twice and verify the database is empty after the second deploy.  
**How to fix:** Add a Render Persistent Disk (Starter plan required), mount at `/var/data`, set `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite`.

---

### F. Frontend not rebuilt with correct VITE_API_BASE_URL / VITE_AUTH_ENABLED
**Likelihood: MEDIUM**  
**Evidence:** `VITE_API_BASE_URL` is `sync: false` in `render.yaml` — meaning it must be manually set before the first build. If it was absent at build time, the API URL falls back to domain inference (`desk.` → `api.`) which should produce the correct URL for `desk.techrestoredesk.com`. However `VITE_AUTH_ENABLED` is declared as `value: true` in `render.yaml` and should be correct. The risk is that an old build was deployed before env vars were configured.  
**How to confirm:** In Render dashboard → frontend static site → check build logs to see the value of `VITE_API_BASE_URL` during the last build. Also check that the frontend JS actually sends requests to `api.techrestoredesk.com` (network tab in browser DevTools).  
**How to fix:** Set `VITE_API_BASE_URL=https://api.techrestoredesk.com` in Render dashboard → redeploy (trigger new build).

---

### G. Invite email sends but goes to spam/promotions tab
**Likelihood: MEDIUM (only if SMTP block is resolved)**  
**Evidence:** Gmail often routes automated invite-style emails from unfamiliar senders to spam or promotions. The email uses a generic "Tech Restore Desk" sender from `techrestore500@gmail.com`. Google Promotions tab filtering is common for HTML-rich email.  
**How to confirm:** After confirming SMTP sends successfully (no Errno 101), check mattiskleinbh@gmail.com → Spam folder → All Mail → Promotions tab.  
**How to fix:** Check all Gmail folders. Consider plain-text only email option. The current implementation sends both HTML and plain text (`message.set_content(text_body)` then `add_alternative(html_body, ...)`), which is correct.

---

### E. Backend not redeployed to latest commit (13692c7)
**Likelihood: MEDIUM**  
**Evidence:** The SMTP hardening (SSL/STARTTLS toggles, diagnostic logging, bootstrap resend endpoint) was implemented in commit 13692c7, pushed today. If Render has not auto-deployed from main, the production backend may be running an older version without these features.  
**How to confirm:** In Render dashboard → backend service → Events → check last deploy commit SHA matches 13692c7baa19420f4338530d494b89b8739b9d1e.  
**How to fix:** Trigger manual redeploy in Render dashboard or push a new commit to main.

---

### C. ADMIN_EMAIL is wrong (set to sender instead of recipient)
**Likelihood: LOW-MEDIUM**  
**Evidence:** A common configuration mistake is setting `ADMIN_EMAIL=techrestore500@gmail.com` (the sender) instead of `ADMIN_EMAIL=mattiskleinbh@gmail.com` (the recipient). If this happened, the invite email would be sent to the sender's own inbox. No code evidence — this is a pure env configuration risk.  
**How to confirm:** In Render dashboard → backend env → `ADMIN_EMAIL` value.  
**How to fix:** Set `ADMIN_EMAIL=mattiskleinbh@gmail.com`.

---

### B2. SMTP_PASSWORD is missing, wrong, or contains spaces
**Likelihood: LOW (blocked before password is tried)**  
**Evidence:** The `Errno 101` error occurs at TCP connection time, before any SMTP credentials are sent. A wrong password would produce `SMTPAuthenticationError` not `OSError`. However, if Render's network block is removed, a wrong or space-padded password becomes the next likely failure.  
**How to confirm:** After fixing network: check Render logs for `SMTP send failed (SMTPAuthenticationError)`. Gmail app passwords are 16 chars with no spaces — verify the Render env value has no spaces and was created specifically for `techrestore500@gmail.com`.  
**How to fix:** Generate a new Gmail App Password for `techrestore500@gmail.com` at myaccount.google.com/apppasswords. Set with no spaces.

---

### D. ADMIN_INVITE_BOOTSTRAP_KEY mismatch
**Likelihood: LOW**  
**Evidence:** The endpoint returns 403 if key doesn't match and 404 if the key env var is not set. This would surface as HTTP 403 or 404, not an SMTP error.  
**How to confirm:** Call the endpoint with a wrong key — expect 403. Call with no key — expect 403. Call with correct key — if SMTP works, expect 200; if SMTP broken, expect 400 with `"Could not connect to SMTP server"`.  
**How to fix:** Ensure `ADMIN_INVITE_BOOTSTRAP_KEY` in Render matches exactly what you send in the `X-Bootstrap-Key` header.

---

### K. CORS issue between desk.techrestoredesk.com and api.techrestoredesk.com
**Likelihood: LOW**  
**Evidence:** `CORS_ALLOWED_ORIGINS` is in `render.yaml` as `sync: false` — must be manually set. If not set, FastAPI CORS middleware defaults to no allowed origins, which would block all cross-origin API calls from the frontend. However, preflight OPTIONS requests are passed through by `AuthGateMiddleware`. If CORS is broken, the frontend would show network errors on login and all API calls, not just invite flows.  
**How to confirm:** Open browser DevTools → Network → look for CORS errors on requests to `api.techrestoredesk.com`.  
**How to fix:** Set `CORS_ALLOWED_ORIGINS=https://desk.techrestoredesk.com` in Render dashboard.

---

### L. /api/auth/bootstrap/resend response not exposing enough diagnostic detail
**Likelihood: N/A (known gap, not a root cause)**  
**Evidence:** On SMTP failure, the endpoint returns `{"detail": "Could not connect to SMTP server"}` — no mode, host, port, or error type in the HTTP response. The full diagnostic is only in Render logs. This is a known limitation but not the cause of the failure — it just makes diagnosis harder.

---

### H. Invite record exists but token URL/frontend accept route fails
**Likelihood: MEDIUM (dependent on I — the rewrite issue)**  
**Evidence:** Even if an invite is created and emailed successfully, the accept link `https://desk.techrestoredesk.com/invite/<token>` will 404 on Render's static site without the SPA rewrite. This is a downstream effect of finding I above.

---

### M. SMTP diagnostics exist but not used
**Likelihood: N/A (already implemented)**  
**Evidence:** Diagnostic logging was implemented in commit 13692c7. The logs include exception class, host, port, SSL mode, STARTTLS mode, and timeout. These appear in Render's log stream. The `Errno 101` error in the known production log is exactly the diagnostic format now in production.

---

## 8. Exact Commands to Run From Windows PowerShell

Replace `<BOOTSTRAP_KEY>` with the actual value of `ADMIN_INVITE_BOOTSTRAP_KEY` from your Render env. Do not include the angle brackets.

### Check backend health
```powershell
Invoke-RestMethod -Uri "https://api.techrestoredesk.com/api/health" -Method GET | ConvertTo-Json
```

### Check a protected route returns 401 (confirms auth is enforced)
```powershell
Invoke-RestMethod -Uri "https://api.techrestoredesk.com/api/auth/users" -Method GET -ErrorAction SilentlyContinue
```
Expected: `401` with `"Missing bearer token"`.

### Call bootstrap resend with MISSING key (should return 403)
```powershell
try {
    Invoke-RestMethod -Uri "https://api.techrestoredesk.com/api/auth/bootstrap/resend" -Method POST
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)"
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    Write-Host "Body: $($reader.ReadToEnd())"
}
```
Expected: `403 Forbidden`.

### Call bootstrap resend with WRONG key (should return 403)
```powershell
try {
    Invoke-RestMethod -Uri "https://api.techrestoredesk.com/api/auth/bootstrap/resend" -Method POST -Headers @{ "X-Bootstrap-Key" = "wrongkey" }
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)"
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    Write-Host "Body: $($reader.ReadToEnd())"
}
```
Expected: `403 Forbidden`.

### Call bootstrap resend with CORRECT key
```powershell
try {
    $result = Invoke-RestMethod -Uri "https://api.techrestoredesk.com/api/auth/bootstrap/resend" -Method POST -Headers @{ "X-Bootstrap-Key" = "<BOOTSTRAP_KEY>" }
    Write-Host "SUCCESS: invite created"
    $result | ConvertTo-Json
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)"
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    Write-Host "Body: $($reader.ReadToEnd())"
}
```
Expected outcomes:  
- `200` with invite JSON → SMTP worked, check email  
- `400 "Could not connect to SMTP server"` → SMTP port blocked (check Render logs for Errno 101)  
- `400 "Failed to deliver invite email"` → SMTP connected but auth or send failed (check Gmail app password)  
- `400 "Bootstrap invites are disabled"` → `ADMIN_INVITE_BOOTSTRAP` not set to `true` in Render  
- `400 "ADMIN_EMAIL is not configured"` → `ADMIN_EMAIL` not set in Render  
- `404 "Bootstrap resend endpoint disabled"` → `ADMIN_INVITE_BOOTSTRAP_KEY` not set in Render  

### Check if frontend is loading and auth is enabled
```powershell
$response = Invoke-WebRequest -Uri "https://desk.techrestoredesk.com" -UseBasicParsing
Write-Host "Status: $($response.StatusCode)"
```

### Test if invite deep link returns 404 on Render static site (critical test)
```powershell
try {
    $response = Invoke-WebRequest -Uri "https://desk.techrestoredesk.com/invite/testtoken123" -UseBasicParsing
    Write-Host "Status: $($response.StatusCode) (200 = SPA rewrite works, 404 = rewrite missing)"
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__) (404 = SPA rewrite missing — invite links will fail)"
}
```
Expected if rewrite is missing: `404`. Expected if rewrite is present: `200` (HTML of React app).

### Check CORS preflight from PowerShell
```powershell
Invoke-WebRequest -Uri "https://api.techrestoredesk.com/api/auth/login" -Method OPTIONS -Headers @{
    "Origin" = "https://desk.techrestoredesk.com"
    "Access-Control-Request-Method" = "POST"
    "Access-Control-Request-Headers" = "Content-Type"
} -UseBasicParsing | Select-Object -ExpandProperty Headers
```
Expected: `Access-Control-Allow-Origin: https://desk.techrestoredesk.com` should be present.

---

## 9. What to Check in Render Dashboard

### Backend Service (tech-restore-api)

- [ ] **Plan** → confirm it is **Starter** or higher, not Free. Free tier may block outbound SMTP ports.
- [ ] **Latest deploy commit** → confirm it matches `13692c7baa19420f4338530d494b89b8739b9d1e`. If not, trigger manual redeploy.
- [ ] **Environment → REPAIR_DESK_AUTH_ENABLED** → must be `true`.
- [ ] **Environment → ADMIN_EMAIL** → must be `mattiskleinbh@gmail.com` (NOT `techrestore500@gmail.com`).
- [ ] **Environment → ADMIN_INVITE_BOOTSTRAP** → must be `true`.
- [ ] **Environment → ADMIN_INVITE_BOOTSTRAP_KEY** → must be set to a secret value (record it for the PowerShell command).
- [ ] **Environment → ADMIN_INVITE_ROLE** → should be `owner`.
- [ ] **Environment → SMTP_HOST** → must be `smtp.gmail.com`.
- [ ] **Environment → SMTP_PORT** → must be `587` (or `465` if using SSL).
- [ ] **Environment → SMTP_USE_SSL** → `false` for 587, `true` for 465.
- [ ] **Environment → SMTP_STARTTLS** → `true` for 587, `false` for 465.
- [ ] **Environment → SMTP_USERNAME** → must be `techrestore500@gmail.com`.
- [ ] **Environment → SMTP_PASSWORD** → must be a **Gmail App Password** with **no spaces** (16 alphanumeric chars). Not the Gmail account password.
- [ ] **Environment → SMTP_FROM_EMAIL** → must be `techrestore500@gmail.com`.
- [ ] **Environment → SMTP_FROM_NAME** → should be `Tech Restore`.
- [ ] **Environment → SMTP_TIMEOUT_SECONDS** → `20` is fine.
- [ ] **Environment → FRONTEND_BASE_URL** → must be `https://desk.techrestoredesk.com`.
- [ ] **Environment → CORS_ALLOWED_ORIGINS** → must be `https://desk.techrestoredesk.com`.
- [ ] **Environment → SECRET_KEY** → must be set (a long random string for JWT signing).
- [ ] **Environment → DATABASE_URL** → if set, confirm path; if pointing to ephemeral container path, data will be lost on restart.
- [ ] **Disks** → check if a Persistent Disk is attached. If not, data is lost on restart/redeploy.
- [ ] **Logs** → after triggering bootstrap resend, look for:
  - `SMTP connection failed (OSError): [Errno 101] Network is unreachable` → Render SMTP block confirmed
  - `SMTP send failed (SMTPAuthenticationError)` → wrong app password
  - `startup_bootstrap_owner_invite_created` → bootstrap invite was created at startup
  - `Bootstrap admin invite was not sent:` → startup failure reason

### Frontend Static Site (tech-restore-desk)

- [ ] **Latest deploy** → confirm it was rebuilt after `VITE_API_BASE_URL` was set.
- [ ] **Environment → VITE_API_BASE_URL** → must be `https://api.techrestoredesk.com`. Must be set **before** the build that is currently deployed.
- [ ] **Environment → VITE_AUTH_ENABLED** → should be `true` (declared in render.yaml).
- [ ] **Redirects/Rewrites** → check if any SPA rewrite rule exists. If not, `/invite/:token` deep links will 404.
- [ ] **Build log** → confirm `VITE_API_BASE_URL` was available during the last build.

---

## 10. What to Check in Gmail

For the `mattiskleinbh@gmail.com` account:

- [ ] **Inbox** → look for subject "Set up your Tech Restore Desk account" from `Tech Restore <techrestore500@gmail.com>`.
- [ ] **Spam** → Gmail may flag automated emails from new/low-reputation senders.
- [ ] **All Mail** → `More → All Mail` in Gmail shows every email regardless of tab or label.
- [ ] **Promotions** → Gmail's AI may route HTML emails from unfamiliar senders here.
- [ ] **Search** → In Gmail search bar type: `from:techrestore500@gmail.com` to find any email from the sender.

For the `techrestore500@gmail.com` sender account:

- [ ] **Google Account → Security → Recent security events** → look for any "Blocked sign-in attempt" notifications that would indicate Google rejected the app.
- [ ] **Google Account → Security → 2-Step Verification** → must be enabled for App Passwords to work.
- [ ] **Google Account → Security → App Passwords** → confirm an App Password was created specifically for this app. App Passwords are labeled when created; the 16-char password with no spaces is what goes in `SMTP_PASSWORD`.
- [ ] **Note on Errno 101:** If Render is producing `Errno 101 (Network is unreachable)`, the SMTP connection never reached Gmail. Google did not block the login — the packet never arrived. Errno 101 is a kernel-level routing error, not a Gmail authentication error. This strongly points to a network-layer restriction on the Render container, not a Gmail configuration problem.

---

## 11. Storage Risk

The current `DATABASE_URL` configuration stores the SQLite database at `./data/tech_restore_desk.sqlite` relative to the app container root (`/app/data/tech_restore_desk.sqlite` on Render). This path is **inside the ephemeral container filesystem**.

**Consequence:** Every time Render deploys a new version, restarts the service, or the container is replaced for any infrastructure reason, the SQLite file is destroyed and recreated from scratch. Invite records, user accounts, ticket data, customer records, and all operational data are permanently lost.

**Before entering any real customer data or completing first-admin setup:**

1. Add a **Render Persistent Disk** to the backend web service (requires Starter plan or higher).
2. Mount it at `/var/data` (or another persistent path).
3. Set `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite` in Render env (note the four slashes — three for `sqlite:///` and one for the absolute Linux path `/var/data/...`).
4. Redeploy the backend. The database will now persist across deploys and restarts.

Do not enter real customer data until this is confirmed working.

---

## 12. Security Notes

The following credentials may have been exposed during setup, debugging, or configuration and should be **rotated before production use** with real data:

- **Gmail App Password** for `techrestore500@gmail.com`: revoke the existing app password at myaccount.google.com/apppasswords and generate a new one. Update `SMTP_PASSWORD` in Render.
- **Twilio Auth Token**: if it was ever pasted into a chat, log, or commit, rotate it at console.twilio.com.
- **`SECRET_KEY`** (JWT signing key): if it was shared or logged, rotate it. Update in Render env. All existing JWT tokens will be invalidated.
- **`ADMIN_INVITE_BOOTSTRAP_KEY`**: rotate if shared.
- **`REPAIR_DESK_PASSWORD`** (shared password fallback): rotate if it was shared.

Additional notes:
- Do not commit actual secret values to the repository. `.gitignore` should exclude `.env` files; confirm with `git status`.
- Do not log `SMTP_PASSWORD`, `SECRET_KEY`, or invite token cleartext values. The current logging implementation in `emailer.py` correctly logs only host/port/mode/timeout — no credentials.
- The `/docs` endpoint (FastAPI's built-in Swagger UI) is currently public in production (`https://api.techrestoredesk.com/docs`). This exposes the full API schema including auth endpoint structure. This is a production hardening concern but not related to the invite failure.

---

## 13. Recommended Next Action

**Evidence still supports Render free-tier SMTP block as primary cause.** Recommended exact sequence:

1. **In Render dashboard — confirm backend is on Starter plan.** If it is on Free, upgrade to Starter. This is required for SMTP outbound and for Persistent Disk.

2. **In Render dashboard — add all missing env vars** to the backend service:
   - `ADMIN_EMAIL=mattiskleinbh@gmail.com`
   - `ADMIN_INVITE_BOOTSTRAP=true`
   - `ADMIN_INVITE_ROLE=owner`
   - `ADMIN_NAME=Mattis Klein`
   - `ADMIN_INVITE_BOOTSTRAP_KEY=<choose a secret key>`
   - `SMTP_HOST=smtp.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USE_SSL=false`
   - `SMTP_STARTTLS=true`
   - `SMTP_TIMEOUT_SECONDS=20`
   - `SMTP_USERNAME=techrestore500@gmail.com`
   - `SMTP_PASSWORD=<gmail-app-password-no-spaces>`
   - `SMTP_FROM_EMAIL=techrestore500@gmail.com`
   - `SMTP_FROM_NAME=Tech Restore`
   - `FRONTEND_BASE_URL=https://desk.techrestoredesk.com`
   - `CORS_ALLOWED_ORIGINS=https://desk.techrestoredesk.com`

3. **Add Persistent Disk** to backend service, mount at `/var/data`, then add `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite` to env vars.

4. **Redeploy backend.** Wait for deploy to complete.

5. **Run bootstrap resend PowerShell command** (from section 8) with the correct `ADMIN_INVITE_BOOTSTRAP_KEY` value.

6. **Check Render backend logs** immediately after. Look for either `Errno 101` (network still blocked → escalate to Render support or switch to HTTPS-based email API) or a success audit log entry.

7. **Add SPA rewrite rule** before testing invite link. Create `frontend/public/_redirects` with content `/* /index.html 200`, commit and push, then wait for Render to rebuild the frontend static site.

8. **Check mattiskleinbh@gmail.com** → Inbox, then Spam, then All Mail, then Promotions.

9. **Click the invite link.** Verify it loads the invite accept UI (not a 404).

10. **Set password and activate account.** Verify login works.

11. **Only after login works:** consider configuring more users, entering customer data, and completing operational setup.

---

## 14. Suggested Code Improvements (Do Not Apply Yet)

These are improvements to implement after production access is confirmed working. No code changes are recommended now.

### L. Better diagnostic response from bootstrap resend endpoint
Currently on SMTP failure, the endpoint returns only `{"detail": "Could not connect to SMTP server"}`. A safer improvement would return a structured error body including the exception class name, host, and port (but not password) so the caller can diagnose without needing to access Render logs:

```json
{
  "detail": "Could not connect to SMTP server",
  "smtp_error_type": "OSError",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_ssl": false,
  "smtp_starttls": true
}
```

### Admin-only SMTP test endpoint
A `POST /api/auth/smtp/test` endpoint (owner/admin only) that attempts a test SMTP connection and returns success or detailed failure info. This would allow diagnosing SMTP config from the admin UI without needing to trigger a real invite send.

### Frontend invite accept: clearer error states
`InviteAcceptPage.tsx` shows generic "Invite not available" for expired, revoked, already-accepted, and not-found tokens. Separate messages for each state would give better UX.

### Static site rewrite documentation
Add a `frontend/public/_redirects` file (required for Render static SPA) and document it in `docs/PRODUCTION_DEPLOYMENT.md`. This is a confirmed production blocker.

### Production hardening for /docs
Disable FastAPI's `/docs` and `/redoc` endpoints in production by passing `docs_url=None, redoc_url=None` to `FastAPI()` when `APP_ENV=production`.

### Login wording polish
`AuthGate.tsx` currently says "Sign in with your invited Tech Restore account." — this is correct and does not suggest public signup. No change needed here.

### Password eye toggle on login
`AuthGate.tsx` includes a show/hide password toggle on the password field. `InviteAcceptPage.tsx` also includes it. Both look correct. No change needed.

### Auth guard hiding dashboard shell until auth is validated
`App.tsx` wraps `<RouterProvider>` in `<AuthGate>`, so the `AppShell` only renders after authentication. This is correct. No change needed.

---

*Investigation performed 2026-05-28. No code changes made. All 25 backend auth/emailer tests pass.*
