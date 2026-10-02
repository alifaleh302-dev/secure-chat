# تشغيل secure-chat محلياً على جهازك — بلا تكاليف

دليل كامل لتشغيل المشروع على كمبيوترك الشخصي (Windows / macOS / Linux)
**بدون أي دفع، وبدون اتصال بالإنترنت أثناء التشغيل**.

---

## الجزء 0 — ماذا نحتاج فعلاً؟ (وما حجم التحميل)

المشروع يستخدم مكتبتين خارجيتين فقط:

| المكتبة | لماذا | الحجم التقريبي |
|---------|-------|----------------|
| `pycryptodome` | AES (كل الأوضاع) — بديل `Crypto` | ~10 م.ب |
| `cryptography` | ECDH (تبادل المفاتيح) + توقيعات | ~5 م.ب |

**إجمالي التحميل: ~15-25 م.ب مرة واحدة فقط.** بعدها يعمل المشروع **بلا إنترنت تماماً**.

> 💡 كل شيء آخر (socket, hashlib, hmac, json, threading) من مكتبة بايثون القياسية — بلا تحميل.

### هل نستطيع الاستغناء عن التحميل؟

نعم، لو أردت صفر تحميل:
- يمكن الاستغناء عن `cryptography` بتعطيل ECDH (`KEY_EXCHANGE=HARDCODED`) — لكنه **أقل أماناً**.
- لا يمكن الاستغناء عن `pycryptodome` إلا بإعادة كتابة AES من الصفر (غير عملي).

> **الخلاصة:** حمّل المكتبتين مرة واحدة، وستعمل بلا إنترنت للأبد.

---

## الجزء 1 — تثبيت بايثون (مرة واحدة)

تأكد أن بايثون **3.10 أو أحدث** مثبّت:

```bash
python --version      # أو: python3 --version
```

إن لم يكن مثبّتاً:
- **Windows**: <https://www.python.org/downloads/> — ✅ ضع علامة **"Add Python to PATH"** أثناء التثبيت.
- **macOS**: `brew install python` أو من python.org
- **Linux**: `sudo apt install python3 python3-pip`
- **كالي لينكس**: مثبّت افتراضياً — تخطَّ هذه الخطوة (انظر القسم التالي).

---

## الجزء 1.5 — كالي لينكس (خاص) 🐉

كالي هو Debian، لذا **كل أوامر لينكس هنا تعمل كما هي**. لكن انتبه لأربع نقاط:

### 1) استخدم `python3` و `pip3` (لا `python`)

في كالي غالباً لا يوجد اختصار `python` (إلا إن ثبّتّ `python-is-python3`):

```bash
python3 --version    # 3.11+ على كالي الحديث
```

> 💡 إن أردت استخدام `python` مباشرة: `sudo apt install python-is-python3`

### 2) لا تثبّت المكتبات بـ pip نظامياً — استخدم بيئة افتراضية

كالي (كأي Debian حديث) يمنع `pip install` خارج البيئة الافتراضية
(خطأ `externally-managed-environment`). الحل — وهو الأنظف أصلاً:

```bash
sudo apt install python3-venv -y      # مرة واحدة إن لم يكن مثبّتاً
cd secure-chat
python3 -m venv .venv
source .venv/bin/activate             # يظهر (.venv) في الطرفية
pip install -r requirements.txt
```

بعد التفعيل، `python` داخل البيئة = `python3` — فتعمل أوامر المشروع كما هي.

### 3) الواجهتان الرسوميتان تحتاجان `python3-tk`

كالي يأتي عادةً مع `tkinter`، لكن إن ظهر
`ModuleNotFoundError: No module named 'tkinter'`:

```bash
sudo apt install python3-tk -y
```

> هذا **فقط** للواجهتين (`server_gui.py` و `client_gui.py`).
> السيرفر والعميل الطرفي **لا يحتاجان** tkinter إطلاقاً.

### 4) تشغيل المشروع — الأمر الكامل

```bash
# 1) مرة واحدة (يحتاج إنترنت)
git clone https://github.com/alifaleh302-dev/secure-chat.git
cd secure-chat
sudo apt install python3-venv -y
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) في كل مرة (بلا إنترنت)
bash run_local.sh
```

ثم افتح: `http://localhost:5000/chat` (الدردشة) و `http://localhost:5000/settings`
(لوحة التحكم — المستخدم `admin`، وكلمة المرور تظهر في سجل السيرفر).

**أو الواجهات الرسومية:**

```bash
python server_gui.py     # إدارة الخادم
python client_gui.py     # العميل
```

### 🕵️ ميزة كالي: Wireshark جاهز

Wireshark مثبّت افتراضياً على كالي — مناسب تماماً لتجارب المشروع:

