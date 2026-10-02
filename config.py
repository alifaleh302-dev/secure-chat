"""
الإعدادات — مفاتيح التبديل (Toggles) التعليمية.

هذا هو أهم ملف في المشروع: منه تُطفئ وتشغّل كل خاصية أمنية، ثم تفتح
Wireshark وترى الفرق فوراً.

كل قيمة يمكن تجاوزها بمتغير بيئة بنفس الاسم، مثال:
    ENCRYPTION=0 CIPHER=RC4 python server.py
"""

import os


def _flag(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() not in ("0", "false", "no", "off", "")


def _text(name: str, default: str) -> str:
    return os.environ.get(name, default)


# ============================================================
# 1) التشفير — السرية (Confidentiality)
# ============================================================
# أطفئها → النص يظهر بالوضوح التام في Wireshark
ENCRYPTION = _flag("ENCRYPTION", True)

# أي وضع تشفير نستخدم؟  (ECB → CBC → CTR → GCM)
#   "RC4"     : ✍️ مكتوب من الصفر (stream)
#   "AES-ECB" : 🔴 يكشف الأنماط
#   "AES-CBC" : 🟡 يخفي الأنماط، تسلسلي
#   "AES-CTR" : 🟢 متوازٍ، بلا سلامة
#   "AES-GCM" : ✅ تشفير + سلامة مدمجان (AEAD)
CIPHER = _text("CIPHER", "AES-CTR")

# ============================================================
# 2) السلامة — Integrity
# ============================================================
# أطفئها → أي تعديل على الرسالة يمرّ دون كشف
INTEGRITY = _flag("INTEGRITY", True)

# كيف نحقق السلامة؟
#   "HMAC" : ✍️ Encrypt-then-MAC (مكتوب من الصفر) — يعمل مع RC4/ECB/CBC/CTR
#   "GCM"  : 📚 مدمج داخل AES-GCM (لا يحتاج HMAC منفصل)
MAC_MODE = _text("MAC_MODE", "HMAC")

# ============================================================
# 3) المصادقة — Authentication
# ============================================================
# أطفئها → لا نتحقق من هوية السيرفر (عرضة لهجوم رجل-في-المنتصف)
AUTHENTICATION = _flag("AUTHENTICATION", True)

# ============================================================
# 4) تبادل المفاتيح — Key Exchange
# ============================================================
#   "ECDH"      : 📚 X25519 (Forward Secrecy)
#   "HARDCODED" : مفتاح ثابت (للمقارنة فقط — غير آمن)
KEY_EXCHANGE = _text("KEY_EXCHANGE", "ECDH")

# ============================================================
# 5) إعدادات الشبكة
# ============================================================
HOST = _text("HOST", "0.0.0.0")
PORT = int(_text("PORT", "5000"))          # منفذ الدردشة (TCP خام + WebSocket)
WEB_PORT = int(_text("WEB_PORT", "8080"))  # منفذ واجهة التحكم (HTTP)
BUFFER = 4096

# مفتاح ثابت يُستخدم فقط عندما KEY_EXCHANGE = "HARDCODED"
HARDCODED_SECRET = b"this-is-a-demo-secret-do-not-use-in-production"


def get_all() -> dict:
    """إرجاع كل الإعدادات كـ dict (لواجهة الويب)."""
    return {
        "ENCRYPTION": ENCRYPTION,
        "CIPHER": CIPHER,
        "INTEGRITY": INTEGRITY,
        "MAC_MODE": MAC_MODE,
        "AUTHENTICATION": AUTHENTICATION,
        "KEY_EXCHANGE": KEY_EXCHANGE,
        "HOST": HOST,
        "PORT": PORT,
    }


def update(values: dict) -> dict:
    """تحديث الإعدادات مباشرة في الذاكرة (من واجهة الويب)."""
    global ENCRYPTION, CIPHER, INTEGRITY, MAC_MODE, AUTHENTICATION, KEY_EXCHANGE
    bools = {"ENCRYPTION", "INTEGRITY", "AUTHENTICATION"}
    allowed = {
        "CIPHER": {"RC4", "AES-ECB", "AES-CBC", "AES-CTR", "AES-GCM"},
        "MAC_MODE": {"HMAC", "GCM"},
        "KEY_EXCHANGE": {"ECDH", "HARDCODED"},
    }
    for key, value in values.items():
        if key in bools:
            globals()[key] = bool(value)
        elif key in allowed and value in allowed[key]:
            globals()[key] = value
    return get_all()


def describe() -> str:
    """وصف مختصر للإعدادات الحالية — يُطبع عند بدء التشغيل."""
    lines = [
        "=" * 56,
        "  إعدادات الأمان الحالية",
        "=" * 56,
        f"  التشفير (ENCRYPTION)      : {'ON ' if ENCRYPTION else 'OFF'}  [{CIPHER}]",
        f"  السلامة (INTEGRITY)       : {'ON ' if INTEGRITY else 'OFF'}  [{MAC_MODE}]",
        f"  المصادقة (AUTHENTICATION) : {'ON ' if AUTHENTICATION else 'OFF'}",
        f"  تبادل المفاتيح            : {KEY_EXCHANGE}",
        "=" * 56,
    ]
    return "\n".join(lines)
