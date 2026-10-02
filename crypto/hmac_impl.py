"""
HMAC — مكتوب من الصفر (درس منفصل كما طلبت).

HMAC (RFC 2104) يضمن سلامة البيانات (Integrity) والمصادقة على المصدر
عند وجود مفتاح مشترك. هو ليس تشفيراً: النص يبقى مقروءاً، لكن أي تعديل
عليه يُكشف لأن الـ tag لن يتطابق.

المعادلة:
    HMAC(K, m) = H( (K ⊕ opad) ‖ H( (K ⊕ ipad) ‖ m ) )

    ipad = 0x36 مكرّرة  (inner padding)
    opad = 0x5c مكرّرة  (outer padding)

استخدام آمن مهم:
    استخدم hmac.compare_digest() للمقارنة (زمن ثابت) وليس ==
    لتجنّب هجوم التوقيت (Timing Attack).
"""

import hashlib

BLOCK_SIZE = 64  # حجم كتلة SHA-256 بالبايت


def _hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hmac_sha256(key: bytes, message: bytes) -> bytes:
    """حساب HMAC-SHA256 من الصفر."""
    # 1) إذا كان المفتاح أطول من حجم الكتلة، نُجزّئه
    if len(key) > BLOCK_SIZE:
        key = _hash(key)

    # 2) اكمال المفتاح بالأصفار حتى حجم الكتلة
    key = key.ljust(BLOCK_SIZE, b"\x00")

    # 3) بناء الحشوتين الداخلية والخارجية
    ipad = bytes(b ^ 0x36 for b in key)
    opad = bytes(b ^ 0x5C for b in key)

    # 4) المعادلة الأساسية
    inner = _hash(ipad + message)
    return _hash(opad + inner)


def hmac_verify(key: bytes, message: bytes, tag: bytes) -> bool:
    """التحقق من الـ tag بمقارنة ثابتة الزمن."""
    expected = hmac_sha256(key, message)
    import hmac as _std
    return _std.compare_digest(expected, tag)