```bash
sudo wireshark        # أو من القائمة
```

اختر واجهة **Loopback (`lo`)**، وفلتر `tcp.port == 5000`، ثم اتبع تجارب
القسم «الجزء 6» أدناه. ولهذا صُمّم المشروع: لترى الفرق بين نص واضح ومشفّر بعينك.

### 🌐 للاتصال من جهاز آخر في الشبكة

```bash
python3 server.py --host 0.0.0.0 --port 5000
# من الجهاز الآخر: http://<كالي-ip>:5000/chat
```

> إن لم يعمل، اسمح بالمنفذ في جدار الحماية: `sudo ufw allow 5000/tcp`

---

## الجزء 2 — تنزيل المشروع (مرة واحدة)

**الطريقة أ: Git**
```bash
git clone https://github.com/alifaleh302-dev/secure-chat.git
cd secure-chat
```

**الطريقة ب: ZIP** — من صفحة GitHub → زر **Code → Download ZIP** → فك الضغط.

---

## الجزء 3 — تثبيت المكتبات (مرة واحدة، ~20 م.ب)

### الأفضل: بيئة افتراضية (لا تلوّث نظامك)

```bash
cd secure-chat

# إنشاء بيئة افتراضية
python -m venv .venv

# تنشيطها:
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows

# تثبيت المكتبات
pip install -r requirements.txt
```

سترى تحميلاً لمرة واحدة. بعدها:

```bash
python -c "import Crypto, cryptography; print('✅ جاهز')"
```

### تحميل بلا إنترنت؟ (اختياري متقدّم)

على جهاز فيه إنترنت:
```bash
pip download -r requirements.txt -d wheels/
```
انسخ مجلد `wheels/` إلى الجهاز الآخر، ثم:
```bash
pip install --no-index --find-links=wheels/ -r requirements.txt
```

---

## الجزء 4 — تشغيل السيرفر

### الطريقة السريعة (سكربت جاهز)

```bash
bash run_local.sh
```

سيطبع لك الروابط وكلمة المرور. **بديل يدوي:**

### الطريقة اليدوية

```bash
# Linux / macOS
ADMIN_PASSWORD='كلمة-قوية' python server.py --host 127.0.0.1 --port 5000

# Windows (PowerShell)
$env:ADMIN_PASSWORD='كلمة-قوية'; python server.py --host 127.0.0.1 --port 5000

# Windows (CMD)
set ADMIN_PASSWORD=كلمة-قوية && python server.py --host 127.0.0.1 --port 5000
```

الناتج المتوقع:
```
  التشفير (ENCRYPTION)      : ON   [AES-CTR]
  السلامة (INTEGRITY)       : ON   [HMAC]
  المصادقة (AUTHENTICATION) : ON
  تبادل المفاتيح            : ECDH
[*] السيرفر يعمل على المنفذ 5000
```

> 💡 **كلمة المرور:** إن لم تضبط `ADMIN_PASSWORD`، سيطبع السيرفر كلمة عشوائية
> في السجل. في السكربت `run_local.sh` الكلمة الافتراضية هي `local-demo-1234`.

---

## الجزء 5 — استخدم المشروع

### أ) دردشة المتصفح
افتح: **<http://localhost:5000/chat>**

### ب) لوحة التحكم (مفاتيح التبديل التعليمية)
افتح: **<http://localhost:5000/settings>**
- المستخدم: `admin`
- كلمة المرور: ما ضبطته (أو `local-demo-1234`)

من هنا تشغّل/تطفئ التشفير والسلامة والمصادقة، وتبدّل وضع AES.

### ج) عميل بايثون (للمختبر التعليمي الكامل)
افتح **طرفية ثانية** (ونشّط البيئة الافتراضية):

```bash
# Linux/macOS
source .venv/bin/activate

python client.py --name ali                      # AES-CTR افتراضياً
python client.py --name ali --cipher AES-ECB     # 🔴 لتجربة كشف الأنماط
python client.py --name ali --cipher AES-GCM     # ✅ تشفير + سلامة
ENCRYPTION=0 python client.py --name ali         # نص واضح تماماً
```

> 💡 **الأفضل تعليمياً:** استخدم عميل بايثون لأن المتصفح يدعم GCM فقط،
> بينما عميل بايثون يدعم RC4/ECB/CBC/CTR/GCM كاملة.

---

## الجزء 6 — تجربة Wireshark (جوهر المشروع التعليمي)

