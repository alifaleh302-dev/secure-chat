"""
أوضاع تشغيل AES الأربعة — مكتوبة من الصفر خطوة بخطوة.

نستخدم pycryptodome فقط كـ "محرّك AES الخام" لتشفير كتلة واحدة (16 بايت).
كل منطق الأوضاع (ECB, CBC, CTR, GCM + GHASH) مكتوب هنا يدوياً للتعلم.

تسلسل الدرس:
    ECB → نفس النص = نفس المشفّر (يكشف الأنماط) 🔴
    CBC → IV يخفي الأنماط لكن تسلسلي          🟡
    CTR → يحوّل AES إلى stream (متوازٍ)         🟢
    GCM → CTR + GHASH = تشفير + سلامة          ✅
"""

from Crypto.Cipher import AES

BLOCK = 16  # حجم كتلة AES بالبايت


# ---------- محرّك AES الخام (كتلة واحدة) ----------
def _enc_block(key: bytes, block: bytes) -> bytes:
    return AES.new(key, AES.MODE_ECB).encrypt(block)


def _dec_block(key: bytes, block: bytes) -> bytes:
    return AES.new(key, AES.MODE_ECB).decrypt(block)


# ---------- PKCS#7 padding ----------
def pad(data: bytes) -> bytes:
    n = BLOCK - (len(data) % BLOCK)
    return data + bytes([n]) * n


def unpad(data: bytes) -> bytes:
    n = data[-1]
    return data[:-n]


def xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


# ============================================================
# 1) ECB — كل كتلة مستقلة (الأبسط والأخطر)
# ============================================================
def ecb_encrypt(key: bytes, plaintext: bytes) -> bytes:
    data = pad(plaintext)
    return b"".join(_enc_block(key, data[i:i + BLOCK]) for i in range(0, len(data), BLOCK))


def ecb_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    data = b"".join(_dec_block(key, ciphertext[i:i + BLOCK]) for i in range(0, len(ciphertext), BLOCK))
    return unpad(data)


# ============================================================
# 2) CBC — ربط الكتل عبر XOR مع الكتلة السابقة
# ============================================================
def cbc_encrypt(key: bytes, plaintext: bytes, iv: bytes) -> bytes:
    data = pad(plaintext)
    out = bytearray()
    prev = iv
    for i in range(0, len(data), BLOCK):
        block = xor(data[i:i + BLOCK], prev)
        prev = _enc_block(key, block)
        out += prev
    return bytes(out)


def cbc_decrypt(key: bytes, ciphertext: bytes, iv: bytes) -> bytes:
    out = bytearray()
    prev = iv
    for i in range(0, len(ciphertext), BLOCK):
        block = ciphertext[i:i + BLOCK]
        out += xor(_dec_block(key, block), prev)
        prev = block
    return unpad(bytes(out))


# ============================================================
# 3) CTR — يحوّل AES إلى stream cipher (لا padding)
# ============================================================
def _ctr_keystream(key: bytes, nonce: bytes, length: int, start: int = 0) -> bytes:
    """CTR: nonce(8) ‖ counter(8) — عدّاد 64-بت."""
    ks = bytearray()
    counter = start
    while len(ks) < length:
        block = nonce + counter.to_bytes(8, "big")
        ks += _enc_block(key, block)
        counter += 1
    return bytes(ks[:length])


def _gcm_keystream(key: bytes, prefix: bytes, length: int, start: int) -> bytes:
    """GCM: prefix(12) ‖ counter(4) — عدّاد 32-بت (كما في المواصفة NIST)."""
    ks = bytearray()
    counter = start
    while len(ks) < length:
        block = prefix + (counter % (2 ** 32)).to_bytes(4, "big")
        ks += _enc_block(key, block)
        counter += 1
    return bytes(ks[:length])


