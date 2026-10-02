# AGENTS.md — معرفة المشروع

## نظرة عامة
مشروع تعليمي (الأمن السيبراني): دردشة آمنة بـ **Python + socket**.
كل الخوارزميات مكتوبة **من الصفر** (تعليمي): RC4، HMAC-SHA256،
AES-ECB/CBC/CTR/GCM (+GHASH). `pycryptodome` يُستخدم فقط كمحرك AES خام في
الاختبارات للمقارنة — لا في مسار التشغيل.

## الأوامر
```bash
python server.py [--port 5000]   # سيرفر بمنفذ واحد (HTTP + WebSocket + TCP خام)
python client.py --name ali      # عميل بايثون (TCP خام)
python selftest.py               # 27 اختبار خوارزميات (مطابقة للمعايير)
bash run_tests.sh                # كل الاختبارات (selftest + integration + browser + HTTP)
bash check_modes.sh              # التحقق من كل أوضاع التشفير طرفاً لطرف
python tools/mitm.py --listen 6000 --target 5000 --tamper   # أداة MITM
```

## نقاط معمارية مهمة
- **منفذ واحد**: `server.py` يميّز البروتوكول من أول 4 بايتات — إن كانت
  `protocol.MAGIC` (`b"SCP1"`) فهو عميل بايثون (TCP خام)، وإلا فهو HTTP
  (صفحات الويب أو مصافحة WebSocket يدوية عند وجود `Upgrade: websocket`).
- **السيرفر مصدر الحقيقة**: `HELLO_ACK` يحمل `cipher` و`encryption` و
  `integrity` و`authenticated`. العميل يلتزم بها، لذا التبديل من لوحة التحكم
  يؤثر على الاتصالات الجديدة (بايثون والمتصفح معاً).
- **المتصفح**: Web Crypto API فقط — ECDH P-256 + HKDF-SHA256 + AES-GCM.
  مصافحة WebSocket (RFC 6455) مكتوبة يدوياً في `websocket.py`.
- **التشفير**: `protocol.encrypt_message/decrypt_message` توزّع حسب الوضع.
  Encrypt-then-MAC: HMAC على النص المشفّر كاملاً.
- **GCM**: عدّاد CTR في GCM **4 بايت (32-bit)** — خطأ شائع يفسد الـ tag.
- **مفتاح P-256 الخاص**: يُصدَّر بـ `private_numbers().private_value`.

## قواعد
- المفتاح الخاص `crypto/server_identity.key` **مستثنى من Git** — لا ترفعه أبداً.
- الكود اليدوي **تعليمي فقط** — غير مُدقّق، لا يصلح للإنتاج.
- الترتيب التعليمي لأوضاع AES: ECB → CBC → CTR → GCM.

## المستودع
- GitHub: https://github.com/alifaleh302-dev/secure-chat (الفرع الافتراضي `main`)
- الدفع يتطلب `GITHUB_PERSONAL_ACCESS_TOKEN` (توكن `GITHUB_TOKEN` محدود الصلاحيات).
