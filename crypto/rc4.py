"""
RC4 — Stream Cipher مكتوب من الصفر.

⚠️ تحذير تعليمي:
    RC4 مهجور أمنياً (تُوجد هجمات معروفة عليه) ولا يُستخدم في الإنتاج.
    الهدف هنا فهم مبدأ "Stream Cipher": توليد تدفق مفاتيح (keystream)
    ثم دمجه مع النص عبر XOR.

الفكرة:
    keystream = RC4(key, len(message))
    ciphertext = message XOR keystream

    فك التشفير بنفس العملية تماماً (XOR متماثل).
"""


def _ksa(key: bytes) -> list[int]:
    """Key-Scheduling Algorithm — تهيئة المصفوفة S بخلط يعتمد على المفتاح."""
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    return S


def _prga(S: list[int], length: int) -> bytes:
    """Pseudo-Random Generation Algorithm — توليد keystream."""
    i = j = 0
    out = bytearray()
    for _ in range(length):
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i] + S[j]) % 256])
    return bytes(out)


def rc4(key: bytes, data: bytes) -> bytes:
    """التشفير وفك التشفير عملية واحدة في RC4."""
    if not key:
        raise ValueError("RC4: المفتاح لا يمكن أن يكون فارغاً")
    S = _ksa(key)
    keystream = _prga(S, len(data))
    return bytes(a ^ b for a, b in zip(data, keystream))


def rc4_encrypt(key: bytes, plaintext: bytes) -> bytes:
    return rc4(key, plaintext)


def rc4_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    return rc4(key, ciphertext)
