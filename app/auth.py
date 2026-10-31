"""Form login: a login page and a signed session cookie.

Every request needs a valid session cookie except the login page itself. API calls
without one get 401 (the page then goes to the login form); pages are redirected.
"""
import base64
import hashlib
import hmac
import html
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs

import bcrypt
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool

COOKIE = "mcpanel_session"
SESSION_SECONDS = 30 * 24 * 3600
FAIL_DELAY = 1.0  # seconds added to each failed login
LOGIN_PAGE = (Path(__file__).parent / "static" / "login.html").read_text()


def setup(app: FastAPI, user: str, password_hash: str) -> None:
    if not password_hash.startswith("$2"):
        raise SystemExit("mcpanel: PANEL_PASSWORD_HASH must be a bcrypt hash (see README)")
    hash_bytes = password_hash.encode()
    # Signing key comes from the hash, so changing the password signs everyone out.
    key = hashlib.sha256(b"mcpanel-session:" + hash_bytes).digest()
    login_lock = threading.Lock()  # one password check at a time

    def sign(payload: str) -> str:
        return hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()

    def make_token() -> str:
        payload = f"{user}:{int(time.time()) + SESSION_SECONDS}"
        return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=") + "." + sign(payload)

    def valid(token: str | None) -> bool:
        try:
            encoded, sig = (token or "").split(".", 1)
            payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode()
            name, expires = payload.rsplit(":", 1)
            return (hmac.compare_digest(sig, sign(payload)) and name == user
                    and int(expires) > time.time())
        except (ValueError, UnicodeDecodeError):
            return False

    def check_password(name: str, password: str) -> bool:
        with login_lock:
            # Always run bcrypt so a wrong username takes as long as a wrong password.
            ok = bcrypt.checkpw(password.encode(), hash_bytes)
            ok = hmac.compare_digest(name.encode(), user.encode()) and ok
            if not ok:
                time.sleep(FAIL_DELAY)
            return ok

    def login_page(error: str = "", name: str = "", status: int = 200) -> HTMLResponse:
        page = (LOGIN_PAGE.replace("{{error}}", html.escape(error))
                .replace("{{user}}", html.escape(name)))
        return HTMLResponse(page, status, headers={"Cache-Control": "no-store"})

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        if request.url.path == "/login" or valid(request.cookies.get(COOKIE)):
            return await call_next(request)
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "not signed in"}, 401)
        return RedirectResponse("login", 303)

    @app.get("/login")
    def login_form(request: Request):
        if valid(request.cookies.get(COOKIE)):
            return RedirectResponse("./", 303)
        return login_page()

    @app.post("/login")
    async def login(request: Request):
        form = parse_qs((await request.body()).decode(errors="replace"))
        name = form.get("username", [""])[0].strip()
        password = form.get("password", [""])[0]
        if not await run_in_threadpool(check_password, name, password):
            return login_page("Wrong username or password.", name, 401)
        resp = RedirectResponse("./", 303)
        # No path: the browser scopes the cookie to the folder the panel is served
        # from (e.g. /mcpanel), so other apps on the same host never see it.
        resp.set_cookie(COOKIE, make_token(), max_age=SESSION_SECONDS, path=None,
                        httponly=True, samesite="strict",
                        secure=request.headers.get("x-forwarded-proto", request.url.scheme) == "https")
        return resp

    @app.post("/logout")
    def logout():
        resp = RedirectResponse("login", 303)
        resp.delete_cookie(COOKIE, path=None)
        return resp
