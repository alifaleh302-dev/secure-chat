"""
اشتقاق المفاتيح (KDF) — HKDF (RFC 5869).

نحتاج مشتقّة مفاتيح لأن بروتوكولات الأمان تستخدم مفاتيح منفصلة لكل غرض:
    - مفتاح التشفير (encryption key)
    - مفتاح السلامة (MAC key)

استخدام مفتاح واحد للتشفير و HMAC خطأ أمني شائع. HKDF يشتقّ مفاتيح
مستقلة من سرّ واحد (مثلاً من ECDH shared secret).
"""

import hashlib
import hmac as _std


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """Extract: يضغط المدخل إلى مفتاح موحّد (PRK)."""
    if not salt:
        salt = b"\x00" * hashlib.sha256().digest_size
    return _std.new(salt, ikm, hashlib.sha256).digest()


def hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    """Expand: يوسّع PRK إلى المفاتيح المطلوبة."""
    out = b""
    t = b""
    counter = 1
    while len(out) < length:
        t = _std.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        out += t
        counter += 1
    return out[:length]


def hkdf(salt: bytes, ikm: bytes, info: bytes, length: int) -> bytes:
    return hkdf_expand(hkdf_extract(salt, ikm), info, length)


def derive_keys(shared_secret: bytes, salt: bytes) -> dict:
    """يشتقّ مفاتيح منفصلة للتشفير والسلامة من نفس السرّ."""
    enc_key = hkdf(salt, shared_secret, b"encryption", 32)
    mac_key = hkdf(salt, shared_secret, b"integrity", 32)
    return {"enc": enc_key, "mac": mac_key}