1. ثبّت [Wireshark](https://www.wireshark.org/download.html) (مجاني).
2. شغّل السيرفر والعميل، وتبادلا رسالة.
3. في Wireshark اختر واجهة **Loopback** (`lo` على Linux، `Adapter for loopback` على Windows).
4. صفّي بالمنفذ: `tcp.port == 5000`
5. جرّب وارتقِ:

| التجربة | الأمر | ما تراه في Wireshark |
|---------|-------|----------------------|
| بلا تشفير | `ENCRYPTION=0 python client.py` | النص واضح تماماً 👀 |
| ECB | `--cipher AES-ECB` | تكرار الكتل يكشف الأنماط |
| CBC | `--cipher AES-CBC` | الأنماط اختفت |
| CTR | `--cipher AES-CTR` | عشوائي، لكن بلا سلامة |
| GCM | `--cipher AES-GCM` | عشوائي + سلامة مدمجة |
| تعديل رسالة | عدّل بايتاً في Wireshark | HMAC يرفض الرسالة |

---

## الجزء 7 — الاختبارات (للتأكد أن كل شيء سليم)

```bash
bash run_tests.sh          # selftest + integration + browser + HTTP
python selftest.py         # 27 اختبار وحدة فقط
```

---

## الجزء 8 — ماذا تكتب في المتغيرات؟ (مرجع سريع)

| المفتاح | القيمة | الأثر |
|---------|--------|-------|
| `HOST` | `127.0.0.1` | محلي فقط (الأأمن) — استخدم `0.0.0.0` لتسمح لأجهزة شبكتك |
| `PORT` | `5000` | منفذ السيرفر |
| `ADMIN_PASSWORD` | كلمة قوية | كلمة لوحة التحكم |
| `ENCRYPTION` | `1` / `0` | تشغيل/إطفاء السرية |
| `CIPHER` | `RC4`\|`AES-ECB`\|`AES-CBC`\|`AES-CTR`\|`AES-GCM` | وضع التشفير |
| `INTEGRITY` | `1` / `0` | تشغيل/إطفاء HMAC |
| `MAC_MODE` | `HMAC` / `GCM` | نوع السلامة |
| `AUTHENTICATION` | `1` / `0` | التحقق من هوية السيرفر |
| `KEY_EXCHANGE` | `ECDH` / `HARDCODED` | تبادل المفاتيح |

مثال:
```bash
CIPHER=AES-ECB ENCRYPTION=1 INTEGRITY=0 python server.py
```

---

## الجزء 9 — الشبكة المحلية (اختياري: جهاز آخر يشارك)

1. شغّل السيرفر على `0.0.0.0`:
   ```bash
   python server.py --host 0.0.0.0 --port 5000
   ```
2. اعرف IP جهازك: `ipconfig` (Windows) أو `ip addr` (Linux/macOS).
3. من الجهاز الآخر: `http://192.168.1.xx:5000/chat`

> ⚠️ هذا مكشوف على شبكتك المحلية فقط (ليس الإنترنت). لا تستخدمه على شبكة عامة.

---

## الجزء 10 — مشاكل شائعة

| المشكلة | الحل |
|---------|------|
| `ModuleNotFoundError: No module named 'Crypto'` | `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'cryptography'` | نفس الأمر أعلاه |
| `Address already in use` | المنفذ مشغول: `--port 5001` أو أوقف العملية القديمة |
| `Permission denied` على المنفذ < 1024 | استخدم منفذاً أعلى من 1024 |
| الصفحة لا تفتح | تأكد أن السيرفر يعمل، وأنك تستخدم `http://` لا `https://` |
| اللوحة تطلب دخولاً دائماً | لم تضبط `ADMIN_PASSWORD` — اقرأ الكلمة من السجل |
| المتصفح لا يعرض رسائل عميل بايثون | كلاهما يعمل؟ راجع أن المنفذ نفسه |
| `python` غير معروف (Windows) | استخدم `py` أو أعد التثبيت مع "Add to PATH" |
| `externally-managed-environment` (كالي/Debian) | لا تثبّت نظامياً — فعّل بيئة افتراضية: `source .venv/bin/activate` |
| `No module named 'tkinter'` (كالي) | `sudo apt install python3-tk` (للواجهتين فقط) |
| `python: command not found` (كالي) | استخدم `python3` أو `sudo apt install python-is-python3` |

---

## الخلاصة: خطواتك

```bash
# 1) مرة واحدة فقط (يحتاج إنترنت)
git clone https://github.com/alifaleh302-dev/secure-chat.git
cd secure-chat
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) في كل مرة (بلا إنترنت)
bash run_local.sh

# 3) ثم افتح المتصفح
#    http://localhost:5000/chat
```

> 🐉 **على كالي لينكس:** استبدل `python` بـ `python3` (أو فعّل البيئة الافتراضية
> أولاً فيعمل `python`)، وثبّت `python3-venv` قبل إنشاء البيئة. التفاصيل في
> «الجزء 1.5» أعلاه.
