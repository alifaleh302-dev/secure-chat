"""
المصادقة (Authentication) — توقيع ECDSA على منحنى P-256 (ES256).

لماذا نحتاجها إذا كان لدينا ECDH؟
    ECDH وحده عرضة لهجوم "رجل في المنتصف" (MITM): المهاجم ينشئ جلسة
    منفصلة مع كل طرف ويقرأ كل شيء. الحل: يوقّع السيرفر مفتاحه المؤقّت
    (ephemeral) بمفتاح طويل المدى، والعميل يعرف المفتاح العام مسبقاً
    (pinning). هذا بالضبط دور شهادات X.509 في TLS.

لماذا P-256 وليس Ed25519؟
    Web Crypto API في المتصفح يدعم P-256 (ECDSA) بشكل موثوق في كل
    المتصفحات، بينما دعم Ed25519 أحدث. نستخدم P-256 ليعمل الطرفان
    (بايثون والمتصفح) بنفس الخوارزمية.

صيغة التوقيع:
    Web Crypto يعيد التوقيع بصيغة IEEE P1363 = r‖s (64 بايت).
    مكتبة cryptography تعيده بصيغة DER. نحوّل بينهما ليتوافق الطرفان.
"""

import base64
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

KEY_FILE = os.path.join(os.path.dirname(__file__), "server_identity.key")
PUB_FILE = os.path.join(os.path.dirname(__file__), "server_identity.pub")


def load_or_create_server_key() -> ec.EllipticCurvePrivateKey:
    """مفتاح السيرفر طويل المدى — يُنشأ أول مرة ويُحفظ."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)

    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(KEY_FILE, "wb") as f:
        f.write(pem)
    with open(PUB_FILE, "wb") as f:
        f.write(public_bytes(key))
    return key


def public_bytes(key) -> bytes:
    """نقطة غير مضغوطة: 0x04 ‖ x(32) ‖ y(32) = 65 بايت (يقرأها Web Crypto)."""
    if isinstance(key, ec.EllipticCurvePrivateKey):
        key = key.public_key()
    return key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )


def sign(key: ec.EllipticCurvePrivateKey, message: bytes) -> bytes:
    """توقيع ECDSA-SHA256 بصيغة r‖s (مطابق لـ Web Crypto)."""
    der = key.sign(message, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def verify(public: bytes, signature: bytes, message: bytes) -> bool:
    """التحقق من التوقيع — يقبل صيغتي r‖s و DER."""
    try:
        if len(signature) == 64:
            r = int.from_bytes(signature[:32], "big")
            s = int.from_bytes(signature[32:], "big")
            signature = encode_dss_signature(r, s)
        pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), public)
        pub.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


def fingerprint(public: bytes) -> str:
    """بصمة مقروءة للمفتاح — للتحقق اليدوي (Out-of-band)."""
    return base64.b64encode(public).decode()


def load_pinned_public() -> bytes | None:
    """المفتاح العام للسيرفر الذي يثبّته العميل مسبقاً."""
    if os.path.exists(PUB_FILE):
        with open(PUB_FILE, "rb") as f:
            return f.read()
    return None
