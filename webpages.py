"""صفحات HTML لواجهة التحكم ودردشة المتصفح (قوالب نصية)."""

FAVICON = (
    b"\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00 \x00\x68\x04\x00\x00"
    b"\x16\x00\x00\x00" + b"\x00" * (40 + 1024)
)

LANDING_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>دردشة آمنة — مشروع تعليمي</title>
<style>
  :root { --bg:#0d1117; --card:#161b22; --line:#30363d; --fg:#e6edf3; --mut:#8b949e; --acc:#2f81f7; }
  * { box-sizing:border-box; }
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         font-family:system-ui,Segoe UI,Tahoma,sans-serif; background:var(--bg); color:var(--fg); padding:24px; }
  .box { max-width:620px; width:100%; background:var(--card); border:1px solid var(--line);
         border-radius:16px; padding:32px; }
  h1 { margin:0 0 8px; font-size:24px; }
  p.sub { margin:0 0 24px; color:var(--mut); font-size:14px; line-height:1.7; }
  a.card { display:block; text-decoration:none; color:var(--fg); border:1px solid var(--line);
           border-radius:12px; padding:16px 18px; margin-bottom:12px; transition:.15s; }
  a.card:hover { border-color:var(--acc); background:#0d1117; }
  a.card b { display:block; font-size:15px; margin-bottom:4px; }
  a.card span { color:var(--mut); font-size:13px; }
  .lock { font-size:12px; color:var(--mut); border-top:1px solid var(--line); margin-top:20px; padding-top:14px; }
</style>
</head>
<body>
<div class="box">
  <h1>🔐 دردشة آمنة</h1>
  <p class="sub">مشروع تعليمي: مصافحة WebSocket يدوية + ECDH P-256 + HKDF-SHA256 + AES-GCM،
     مكتوبة فوق <code>socket</code> الخام بلا مكتبات جاهزة.</p>

  <a class="card" href="/chat">
    <b>💬 فتح الدردشة →</b>
    <span>عامة للجميع — القناة محمية بمفاتيح مؤقتة لكل جلسة.</span>
  </a>
  <a class="card" href="/settings">
    <b>⚙️ لوحة التحكم →</b>
    <span>محمية بكلمة مرور — فيها مفاتيح التبديل التعليمية (التشفير/السلامة/المصادقة).</span>
  </a>

  <div class="lock">🔒 لوحة التحكم تتطلب تسجيل دخول (المستخدم: <code>admin</code>).</div>
</div>
</body>
</html>"""


LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>تسجيل الدخول — لوحة التحكم</title>
<style>
  :root { --bg:#0d1117; --card:#161b22; --line:#30363d; --fg:#e6edf3; --mut:#8b949e; --acc:#2f81f7; }
  * { box-sizing:border-box; }
  body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         font-family:system-ui,Tahoma,sans-serif; background:var(--bg); color:var(--fg); padding:24px; }
  form { max-width:380px; width:100%; background:var(--card); border:1px solid var(--line);
         border-radius:16px; padding:28px; }
  h1 { margin:0 0 6px; font-size:19px; }
  p { margin:0 0 20px; color:var(--mut); font-size:13px; }
  label { display:block; font-size:13px; margin:12px 0 6px; color:var(--mut); }
  input { width:100%; background:#0d1117; color:var(--fg); border:1px solid var(--line);
          border-radius:9px; padding:11px 13px; font-family:inherit; font-size:14px; }
  button { width:100%; margin-top:20px; background:var(--acc); color:#fff; border:0;
           border-radius:9px; padding:12px; font-size:15px; cursor:pointer; font-family:inherit; }
  .err { background:#3d1418; border:1px solid #f85149; color:#ffb3b8; border-radius:9px;
         padding:10px 13px; font-size:13px; margin-bottom:8px; }
  a { color:var(--acc); font-size:13px; display:inline-block; margin-top:16px; }
</style>
</head>
<body>
<form method="POST" action="/login">
  <h1>🔒 لوحة التحكم</h1>
  <p>هذه الصفحة تحكّم في أمان الخادم كله — دخولها محمي.</p>
  __ERROR__
  <label for="u">المستخدم</label>
  <input id="u" name="username" value="admin" autocomplete="username" autofocus>
  <label for="p">كلمة المرور</label>
  <input id="p" name="password" type="password" autocomplete="current-password">
  <button type="submit">دخول</button>
  <a href="/chat">→ الذهاب إلى الدردشة</a>
</form>
</body>
</html>"""


SETTINGS_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة تحكم السيرفر الآمن</title>
<style>
  :root { --bg:#0d1117; --card:#161b22; --line:#30363d; --fg:#e6edf3; --mut:#8b949e;
          --acc:#2f81f7; --ok:#3fb950; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,Segoe UI,Tahoma,sans-serif; background:var(--bg); color:var(--fg); }
  header { padding:20px 28px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;}
  h1 { margin:0; font-size:20px; }
  a.btn, button { background:var(--acc); color:#fff; border:0; padding:9px 16px; border-radius:8px;
                  text-decoration:none; font-size:14px; cursor:pointer; }
  .wrap { padding:24px 28px; display:grid; gap:16px; max-width:900px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 20px; }
  .card h2 { margin:0 0 4px; font-size:15px; }
  .card p { margin:0 0 14px; color:var(--mut); font-size:13px; }
  .row { display:flex; align-items:center; justify-content:space-between; padding:9px 0; border-top:1px solid var(--line); }
  .row:first-of-type { border-top:0; }
  select { background:#0d1117; color:var(--fg); border:1px solid var(--line); border-radius:8px; padding:7px 10px; }
  .sw { position:relative; width:46px; height:26px; }
  .sw input { opacity:0; width:0; height:0; }
  .sl { position:absolute; inset:0; background:#30363d; border-radius:26px; transition:.2s; cursor:pointer; }
  .sl:before { content:""; position:absolute; height:20px; width:20px; left:3px; top:3px; background:#fff; border-radius:50%; transition:.2s; }
  input:checked + .sl { background:var(--ok); }
  input:checked + .sl:before { transform:translateX(20px); }
  code { background:#0d1117; padding:2px 6px; border-radius:6px; font-size:12px; word-break:break-all; }
  .status { color:var(--ok); font-size:13px; }
</style>
</head>
<body>
<header>
  <h1>🔐 لوحة تحكم السيرفر الآمن</h1>
  <span>
    <a class="btn" href="/chat">فتح الدردشة →</a>
    <a class="btn" href="/logout" style="background:#30363d">خروج</a>
  </span>
</header>
<div class="wrap">

  <div class="card">
    <h2>إعدادات الأمان</h2>
    <p>غيّر أي خاصية ثم افتح Wireshark على المنفذ <code>__PORT__</code> لترى الفرق فوراً.</p>

    <div class="row"><span>التشفير (السرية)</span>
      <label class="sw"><input type="checkbox" id="ENCRYPTION"><span class="sl"></span></label></div>

    <div class="row"><span>وضع التشفير</span>
      <select id="CIPHER">
        <option>RC4</option><option>AES-ECB</option><option>AES-CBC</option>
        <option>AES-CTR</option><option>AES-GCM</option><option>VIGENERE</option>
      </select></div>

    <div class="row"><span>مفتاح فيجينير</span>
      <input type="text" id="CLASSICAL_KEY" value="ahmed" style="max-width:120px"></div>

    <div class="row"><span>السلامة (كشف التعديل)</span>
      <label class="sw"><input type="checkbox" id="INTEGRITY"><span class="sl"></span></label></div>

    <div class="row"><span>طريقة السلامة</span>
      <select id="MAC_MODE"><option>HMAC</option><option>GCM</option></select></div>

    <div class="row"><span>المصادقة</span>
      <label class="sw"><input type="checkbox" id="AUTHENTICATION"><span class="sl"></span></label></div>

    <div class="row"><span>تبادل المفاتيح</span>
      <select id="KEY_EXCHANGE"><option>ECDH</option><option>HARDCODED</option></select></div>

    <div class="row"><span class="status" id="msg"></span>
      <button onclick="save()">حفظ الإعدادات</button></div>
  </div>

  <div class="card">
    <h2>المتصلون الآن</h2>
    <p id="clients">لا يوجد أحد.</p>
  </div>

  <div class="card">
    <h2>هوية السيرفر (للمصادقة)</h2>
    <p>ثبّت هذه البصمة في العميل (Out-of-band) لمنع هجوم رجل-في-المنتصف.</p>
    <code id="fp">...</code>
  </div>
</div>

<script>
const KEYS = ["ENCRYPTION","CIPHER","INTEGRITY","MAC_MODE","AUTHENTICATION","KEY_EXCHANGE","CLASSICAL_KEY"];
const BOOLS = ["ENCRYPTION","INTEGRITY","AUTHENTICATION"];

async function load() {
  const cfg = await (await fetch("/api/config")).json();
  for (const k of KEYS) {
    const el = document.getElementById(k);
    if (BOOLS.includes(k)) el.checked = cfg[k];
    else el.value = cfg[k];
  }
  const st = await (await fetch("/api/status")).json();
  const c = st.clients;
  document.getElementById("clients").textContent =
    c.length ? c.map(x => `${x.name} (${x.mode}, ${x.cipher})`).join(" • ") : "لا يوجد أحد.";
  const id = await (await fetch("/api/identity")).json();
  document.getElementById("fp").textContent = id.fingerprint;
}

async function save() {
  const body = {};
  for (const k of KEYS) {
    const el = document.getElementById(k);
    body[k] = BOOLS.includes(k) ? el.checked : el.value;
  }
  const res = await (await fetch("/api/config", {
    method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)
  })).json();
  document.getElementById("msg").textContent = res.ok ? "✅ تم الحفظ" : "❌ خطأ";
  setTimeout(() => document.getElementById("msg").textContent = "", 2500);
}

load();
setInterval(load, 3000);
</script>
</body>
</html>"""


CHAT_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>دردشة آمنة (WebSocket)</title>
<style>
  :root { --bg:#0d1117; --card:#161b22; --line:#30363d; --fg:#e6edf3; --mut:#8b949e; --acc:#2f81f7; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,Tahoma,sans-serif; background:var(--bg); color:var(--fg);
         display:flex; flex-direction:column; height:100vh; }
  header { padding:14px 20px; border-bottom:1px solid var(--line); display:flex; gap:12px; align-items:center; flex-wrap:wrap;}
  h1 { font-size:17px; margin:0; }
  input, button { font-family:inherit; }
  #log { flex:1; overflow-y:auto; padding:18px 20px; display:flex; flex-direction:column; gap:8px; }
  .msg { max-width:70%; padding:9px 13px; border-radius:12px; font-size:14px; line-height:1.5; }
  .me { align-self:flex-start; background:var(--acc); color:#fff; }
  .other { align-self:flex-end; background:#21262d; }
  .sys { align-self:center; color:var(--mut); font-size:12px; }
  footer { padding:12px 20px; border-top:1px solid var(--line); display:flex; gap:10px; }
  #text { flex:1; background:#0d1117; border:1px solid var(--line); border-radius:10px; padding:11px 14px; color:var(--fg); }
  #send { background:var(--acc); color:#fff; border:0; border-radius:10px; padding:0 20px; cursor:pointer; }
  .badge { font-size:12px; background:#21262d; padding:4px 10px; border-radius:20px; color:var(--mut); }
  a { color:var(--acc); }
</style>
</head>
<body>
<header>
  <h1>💬 دردشة آمنة</h1>
  <span class="badge" id="status">جارٍ الاتصال…</span>
  <span class="badge" id="cipher">—</span>
  <span class="badge" id="auth">—</span>
  <a href="/settings" style="margin-inline-start:auto">⚙️ الإعدادات</a>
</header>
<div id="log"></div>
<footer>
  <input id="text" placeholder="اكتب رسالتك…" autocomplete="off" disabled>
  <button id="send" disabled>إرسال</button>
</footer>

<script>
const MAGIC = new Uint8Array([0x53,0x43,0x50,0x31]); // "SCP1"
const T_HELLO=1, T_HELLO_ACK=2, T_MESSAGE=3, T_SYSTEM=5;
const F_ENCRYPTED=1, F_MAC=2, F_GCM=4;
const CIPHER_CODES = {NONE:0, RC4:1, "AES-ECB":2, "AES-CBC":3, "AES-CTR":4, "AES-GCM":5, VIGENERE:6};

let ws, encKey, macKey, myName, useEnc = true, integrity = true, cipherMode = "AES-GCM", classicalKey = "ahmed";
const logEl = document.getElementById("log");
const statusEl = document.getElementById("status");

// ---------- فيجينير على البايتات (mod 256) — نفس منطق بايثون ----------
function vigenereTransform(data, key, decrypt) {
  const kb = new TextEncoder().encode(key);
  if (!kb.length) throw new Error("مفتاح فيجينير فارغ");
  const out = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) {
    const k = kb[i % kb.length];
    out[i] = decrypt ? (data[i] - k) & 0xFF : (data[i] + k) & 0xFF;
  }
  return out;
}

// ---------- HMAC-SHA256 عبر Web Crypto ----------
async function hmacTag(data) {
  const sig = await crypto.subtle.sign("HMAC", macKey, data);
  return new Uint8Array(sig);
}

function log(text, cls) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.textContent = text;
  logEl.appendChild(d);
  logEl.scrollTop = logEl.scrollHeight;
}

function frame(type, payload, flags=0) {
  payload = payload || new Uint8Array();
  const buf = new Uint8Array(12 + payload.length);
  buf.set(MAGIC, 0);
  buf[4] = 1; buf[5] = type; buf[6] = flags; buf[7] = 0;
  new DataView(buf.buffer).setUint32(8, payload.length, false);
  buf.set(payload, 12);
  return buf;
}

function parseFrame(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const len = dv.getUint32(8, false);
  return { type: buf[5], payload: buf.slice(12, 12 + len) };
}

const hex = u8 => [...u8].map(b => b.toString(16).padStart(2,"0")).join("");
const unhex = s => new Uint8Array(s.match(/.{1,2}/g).map(h => parseInt(h,16)));

async function sha256(bytes) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
}

function concat(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a); out.set(b, a.length);
  return out;
}

function equalBytes(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

async function start() {
  myName = prompt("اسمك؟", "browser-user") || "browser-user";

  // 1) مفتاح ECDH مؤقّت (P-256)
  const kp = await crypto.subtle.generateKey({name:"ECDH", namedCurve:"P-256"}, false, ["deriveBits"]);
  const myPub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey)); // 65 بايت

  ws = new WebSocket(`${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/`);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    statusEl.textContent = "متصل — جارٍ المصافحة…";
    const hello = new TextEncoder().encode(JSON.stringify({pubkey: hex(myPub), mode:"browser", name: myName}));
    ws.send(frame(T_HELLO, hello));
  };

  ws.onmessage = async (ev) => {
    const { type, payload } = parseFrame(new Uint8Array(ev.data));

    if (type === T_HELLO_ACK) {
      const ack = JSON.parse(new TextDecoder().decode(payload));
      const serverPub = unhex(ack.pubkey);
      document.getElementById("cipher").textContent = ack.cipher;
      useEnc = ack.encryption !== false;

      // 2) السرّ المشترك عبر ECDH
      const serverKey = await crypto.subtle.importKey(
        "raw", serverPub, {name:"ECDH", namedCurve:"P-256"}, false, []);
      const shared = new Uint8Array(await crypto.subtle.deriveBits(
        {name:"ECDH", public: serverKey}, kp.privateKey, 256));

      // 3) salt = SHA-256(clientPub ‖ serverPub) — مطابق للسيرفر
      const salt = await sha256(concat(myPub, serverPub));

      // 4) HKDF: نشتقّ مفتاح التشفير ومفتاح السلامة (HMAC) بشكل منفصل
      const base = await crypto.subtle.importKey("raw", shared, "HKDF", false, ["deriveBits"]);
      encKey = await crypto.subtle.importKey(
        "raw", await crypto.subtle.deriveBits(
          {name:"HKDF", hash:"SHA-256", salt, info: new TextEncoder().encode("encryption")}, base, 256),
        {name:"AES-GCM"}, false, ["encrypt","decrypt"]);
      macKey = await crypto.subtle.importKey(
        "raw", await crypto.subtle.deriveBits(
          {name:"HKDF", hash:"SHA-256", salt, info: new TextEncoder().encode("integrity")}, base, 256),
        {name:"HMAC", hash:"SHA-256"}, false, ["sign","verify"]);

      // إعدادات فعّالة من السيرفر (مصدر الحقيقة)
      cipherMode = ack.cipher;
      useEnc = ack.encryption !== false;
      integrity = ack.integrity !== false;
      if (ack.classical_key) classicalKey = ack.classical_key;

      // 5) التحقق من توقيع السيرفر (ECDSA P-256)
      let ok = false;
      if (ack.authenticated) {
        try {
          const sig = unhex(ack.sig);
          const transcript = concat(concat(myPub, serverPub), new Uint8Array([CIPHER_CODES[ack.cipher]]));
          const idKey = await crypto.subtle.importKey(
            "raw", unhex(ack.identity), {name:"ECDSA", namedCurve:"P-256"}, false, ["verify"]);
          ok = await crypto.subtle.verify({name:"ECDSA", hash:"SHA-256"}, idKey, sig, transcript);
        } catch (e) { console.warn("تعذّر التحقق:", e); }
      }
      document.getElementById("auth").textContent = ack.authenticated
        ? (ok ? "✅ موثّق" : "❌ توقيع غير صالح") : "بدون مصادقة";

      statusEl.textContent = "متصل";
      document.getElementById("text").disabled = false;
      document.getElementById("send").disabled = false;
      const desc = useEnc ? `تم تأمين القناة — ECDH + HKDF + ${cipherMode}` : "⚠️ التشفير مُطفأ في السيرفر — الرسائل بالنص الواضح";
      log(desc, "sys");
      return;
    }

    if (type === T_SYSTEM) {
      log(new TextDecoder().decode(payload), "sys");
      return;
    }

    if (type === T_MESSAGE) {
      try {
        let bytes = payload;
        if (useEnc) {
          if (cipherMode === "VIGENERE") {
            let body = payload;
            if (payload.length >= 32 && integrity) {
              const tag = payload.slice(-32), ct = payload.slice(0, -32);
              const expect = await hmacTag(ct);
              if (!equalBytes(tag, expect)) throw new Error("HMAC mismatch");
              body = ct;
            } else if (payload.length >= 32) {
              body = payload.slice(0, -32); // السلامة مطفأة: نتجاهل الـ tag
            }
            bytes = vigenereTransform(body, classicalKey, true);
          } else {
            const nonce = payload.slice(0,12), tag = payload.slice(-16), ct = payload.slice(12,-16);
            bytes = new Uint8Array(await crypto.subtle.decrypt(
              {name:"AES-GCM", iv:nonce, tagLength:128}, encKey, concat(ct, tag)));
          }
        }
        const m = JSON.parse(new TextDecoder().decode(bytes));
        log(`${m.name}: ${m.text}`, m.name === myName ? "me" : "other");
      } catch (e) { log("⚠️ فشل فك التشفير أو التحقق من السلامة", "sys"); }
    }
  };

  ws.onclose = () => { statusEl.textContent = "انقطع الاتصال"; };
}

async function send() {
  const el = document.getElementById("text");
  const text = el.value.trim();
  if (!text) return;
  el.value = "";

  const plain = new TextEncoder().encode(JSON.stringify({name: myName, text}));
  if (useEnc) {
    if (cipherMode === "VIGENERE") {
      // فيجينير (بايتات) ثم Encrypt-then-MAC: HMAC على النص المشفّر
      let body = vigenereTransform(plain, classicalKey, false);
      let flags = F_ENCRYPTED;
      if (integrity) { body = concat(body, await hmacTag(body)); flags |= F_MAC; }
      ws.send(frame(T_MESSAGE, body, flags));
    } else {
      const nonce = crypto.getRandomValues(new Uint8Array(12));
      const ctTag = new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM", iv:nonce}, encKey, plain));
      ws.send(frame(T_MESSAGE, concat(nonce, ctTag), F_ENCRYPTED | F_GCM));
    }
  } else {
    ws.send(frame(T_MESSAGE, plain, 0));
  }
  // لا نعرضها محلياً: السيرفر يعيد بثّها لكل المتصلين (بمن فيهم المرسل)،
  // فعرضها هنا أيضاً كان يجعلها تظهر مرتين.
}

document.getElementById("send").onclick = send;
document.getElementById("text").addEventListener("keydown", e => { if (e.key === "Enter") send(); });
start();
</script>
</body>
</html>"""
