# الاستضافة على Cloudflare Tunnel مع نطاق مخصّص — خطوة بخطوة

دليل كامل لمشروع `secure-chat`: من صفر إلى نطاق ثابت `https://chat.example.com`
يعمل مجاناً، مع شرح **كل حقل** تكتبه في إعدادات النشر.

---

## الجزء 0 — فهم الفكرة أولاً

```
متصفح الزائر
     │  HTTPS (نطاقك: chat.example.com)
     ▼
Cloudflare (الطرفية)  ──►  نفق مشفّر  ──►  cloudflared (عندك)
                                              │  HTTP محلي
                                              ▼
                                    server.py  على 127.0.0.1:12000
```

- **لا تحتاج IP عاماً ولا فتح منافذ في الراوتر** — الاتصال صادر من جهازك إلى Cloudflare.
- **Cloudflare تمنحك شهادة TLS مجاناً** — فلا تحتاج Certbot.
- **WebSocket يعمل** عبر النفق (مشروعك يحتاجه).

### التكلفة الحقيقية (كن صريحاً مع نفسك)

| العنصر | التكلفة |
|--------|---------|
| حساب Cloudflare | مجاني |
| Cloudflare Tunnel (نفق مُسمّى، بلا حدود زمنية) | مجاني |
| شهادة TLS | مجانية |
| **النطاق نفسه** (`example.com`) | **مدفوع ~10$/سنة عند المسجّل** |

> ⚠️ **الشرط الذي لا مفرّ منه:** Cloudflare Tunnel يحتاج النطاق **مُداراً داخل
> حسابك في Cloudflare**. على الخطة المجانية لا يكفي إضافة سجل CNAME من مزوّد DNS
> آخر — يجب تغيير الـ **nameservers** عند المسجّل إلى nameservers كلاودفلير.
> لهذا **لا يصلح نطاق فرعي مجاني مثل `duckdns.org`** (لا يسمح بتغيير nameservers).
>
> بدائل بلا نطاق: رابط `trycloudflare.com` المؤقت (يتغيّر كل تشغيل)، أو Render.

---

## الجزء 1 — تجهيز النطاق (مرة واحدة، ~15 دقيقة + انتظار الانتشار)

### 1.1 اشترِ نطاقاً
أي مسجّل: Namecheap, Porkbun, GoDaddy, Cloudflare Registrar... نطاق `.com` عادي يكفي.

### 1.2 أضِف النطاق إلى Cloudflare
1. أنشئ حساباً مجانياً على <https://dash.cloudflare.com/sign-up>.
2. **Add a site** → اكتب `example.com` → اختر خطة **Free**.
3. Cloudflare يعرض لك **nameservers** مثل:
   ```
   aida.ns.cloudflare.com
   walt.ns.cloudflare.com
   ```
   (الأسماء تختلف حسب حسابك — انسخها كما هي.)

### 1.3 غيّر الـ nameservers عند المسجّل
- ادخل لوحة المسجّل → قسم النطاق → **Nameservers** → اختر *Custom/Use my own*.
- احذف الـ nameservers القديمة، والصق **الاثنين** من Cloudflare.
- احفظ.

### 1.4 انتظر التنشيط
- عادة دقائق إلى ساعات، وقد تصل إلى 48 ساعة.
- في Cloudflare سيتحوّل النطاق من *Pending* إلى **Active**. لا تكمل قبل ذلك.

---

## الجزء 2 — تثبيت `cloudflared` على جهازك

```bash
# Linux (amd64)
curl -sL -o /tmp/cloudflared \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x /tmp/cloudflared
sudo mv /tmp/cloudflared /usr/local/bin/cloudflared

cloudflared --version        # يجب أن يطبع رقماً
```

- **macOS**: `brew install cloudflared`
- **Windows**: `winget install --id Cloudflare.cloudflared`

---

## الجزء 3 — إنشاء النفق وربط النطاق

> يمكنك تنفيذ كل هذا بأمر واحد: `DOMAIN=chat.example.com bash deploy_domain.sh`
> لكن افهم الخطوات أولاً.

### 3.1 تسجيل الدخول (مرة واحدة)

```bash
cloudflared tunnel login
```

