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

import base64
import hmac
import json

import config
from crypto import auth
from webpages import CHAT_HTML, SETTINGS_HTML


def _authorized(auth_header: str | None) -> bool:
    """تحقق من ترويسة HTTP Basic مقابل بيانات لوحة التحكم."""
    if not auth_header or not auth_header.lower().startswith("basic "):
        return False
    try:
        raw = base64.b64decode(auth_header.split(" ", 1)[1]).decode("utf-8")
        user, _, pw = raw.partition(":")
    except Exception:
        return False
    user_ok = hmac.compare_digest(user, config.ADMIN_USER)
    pw_ok = hmac.compare_digest(pw, config.ADMIN_PASSWORD)
    return user_ok and pw_ok


def route(method: str, path: str, body: bytes, hub,
          headers: dict | None = None) -> tuple[int, str, bytes, dict]:
    """يوجّه طلب HTTP ويعيد (status, content_type, body, extra_headers)."""
    headers = headers or {}

    # /chat عامة (الدردشة نفسها)، وكل ما عداها (لوحة التحكم وواجهات API)
    # محمي: من يصل إليه يستطيع إطفاء التشفير وإبطال الأمان كله.
    protected = path in ("/", "/settings") or path.startswith("/api/")
    if protected and not _authorized(headers.get("authorization")):
        payload = "المصادقة مطلوبة للوصول إلى لوحة التحكم.".encode("utf-8")
        return (401, "text/plain; charset=utf-8", payload,
                {"WWW-Authenticate": 'Basic realm="secure-chat settings"'})

    if method == "GET":
        if path in ("/", "/settings"):
            html = SETTINGS_HTML.replace("__PORT__", str(config.PORT)).encode()
            return 200, "text/html; charset=utf-8", html, {}
        if path == "/chat":
            return 200, "text/html; charset=utf-8", CHAT_HTML.encode(), {}
        if path == "/api/config":
            return 200, "application/json", json.dumps(config.get_all(), ensure_ascii=False).encode(), {}
        if path == "/api/status":
            data = {"config": config.get_all(), "clients": hub.snapshot()}
            return 200, "application/json", json.dumps(data, ensure_ascii=False).encode(), {}
        if path == "/api/identity":
            data = {
                "fingerprint": auth.fingerprint(auth.public_bytes(hub.identity_key)),
                "public_key": auth.public_bytes(hub.identity_key).hex(),
            }
            return 200, "application/json", json.dumps(data, ensure_ascii=False).encode(), {}
        return 404, "text/plain; charset=utf-8", b"Not Found", {}

    if method == "POST" and path == "/api/config":
        try:
            values = json.loads(body.decode() or "{}")
            updated = config.update(values)
            return 200, "application/json", json.dumps({"ok": True, "config": updated}).encode(), {}
        except Exception as exc:
            return 400, "application/json", json.dumps({"ok": False, "error": str(exc)}).encode(), {}

    return 404, "text/plain; charset=utf-8", b"Not Found", {}