def ctr_encrypt(key: bytes, nonce: bytes, plaintext: bytes) -> bytes:
    return xor(plaintext, _ctr_keystream(key, nonce, len(plaintext)))


def ctr_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    return xor(ciphertext, _ctr_keystream(key, nonce, len(ciphertext)))


# ============================================================
# 4) GCM — CTR (تبدأ من 2) + GHASH للسلامة (AEAD)
# ============================================================
_R = 0xE1000000000000000000000000000000


def _gf_mul(x: int, y: int) -> int:
    """ضرب في حقل جالوا GF(2^128) — قلب GHASH."""
    z = 0
    v = y
    for i in range(128):
        if (x >> (127 - i)) & 1:
            z ^= v
        if v & 1:
            v = (v >> 1) ^ _R
        else:
            v >>= 1
    return z


def _ghash(h: int, data: bytes) -> int:
    y = 0
    for i in range(0, len(data), BLOCK):
        block = data[i:i + BLOCK].ljust(BLOCK, b"\x00")
        y = _gf_mul(y ^ int.from_bytes(block, "big"), h)
    return y


def _gcm_j0(nonce: bytes) -> bytes:
    if len(nonce) == 12:  # الحالة القياسية: 96 بت
        return nonce + b"\x00\x00\x00\x01"
    # حالة عامة: GHASH على nonce مع الحشو
    h = int.from_bytes(_enc_block(b"\x00" * 16, b"\x00" * 16), "big")
    padded = nonce + b"\x00" * ((16 - len(nonce) % 16) % 16)
    lens = (len(nonce) * 8).to_bytes(8, "big") + (0).to_bytes(8, "big")
    return _ghash(h, padded + lens).to_bytes(16, "big")


def gcm_encrypt(key: bytes, nonce: bytes, plaintext: bytes, aad: bytes = b"") -> tuple[bytes, bytes]:
    """يعيد (ciphertext, tag)."""
    h = int.from_bytes(_enc_block(key, b"\x00" * 16), "big")
    j0 = _gcm_j0(nonce)

    # تشفير CTR يبدأ من inc32(J0) = 2
    start = int.from_bytes(j0[12:], "big") + 1
    ct = xor(plaintext, _gcm_keystream(key, j0[:12], len(plaintext), start))

    # بناء مدخل GHASH: AAD ‖ pad ‖ C ‖ pad ‖ len(AAD) ‖ len(C)
    aad_pad = aad + b"\x00" * ((16 - len(aad) % 16) % 16)
    ct_pad = ct + b"\x00" * ((16 - len(ct) % 16) % 16)
    lens = (len(aad) * 8).to_bytes(8, "big") + (len(ct) * 8).to_bytes(8, "big")
    s = _ghash(h, aad_pad + ct_pad + lens)

    tag = xor(_enc_block(key, j0), s.to_bytes(16, "big"))
    return ct, tag


def gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, aad: bytes = b"") -> bytes:
    """يتحقق من الـ tag أولاً ثم يفك التشفير. يرفض أي تعديل."""
    h = int.from_bytes(_enc_block(key, b"\x00" * 16), "big")
    j0 = _gcm_j0(nonce)

    aad_pad = aad + b"\x00" * ((16 - len(aad) % 16) % 16)
    ct_pad = ciphertext + b"\x00" * ((16 - len(ciphertext) % 16) % 16)
    lens = (len(aad) * 8).to_bytes(8, "big") + (len(ciphertext) * 8).to_bytes(8, "big")
    s = _ghash(h, aad_pad + ct_pad + lens)
    expected = xor(_enc_block(key, j0), s.to_bytes(16, "big"))

    import hmac as _std
    if not _std.compare_digest(expected, tag):
        raise ValueError("GCM: فشل التحقق من السلامة — تم رفض البيانات المعدّلة!")

    start = int.from_bytes(j0[12:], "big") + 1
    return xor(ciphertext, _gcm_keystream(key, j0[:12], len(ciphertext), start))