- يفتح المتصفح → اختر حسابك → **اختر النطاق** (`example.com`).
- يُكتب ملف اعتماد في `~/.cloudflared/cert.pem`.
- 🔒 هذا الملف **سرّ** — لا ترفعه إلى Git.

### 3.2 إنشاء نفق مُسمّى (مرة واحدة)

```bash
cloudflared tunnel create secure-chat
```

الناتج:
```
Tunnel credentials written to: /home/USER/.cloudflared/8f3a....json
Created tunnel secure-chat with id: 8f3a-1234-...
```

- انسخ **المعرّف (UUID)** — ستحتاجه.
- ملف `8f3a....json` **سرّ** أيضاً.

### 3.3 ربط النطاق (ينشئ سجل DNS تلقائياً)

```bash
cloudflared tunnel route dns secure-chat chat.example.com
```

- ينشئ سجل **CNAME** في DNS كلاودفلير يشير إلى `<UUID>.cfargotunnel.com`.
- إن قال "already exists" فلا مشكلة.

### 3.4 ملف الإعداد `~/.cloudflared/config.yml`

```yaml
tunnel: 8f3a-1234-...            # نفس المعرّف من الخطوة 3.2
credentials-file: /home/USER/.cloudflared/8f3a-1234-....json

ingress:
  # كل طلب إلى نطاقك يذهب إلى سيرفرك المحلي
  - hostname: chat.example.com
    service: http://127.0.0.1:12000
  # قاعدة أخيرة إلزامية: كل ما لا يطابق يعيد 404
  - service: http_status:404
```

> **قاعدة ذهبية:** آخر عنصر في `ingress` يجب أن يكون بلا `hostname` (قاعدة التقاط).
> إن نسيتها سيرفض cloudflared الإقلاع.

### 3.5 شغّل السيرفر ثم النفق

```bash
# طرفية 1: سيرفرك
ADMIN_PASSWORD='كلمة-قوية-هنا' python server.py --host 127.0.0.1 --port 12000

# طرفية 2: النفق
cloudflared tunnel run secure-chat
```

افتح `https://chat.example.com` — يجب أن ترى صفحة الهبوط.

### 3.6 اجعله دائماً (لا يموت بإغلاق الطرفية)

```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
systemctl status cloudflared
```

---

## الجزء 4 — ماذا تكتب في إعدادات النشر؟

### 4.1 في `deploy_domain.sh` (الأمر الواحد)

| ما تكتبه | مثال | المعنى |
|----------|------|--------|
| `DOMAIN` | `chat.example.com` | النطاق الذي سيفتحه الزوار. **بدون** `https://` |
| `TUNNEL_NAME` | `secure-chat` | اسم النفق في حسابك (اختياري، له افتراضي) |
| `PORT` | `12000` | منفذ سيرفرك المحلي (اختياري) |
| `ADMIN_PASSWORD` | `كلمة-قوية` | كلمة لوحة التحكم (اختياري) |

```bash
DOMAIN=chat.example.com TUNNEL_NAME=secure-chat PORT=12000 \
ADMIN_PASSWORD='كلمة-قوية-هنا' bash deploy_domain.sh
```

### 4.2 متغيرات بيئة السيرفر (تُقرأ في `config.py`)

| المفتاح | القيمة | ماذا يفعل |
|---------|--------|-----------|
| `HOST` | `127.0.0.1` | **مع Cloudflare Tunnel اتركه محلياً** — لا تكشفه. (`0.0.0.0` فقط داخل Docker/Render) |
| `PORT` | `12000` | منفذ الاستماع. يجب أن يطابق `service:` في `config.yml` |
| `ADMIN_PASSWORD` | كلمة قوية | **اضبطها دائماً** وإلا تُولَّد كلمة جديدة كل تشغيل وتتعذّر اللوحة |
| `ADMIN_USER` | `admin` | مستخدم اللوحة |
| `ENCRYPTION` | `1` أو `0` | تشغيل/إطفاء السرية |
| `CIPHER` | `AES-GCM` | `RC4` \| `AES-ECB` \| `AES-CBC` \| `AES-CTR` \| `AES-GCM` |
| `INTEGRITY` | `1` أو `0` | تشغيل/إطفاء السلامة (HMAC) |
| `MAC_MODE` | `HMAC` أو `GCM` | نوع السلامة |
| `AUTHENTICATION` | `1` أو `0` | التحقق من هوية السيرفر |
| `KEY_EXCHANGE` | `ECDH` أو `HARDCODED` | تبادل المفاتيح |

