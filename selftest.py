"""
اختبار ذاتي — يتحقق من صحة كل الخوارزميات المكتوبة من الصفر.

التشغيل:
    python selftest.py

يقارن نتائجنا بالمعايير المعروفة (RFC test vectors) وبالمكتبات القياسية،
ويتأكد أن كشف التعديل يعمل كما هو متوقع.
"""

import os

from crypto import aes_modes, hmac_impl, kdf, key_exchange, rc4

PASS, FAIL = "✅", "❌"
results = []


def check(name, cond):
    results.append((name, cond))
    print(f"  {PASS if cond else FAIL} {name}")


def test_rc4():
    print("\n[1] RC4")
    key, pt = b"Key", b"Plaintext"
    # متجه اختبار معروف من ويكيبيديا
    ct = rc4.rc4_encrypt(key, pt)
    check("RC4 تشفير مطابق للمتجه القياسي", ct == bytes([0xBB, 0xF3, 0x16, 0xE8, 0xD9, 0x40, 0xAF, 0x0A, 0xD3]))
    check("RC4 فك التشفير يعيد الأصل", rc4.rc4_decrypt(key, ct) == pt)


def test_hmac():
    print("\n[2] HMAC-SHA256")
    import hashlib
    import hmac as std
    key, msg = b"secret-key", b"hello integrity"
    check("HMAC مطابق للمكتبة القياسية", hmac_impl.hmac_sha256(key, msg) == std.new(key, msg, hashlib.sha256).digest())
    tag = hmac_impl.hmac_sha256(key, msg)
    check("HMAC يقبل الرسالة السليمة", hmac_impl.hmac_verify(key, msg, tag))
    check("HMAC يرفض الرسالة المعدّلة", not hmac_impl.hmac_verify(key, msg + b"x", tag))


def test_aes_modes():
    print("\n[3] أوضاع AES (مقارنة بالمكتبة القياسية)")
    from Crypto.Cipher import AES
    key = os.urandom(32)
    pt = b"A" * 16 + b"B" * 16
    iv = os.urandom(16)

    check("ECB مطابق للمكتبة", aes_modes.ecb_encrypt(key, pt) == AES.new(key, AES.MODE_ECB).encrypt(aes_modes.pad(pt)))

    ref_cbc = AES.new(key, AES.MODE_CBC, iv).encrypt(aes_modes.pad(pt))
    check("CBC مطابق للمكتبة", aes_modes.cbc_encrypt(key, pt, iv) == ref_cbc)
    check("CBC فك التشفير يعيد الأصل", aes_modes.cbc_decrypt(key, ref_cbc, iv) == pt)

    nonce8 = os.urandom(8)
    ref_ctr = AES.new(key, AES.MODE_CTR, nonce=nonce8).encrypt(pt)
    check("CTR مطابق للمكتبة", aes_modes.ctr_encrypt(key, nonce8, pt) == ref_ctr)

    nonce12 = os.urandom(12)
    ct, tag = aes_modes.gcm_encrypt(key, nonce12, pt)
    ref = AES.new(key, AES.MODE_GCM, nonce=nonce12)
    ref_ct, ref_tag = ref.encrypt_and_digest(pt)
    check("GCM ciphertext مطابق للمكتبة", ct == ref_ct)
    check("GCM tag مطابق للمكتبة", tag == ref_tag)
    check("GCM يفك التشفير بنجاح", aes_modes.gcm_decrypt(key, nonce12, ct, tag) == pt)

    try:
        aes_modes.gcm_decrypt(key, nonce12, ct, bytes(16))
        check("GCM يرفض tag خاطئ", False)
    except ValueError:
        check("GCM يرفض tag خاطئ", True)


def test_ecdh():
    print("\n[4] تبادل المفاتيح ECDH (X25519 + P-256)")
    a_priv, a_pub = key_exchange.generate_keypair()
    b_priv, b_pub = key_exchange.generate_keypair()
    check("X25519: السرّ المشترك متساوٍ", key_exchange.compute_shared(a_priv, b_pub) == key_exchange.compute_shared(b_priv, a_pub))

    a_priv2, a_pub2 = key_exchange.generate_keypair_p256()
    b_priv2, b_pub2 = key_exchange.generate_keypair_p256()
    check("P-256: السرّ المشترك متساوٍ", key_exchange.compute_shared_p256(a_priv2, b_pub2) == key_exchange.compute_shared_p256(b_priv2, a_pub2))


def test_kdf():
    print("\n[5] اشتقاق المفاتيح HKDF")
    keys = kdf.derive_keys(b"shared-secret", b"salt")
    check("مفتاح التشفير 32 بايت", len(keys["enc"]) == 32)
    check("مفتاح السلامة 32 بايت", len(keys["mac"]) == 32)
    check("المفتاحان مختلفان (فصل المفاتيح)", keys["enc"] != keys["mac"])


def test_protocol():
    print("\n[6] بروتوكول التشفير (Encrypt-then-MAC)")
    import config
    import protocol
    keys = kdf.derive_keys(b"shared", b"salt")

    for cipher in ["RC4", "AES-ECB", "AES-CBC", "AES-CTR"]:
        pt = b"secret message for " + cipher.encode()
        payload, flags = protocol.encrypt_message(keys, cipher, True, pt)
        ok = protocol.decrypt_message(keys, cipher, True, payload, flags) == pt
        check(f"{cipher} + HMAC: دورة كاملة", ok)

        tampered = bytearray(payload)
        tampered[0] ^= 0xFF
        try:
            protocol.decrypt_message(keys, cipher, True, bytes(tampered), flags)
            check(f"{cipher}: يكشف التعديل", False)
        except ValueError:
            check(f"{cipher}: يكشف التعديل", True)

    pt = b"gcm secret"
    payload, flags = protocol.encrypt_message(keys, "AES-GCM", True, pt)
    check("AES-GCM: دورة كاملة", protocol.decrypt_message(keys, "AES-GCM", True, payload, flags) == pt)


def main():
    print("=" * 56)
    print("  اختبار ذاتي — التحقق من الخوارزميات المكتوبة من الصفر")
    print("=" * 56)
    test_rc4()
    test_hmac()
    test_aes_modes()
    test_ecdh()
    test_kdf()
    test_protocol()

    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print("\n" + "=" * 56)
    print(f"  النتيجة: {passed}/{total} اختبار ناجح")
    print("=" * 56)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
