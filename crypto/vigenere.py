"""
فيجينير (Vigenère) — شيفرة استبدال متعدّد الأبجديات (Polyalphabetic).

⚠️ تحذير تعليمي:
    فيجينير مكسورة عملياً منذ القرن التاسع عشر (هجوم كاسيسكي + تحليل التكرار).
    الهدف هنا هو *فهم* الفكرة، لا استخدامها في أي شيء حقيقي.

الفكرة:
    قيصر يُزيح كل الحروف بإزاحة واحدة ثابتة → سهلة الكسر (26 احتمالاً).
    فيجينير يُزيح كل بايت بإزاحة مختلفة مأخوذة من مفتاح متكرّر:

        C[i] = (P[i] + K[i mod len(K)]) mod 256
        P[i] = (C[i] - K[i mod len(K)]) mod 256

    إزاحة واحدة لكل *موضع* بدل موضع ثابت → الأنماط تتوزّع، لكن ليس كفاية.

نطاق العمل (مهم):
    نطبّقها على البايتات (mod 256) لا على الحروف A-Z.
    السبب: بروتوكولنا ينقل JSON بترميز UTF-8، وفيه نص عربي وإيموجي.
    لو عملنا على A-Z فقط لمرّ النص العربي بالوضوح التام — وهذا مربك.
    المبدأ الرياضي نفسه (إزاحة دورية mod N)، فقط N = 256 بدل 26.

لماذا هي ضعيفة رغم ذلك؟
    - طول المفتاح يُكشف بتحليل التكرار (كل len(K) بايت يعود النمط).
    - المفتاح قصير فيسهل تخمينه/كسره.
    - لا تحمي من تعديل البيانات (لا سلامة) → لذلك نضيف HMAC فوقها.
"""

# المفتاح الافتراضي — قصير عن قصد ليكون كسره ممكناً تعليمياً.
DEFAULT_KEY = b"ahmed"


def _keystream(key: bytes, length: int) -> bytes:
    """يكرّر المفتاح حتى يبلغ طول الرسالة."""
    if not key:
        raise ValueError("فيجينير: المفتاح لا يمكن أن يكون فارغاً")
    reps = (length // len(key)) + 1
    return (key * reps)[:length]


def vigenere_encrypt(key: bytes, plaintext: bytes) -> bytes:
    """C[i] = (P[i] + K[i]) mod 256"""
    ks = _keystream(key, len(plaintext))
    return bytes((p + k) & 0xFF for p, k in zip(plaintext, ks))


def vigenere_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    """P[i] = (C[i] - K[i]) mod 256"""
    ks = _keystream(key, len(ciphertext))
    return bytes((c - k) & 0xFF for c, k in zip(ciphertext, ks))


def resolve_key(raw: str | bytes | None) -> bytes:
    """يحوّل مفتاح الإعدادات (نص) إلى بايتات UTF-8."""
    if raw is None:
        return DEFAULT_KEY
    if isinstance(raw, bytes):
        return raw or DEFAULT_KEY
    text = raw.strip()
    return text.encode("utf-8") if text else DEFAULT_KEY