مثال تشغيل كامل:
```bash
HOST=127.0.0.1 PORT=12000 CIPHER=AES-GCM ENCRYPTION=1 \
INTEGRITY=1 AUTHENTICATION=1 KEY_EXCHANGE=ECDH \
ADMIN_PASSWORD='كلمة-قوية-هنا' python server.py
```

> 💡 لا تكتب `https` أو مسارات في هذه المتغيرات — قيم صريحة فقط.

### 4.3 في لوحة Cloudflare (Zero Trust)

مسار النفق: **Networking → Tunnels → secure-chat → Routes → Add route → Published application**

| الحقل | ماذا تكتب | ملاحظات |
|-------|-----------|---------|
| **Subdomain** | `chat` | أو أي اسم تريده |
| **Domain** | `example.com` | من القائمة المنسدلة |
| **Path** | اتركه فارغاً | إلا إن أردت تقييد مسار |
| **Service → Type** | `HTTP` | لأن سيرفرك HTTP محلي (TLS تتولاه Cloudflare) |
| **Service → URL** | `127.0.0.1:12000` | نفس `PORT` عندك |

هذا يكافئ ما في `config.yml` — يكفي أحدهما.

---

## الجزء 5 — اختبار أن كل شيء يعمل

```bash
# 1) السيرفر محلياً
curl -I http://127.0.0.1:12000/chat          # متوقع 200

# 2) عبر النطاق
curl -I https://chat.example.com/chat        # متوقع 200

# 3) WebSocket عبر النطاق (اختبار مشروعك)
python test_public.py chat.example.com 443

# 4) حالة النفق
cloudflared tunnel info secure-chat
```

النتيجة المتوقعة في الاختبار 3: مصافحة WebSocket ناجحة + `cipher=AES-GCM`.

---

## الجزء 6 — النشر على Render (بديل: استضافة سحابية، بلا جهازك)

هنا السيرفر لا يعمل عندك، بل داخل Render. الخطوات:

### 6.1 إنشاء الخدمة
1. <https://dashboard.render.com> → سجّل بحساب GitHub.
2. **New +** → **Web Service** → اختر مستودع `secure-chat`.
3. الإعدادات:

| الحقل في Render | ماذا تختار |
|-----------------|-----------|
| **Language / Runtime** | `Docker` |
| **Instance Type** | `Free` |
| **Health Check Path** | `/chat` |
| **Dockerfile Path** | `./Dockerfile` |

> ⚠️ **لا تستخدم `/settings` كفحص صحة** — فهي تحوّل 302 إلى `/login`،
> وقد يعتبرها Render فشلاً. استخدم `/chat`.

4. **Create Web Service** → انتظر البناء (~دقيقتان) → رابط `secure-chat-xxxx.onrender.com`.

### 6.2 متغيرات البيئة في Render
**Environment → Add Environment Variable:**

| Key | Value | لماذا |
|-----|-------|-------|
| `ADMIN_PASSWORD` | كلمة قوية | **إلزامي** — بدونها اللوحة غير قابلة للوصول |
| `CIPHER` | `AES-GCM` | الوضع الافتراضي |
| `ENCRYPTION` | `1` | |
| `INTEGRITY` | `1` | |
| `AUTHENTICATION` | `1` | |
| `KEY_EXCHANGE` | `ECDH` | |

> 🚫 **لا تضبط `PORT`** — Render يضخّه تلقائياً والسيرفر يقرأه من `config.py`.
> 🚫 **لا تضبط `HOST`** — `render.yaml` يضبطه `0.0.0.0` مسبقاً.

### 6.3 الطريقة الأسرع: Blueprint (`render.yaml`)
المشروع يحتوي `render.yaml` جاهزاً:
```bash
# New + → Blueprint → اختر المستودع → Apply
```
Render يقرأ الإعدادات من الملف نيابة عنك. بعد الإنشاء اضبط `ADMIN_PASSWORD`
من **Environment** (الملف يعلّمه `sync: false` أي "اطلبه من المستخدم").

