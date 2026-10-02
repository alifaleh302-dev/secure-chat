"""صفحات HTML لواجهة التحكم ودردشة المتصفح (قوالب نصية)."""

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
  <a class="btn" href="/chat">فتح الدردشة →</a>
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
        <option>AES-CTR</option><option>AES-GCM</option>
      </select></div>

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
const KEYS = ["ENCRYPTION","CIPHER","INTEGRITY","MAC_MODE","AUTHENTICATION","KEY_EXCHANGE"];
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
const F_ENCRYPTED=1, F_GCM=4;
const CIPHER_CODES = {NONE:0, RC4:1, "AES-ECB":2, "AES-CBC":3, "AES-CTR":4, "AES-GCM":5};

let ws, encKey, myName, useEnc = true;
const logEl = document.getElementById("log");
const statusEl = document.getElementById("status");

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

      // 4) HKDF: نشتقّ مفتاح التشفير (والسلامة ضمن GCM)
      const base = await crypto.subtle.importKey("raw", shared, "HKDF", false, ["deriveBits"]);
      encKey = await crypto.subtle.importKey(
        "raw", await crypto.subtle.deriveBits(
          {name:"HKDF", hash:"SHA-256", salt, info: new TextEncoder().encode("encryption")}, base, 256),
        {name:"AES-GCM"}, false, ["encrypt","decrypt"]);

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
      log(useEnc ? "تم تأمين القناة — ECDH + HKDF + AES-GCM"
                 : "⚠️ التشفير مُطفأ في السيرفر — الرسائل بالنص الواضح", "sys");
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
          const nonce = payload.slice(0,12), tag = payload.slice(-16), ct = payload.slice(12,-16);
          bytes = new Uint8Array(await crypto.subtle.decrypt(
            {name:"AES-GCM", iv:nonce, tagLength:128}, encKey, concat(ct, tag)));
        }
        const m = JSON.parse(new TextDecoder().decode(bytes));
        log(`${m.name}: ${m.text}`, m.name === myName ? "me" : "other");
      } catch (e) { log("⚠️ فشل فك التشفير", "sys"); }
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
    const nonce = crypto.getRandomValues(new Uint8Array(12));
    const ctTag = new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM", iv:nonce}, encKey, plain));
    ws.send(frame(T_MESSAGE, concat(nonce, ctTag), F_ENCRYPTED | F_GCM));
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
