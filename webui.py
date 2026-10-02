"""
واجهة التحكم الويب + صفحة دردشة المتصفح.

هذا الملف مكتبة توجيه (routing) — لا يفتح منفذاً بنفسه. السيرفر الرئيسي
(server.py) هو الذي يوجّه الطلبات إلى هنا، لذا كل شيء يعمل على منفذ واحد:
    /settings  → لوحة تبديل الإعدادات الأمنية
    /chat      → صفحة الدردشة (عميل متصفح عبر WebSocket يدوي)
    /api/*     → واجهات JSON

صفحة المتصفح تستخدم Web Crypto API:
    ECDH P-256 (نفس منحنى السيرفر) + HKDF-SHA256 + AES-GCM.
"""

import hashlib
import hmac
import json
import time
import urllib.parse

import config
from crypto import auth
from webpages import CHAT_HTML, FAVICON, LANDING_HTML, LOGIN_HTML, SETTINGS_HTML

SESSION_TTL = 12 * 3600


def _sign(value: str) -> str:
    return hmac.new(config.SESSION_SECRET, value.encode(), hashlib.sha256).hexdigest()


def _make_session() -> str:
    expiry = str(int(time.time()) + SESSION_TTL)
    return f"{expiry}.{_sign(expiry)}"


def _valid_session(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    expiry, _, sig = token.partition(".")
    if not hmac.compare_digest(sig, _sign(expiry)):
        return False
    try:
        return int(expiry) > time.time()
    except ValueError:
        return False


def _check_credentials(user: str, pw: str) -> bool:
    # نُنظّف الطرفين: الخطأ الشائع هو مسافة زائدة عند اللصق من لوحة النشر.
    return (hmac.compare_digest(user.strip(), config.ADMIN_USER)
            and hmac.compare_digest(pw.strip(), config.ADMIN_PASSWORD))


def _session_cookie(token: str, max_age: int) -> str:
    return (f"sc_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}")


def _login_page(error: bool = False) -> bytes:
    block = '<div class="err">بيانات الدخول غير صحيحة.</div>' if error else ""
    return LOGIN_HTML.replace("__ERROR__", block).encode()


def route(method: str, path: str, body: bytes, hub,
          headers: dict | None = None) -> tuple[int, str, bytes, dict]:
    """يوجّه طلب HTTP ويعيد (status, content_type, body, extra_headers)."""
    headers = headers or {}
    cookies = _parse_cookies(headers.get("cookie"))
    logged_in = _valid_session(cookies.get("sc_session"))

    if method == "GET":
        if path == "/":
            return 200, "text/html; charset=utf-8", LANDING_HTML.encode(), {}
        if path == "/chat":
            return 200, "text/html; charset=utf-8", CHAT_HTML.encode(), {}
        if path == "/favicon.ico":
            return 200, "image/x-icon", FAVICON, {}
        if path == "/robots.txt":
            return 200, "text/plain; charset=utf-8", b"User-agent: *\nDisallow: /settings\n", {}
        if path == "/login":
            return 200, "text/html; charset=utf-8", _login_page(), {}
        if path == "/logout":
            return (302, "text/plain; charset=utf-8", b"",
                    {"Location": "/", "Set-Cookie": _session_cookie("", 0)})
        if path == "/settings":
            if not logged_in:
                return (302, "text/plain; charset=utf-8", b"", {"Location": "/login"})
            html = SETTINGS_HTML.replace("__PORT__", str(config.PORT)).encode()
            return 200, "text/html; charset=utf-8", html, {}
        if path == "/api/config":
            if not logged_in:
                return _denied()
            return 200, "application/json", json.dumps(config.get_all(), ensure_ascii=False).encode(), {}
        if path == "/api/status":
            if not logged_in:
                return _denied()
            data = {"config": config.get_all(), "clients": hub.snapshot()}
            return 200, "application/json", json.dumps(data, ensure_ascii=False).encode(), {}
        if path == "/api/identity":
            if not logged_in:
                return _denied()
            data = {
                "fingerprint": auth.fingerprint(auth.public_bytes(hub.identity_key)),
                "public_key": auth.public_bytes(hub.identity_key).hex(),
            }
            return 200, "application/json", json.dumps(data, ensure_ascii=False).encode(), {}
        return 404, "text/plain; charset=utf-8", b"Not Found", {}

    if method == "POST" and path == "/login":
        form = urllib.parse.parse_qs(body.decode("utf-8", "replace"))
        user = (form.get("username") or [""])[0]
        pw = (form.get("password") or [""])[0]
        if _check_credentials(user, pw):
            return (302, "text/plain; charset=utf-8", b"",
                    {"Location": "/settings", "Set-Cookie": _session_cookie(_make_session(), SESSION_TTL)})
        return 401, "text/html; charset=utf-8", _login_page(error=True), {}

    if method == "POST" and path == "/api/config":
        if not logged_in:
            return _denied()
        try:
            values = json.loads(body.decode() or "{}")
            updated = config.update(values)
            return 200, "application/json", json.dumps({"ok": True, "config": updated}).encode(), {}
        except Exception as exc:
            return 400, "application/json", json.dumps({"ok": False, "error": str(exc)}).encode(), {}

    return 404, "text/plain; charset=utf-8", b"Not Found", {}


def _denied() -> tuple[int, str, bytes, dict]:
    return 401, "application/json", json.dumps({"ok": False, "error": "تسجيل الدخول مطلوب"}).encode(), {}


def _parse_cookies(header: str | None) -> dict[str, str]:
    jar: dict[str, str] = {}
    if not header:
        return jar
    for part in header.split(";"):
        name, sep, value = part.strip().partition("=")
        if sep:
            jar[name] = value
    return jar