### 6.4 نطاق مخصّص على Render
1. **Settings → Custom Domains → Add Custom Domain**.
2. أدخل `chat.example.com`.
3. Render يعرض السجل المطلوب:
   - **CNAME** → `secure-chat-xxxx.onrender.com`
   - أو **A records** إن كان النطاق جذرياً (`example.com`).
4. أضف السجل عند مزوّد DNS (هنا **لا تحتاج** نقل nameservers — CNAME يكفي).
5. شهادة TLS تلقائية.

### 6.5 قيود Render المجانية (اعرفها قبل العرض)
- تنام بعد **~15 دقيقة** خمول؛ أول طلب يستغرق ~30-60 ثانية استيقاظاً.
- **WebSocket يعمل** على الخطة المجانية (مهم لمشروعك).
- نظام ملفات مؤقت: **مفتاح هوية السيرفر يتغيّر** عند كل إعادة تشغيل،
  فبصمة السيرفر (fingerprint) تتغيّر. التثبيت (pinning) يعمل فقط خلال عمر الحاوية.
- حصة نطاقات مخصّصة محدودة — راجع [توثيق Render](https://render.com/docs/custom-domains).

---

## الجزء 7 — جدول الخلاصة: أي طريقة تناسبك؟

| | Cloudflare Tunnel مُسمّى | Render + نطاق مخصّص | trycloudflare مؤقت |
|---|---|---|---|
| **نطاق ثابت** | ✅ نطاقك | ✅ نطاقك | ❌ يتغيّر كل تشغيل |
| **التكلفة** | مجاني + سعر النطاق | مجاني + سعر النطاق | مجاني تماماً |
| **يحتاج جهازك يعمل؟** | ✅ نعم | ❌ لا | ✅ نعم |
| **نقل nameservers** | ✅ مطلوب | ❌ غير مطلوب (CNAME) | — |
| **المناسبة** | عرض دائم من جهازك | استضافة مستقلة | تجربة سريعة |

---

## الجزء 8 — مشاكل شائعة وحلولها

| المشكلة | السبب | الحل |
|---------|-------|------|
| `403` أو صفحة خطأ Cloudflare | النطاق ما زال *Pending* | انتظر التنشيط في Cloudflare |
| `502 Bad Gateway` | `config.yml` يشير لمنفذ خاطئ | تأكد أن `service:` يطابق `PORT`، والسيرفر يعمل |
| `cloudflared` يرفض الإقلاع | لا توجد قاعدة التقاط أخيرة | أضف `- service: http_status:404` في آخر `ingress` |
| النفق يعمل لكن النطاق لا يفتح | سجل DNS مفقود | `cloudflared tunnel route dns secure-chat chat.example.com` |
| اللوحة `/settings` تطلب دخولاً دائماً | `ADMIN_PASSWORD` غير مضبوط | اضبطه ثم أعد التشغيل |
| `ERR_INVALID_AUTH_CREDENTIALS` | نسخة قديمة بـ HTTP Basic | حدّث الكود (الإصدار الحالي بجلسة) |
| WebSocket يفشل عبر Render | فحص صحة خاطئ | استخدم `/chat` كـ Health Check |
| `ModuleNotFoundError: Crypto` | المكتبات غير مثبّتة | `pip install -r requirements.txt` |

---

## الجزء 9 — أمان (لا تتجاهله)

- 🔒 `~/.cloudflared/cert.pem` و`*.json` **أسرار** — مستثناة في `.gitignore`، لا ترفعها.
- 🔒 لا تكشف `HOST=0.0.0.0` مع Tunnel — اتركه `127.0.0.1`.
- 🔒 `ADMIN_PASSWORD` قوية، وليست في الكود أو المستودع (متغير بيئة فقط).
- 🔒 هذا المشروع **تعليمي**: الكود اليدوي للتشفير غير مُدقّق. للإنتاج الحقيقي استخدم TLS + مكتبات مدقّقة.
- 💡 فكّر بإضافة **Cloudflare Access** أمام اللوحة (طبقة تحقق إضافية) — مجاني حتى 50 مستخدماً.
