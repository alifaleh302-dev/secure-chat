"""
بروتوكول الرسائل (Framing) + توزيع التشفير.

كل رسالة تُرسل كإطار (frame) بالشكل:
    magic(4) | version(1) | type(1) | flags(1) | length(4) | payload(length)

هذا يشبه طريقة عمل بروتوكولات العالم الحقيقي: طبقة "تأطير" تفصل
الرسائل عن بعضها فوق مجرى TCP (وهو مجرد بايتات متصلة بلا حدود).
"""

import os
import struct

import config
from crypto import aes_modes, hmac_impl, rc4, vigenere

MAGIC = b"SCP1"
VERSION = 1
HEADER = struct.Struct(">4sBBBBI")  # magic, version, type, flags, reserved, length

# أنواع الإطارات
T_HELLO = 1       # عميل → سيرفر: مفتاح عام + قدرات
T_HELLO_ACK = 2   # سيرفر → عميل: مفتاح عام + توقيع
T_MESSAGE = 3     # رسالة دردشة
T_PLAIN = 4       # رسالة غير مشفّرة (عند إطفاء التشفير)
T_SYSTEM = 5      # إشعار نظام (انضم/خرج)
T_ERROR = 6
T_BYE = 7

# أعلام (flags)
F_ENCRYPTED = 0b001
F_MAC = 0b010
F_GCM = 0b100

# رموز الخوارزميات — تُتفاوض في المصافحة
CIPHER_CODES = {"NONE": 0, "RC4": 1, "AES-ECB": 2, "AES-CBC": 3, "AES-CTR": 4, "AES-GCM": 5,
                "VIGENERE": 6}
CODE_CIPHERS = {v: k for k, v in CIPHER_CODES.items()}


def pack_frame(ftype: int, payload: bytes = b"", flags: int = 0) -> bytes:
    return HEADER.pack(MAGIC, VERSION, ftype, flags, 0, len(payload)) + payload


def unpack_frame(data: bytes) -> tuple[int, int, bytes]:
    """يفك إطاراً كاملاً (بعد قراءة الرأس + الحمولة)."""
    magic, version, ftype, flags, _reserved, length = HEADER.unpack(data[:HEADER.size])
    if magic != MAGIC:
        raise ValueError("إطار غير صالح: البصمة (magic) غير مطابقة")
    return ftype, flags, data[HEADER.size:HEADER.size + length]


# ============================================================
# توزيع التشفير حسب الوضع المختار
# ============================================================
def encrypt_message(keys: dict, cipher: str, integrity: bool, plaintext: bytes) -> tuple[bytes, int]:
    """يعيد (payload, flags)."""
    if cipher == "NONE":
        return plaintext, 0

    # الشيفرات الكلاسيكية (فيجينير) لا تستخدم مفاتيح HKDF المشتقة من ECDH،
    # بل مفتاحاً بشرياً قصيراً من الإعدادات — عن قصد ليكون قابلاً للكسر.
    if cipher == "VIGENERE":
        ct = vigenere.vigenere_encrypt(vigenere.resolve_key(config.CLASSICAL_KEY), plaintext)
        payload, flags = ct, F_ENCRYPTED

    else:
        key = keys["enc"]

        if cipher == "RC4":
            ct = rc4.rc4_encrypt(key, plaintext)
            payload, flags = ct, F_ENCRYPTED

        elif cipher == "AES-ECB":
            ct = aes_modes.ecb_encrypt(key, plaintext)
            payload, flags = ct, F_ENCRYPTED

        elif cipher == "AES-CBC":
            iv = os.urandom(16)
            payload = iv + aes_modes.cbc_encrypt(key, plaintext, iv)
            flags = F_ENCRYPTED

        elif cipher == "AES-CTR":
            nonce = os.urandom(8)
            payload = nonce + aes_modes.ctr_encrypt(key, nonce, plaintext)
            flags = F_ENCRYPTED

        elif cipher == "AES-GCM":
            nonce = os.urandom(12)
            ct, tag = aes_modes.gcm_encrypt(key, nonce, plaintext)
            return nonce + ct + tag, F_ENCRYPTED | F_GCM

        else:
            raise ValueError(f"خوارزمية غير معروفة: {cipher}")

    # Encrypt-then-MAC: HMAC على النص المشفّر كاملاً (بعد التشفير!)
    if integrity:
        payload = payload + hmac_impl.hmac_sha256(keys["mac"], payload)
        flags |= F_MAC

    return payload, flags


def decrypt_message(keys: dict, cipher: str, integrity: bool, payload: bytes, flags: int) -> bytes:
    """يفك التشفير ويتحقق من السلامة. يرفض أي تعديل."""
    if not (flags & F_ENCRYPTED) or cipher == "NONE":
        return payload

    key = keys["enc"]

    if cipher == "AES-GCM":
        nonce, rest = payload[:12], payload[12:]
        ct, tag = rest[:-16], rest[-16:]
        return aes_modes.gcm_decrypt(key, nonce, ct, tag)

    # التحقق من HMAC أولاً (Encrypt-then-MAC)
    if flags & F_MAC:
        if not integrity:
            # السلامة مطفأة: نتجاهل الـ tag (لكي نرى في Wireshark أن التعديل يمرّ)
            payload = payload[:-32]
        else:
            body, tag = payload[:-32], payload[-32:]
            if not hmac_impl.hmac_verify(keys["mac"], body, tag):
                raise ValueError("HMAC: فشل التحقق — تم رفض البيانات المعدّلة!")
            payload = body

    if cipher == "RC4":
        return rc4.rc4_decrypt(key, payload)
    if cipher == "AES-ECB":
        return aes_modes.ecb_decrypt(key, payload)
    if cipher == "AES-CBC":
        iv, ct = payload[:16], payload[16:]
        return aes_modes.cbc_decrypt(key, ct, iv)
    if cipher == "AES-CTR":
        nonce, ct = payload[:8], payload[8:]
        return aes_modes.ctr_decrypt(key, nonce, ct)
    if cipher == "VIGENERE":
        return vigenere.vigenere_decrypt(vigenere.resolve_key(config.CLASSICAL_KEY), payload)

    raise ValueError(f"خوارزمية غير معروفة: {cipher}")
