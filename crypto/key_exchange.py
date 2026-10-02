"""
تبادل المفاتيح (Key Exchange) — ECDH على منحنى X25519.

الفكرة: الطرفان يولّدان مفتاحين — خاص وعام. يتبادلان العام فقط.
كل طرف يحسب سرّاً مشتركاً من (مفتاحه الخاص × مفتاح الآخر العام).
السرّ المشترك متساوٍ عند الطرفين ولا يعرفه المتلصص (Sniffer).

هذا هو "Forward Secrecy": حتى لو سُرّب المفتاح الخاص لاحقاً،
الرسائل القديمة تبقى آمنة لأن السرّ المشترك لم يُرسل أصلاً.

نستخدم مكتبة `cryptography` هنا (كتابة X25519 من الصفر غير واقعية للمبتدئ).
"""

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization


def generate_keypair() -> tuple[bytes, bytes]:
    """يعيد (private_bytes, public_bytes)."""
    private = X25519PrivateKey.generate()
    priv_bytes = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_bytes, pub_bytes


def compute_shared(private_bytes: bytes, peer_public_bytes: bytes) -> bytes:
    """يحسب السرّ المشترك من مفتاحنا الخاص ومفتاح الطرف الآخر العام."""
    private = X25519PrivateKey.from_private_bytes(private_bytes)
    peer = X25519PublicKey.from_public_bytes(peer_public_bytes)
    return private.exchange(peer)


# ============================================================
# ECDH على P-256 — للتوافق مع Web Crypto API في المتصفح
# ============================================================
# المتصفح لا يدعم X25519 في كل الإصدارات، لكنه يدعم P-256 دائماً.
# Web Crypto يعيد الإحداثي x فقط (32 بايت) وهو نفس ما تعيده
# cryptography عبر exchange(ec.ECDH(), peer). لذا المفاتيح متوافقة.

from cryptography.hazmat.primitives.asymmetric import ec


def generate_keypair_p256() -> tuple[bytes, bytes]:
    """يعيد (private_scalar_bytes(32), public_uncompressed_point(65))."""
    private = ec.generate_private_key(ec.SECP256R1())
    priv_bytes = private.private_numbers().private_value.to_bytes(32, "big")
    pub_bytes = private.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return priv_bytes, pub_bytes


def compute_shared_p256(private_bytes: bytes, peer_public_bytes: bytes) -> bytes:
    """السرّ المشترك = الإحداثي x (32 بايت) — مطابق لـ deriveBits في المتصفح."""
    private = ec.derive_private_key(int.from_bytes(private_bytes, "big"), ec.SECP256R1())
    peer = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), peer_public_bytes)
    return private.exchange(ec.ECDH(), peer)
