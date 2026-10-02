"""اختبار طرف-لطرف عبر الرابط العام (نفق Cloudflare): TLS + WebSocket + SCP1."""
import base64
import hashlib
import json
import os
import socket
import ssl
import sys

import protocol
from crypto import auth, kdf, key_exchange
from transports import WSTransport
from websocket import WebSocket

host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 443
tls = port == 443

if tls:
    raw = socket.create_connection((host, port), timeout=20)
    sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
else:
    sock = socket.create_connection((host, port), timeout=20)

ws_key = base64.b64encode(os.urandom(16)).decode()
sock.sendall((
    "GET / HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {ws_key}\r\n"
    "Sec-WebSocket-Version: 13\r\n\r\n"
).encode())

resp = sock.recv(4096).decode()
if "101 Switching Protocols" not in resp:
    print("❌ فشلت مصافحة WebSocket:")
    print(resp[:400])
    sys.exit(1)
expected = base64.b64encode(
    hashlib.sha1((ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
).decode()
assert expected in resp, "Sec-WebSocket-Accept غير مطابق!"
print("✅ 1) مصافحة WebSocket نجحت (101 + Accept صحيح)")

ws = WebSocket(sock)
t = WSTransport(ws)

priv, pub = key_exchange.generate_keypair_p256()
hello = {"pubkey": pub.hex(), "mode": "browser", "name": "tunnel-test"}
t.send_frame(protocol.pack_frame(protocol.T_HELLO, json.dumps(hello).encode()))

frame = t.recv_frame()
_ft, _fl, payload = protocol.unpack_frame(frame)
ack = json.loads(payload.decode())
print(f"✅ 2) HELLO_ACK: cipher={ack['cipher']}, encryption={ack.get('encryption')}, "
      f"authenticated={ack['authenticated']}")

server_pub = bytes.fromhex(ack["pubkey"])
if ack["authenticated"]:
    transcript = pub + server_pub + bytes([protocol.CIPHER_CODES[ack["cipher"]]])
    ok = auth.verify(bytes.fromhex(ack["identity"]), bytes.fromhex(ack["sig"]), transcript)
    print(f"✅ 3) التحقق من توقيع السيرفر: {ok}")
    assert ok, "توقيع السيرفر غير صالح!"

shared = key_exchange.compute_shared_p256(priv, server_pub)
salt = hashlib.sha256(pub + server_pub).digest()
keys = kdf.derive_keys(shared, salt)

plain = json.dumps({"name": "tunnel-test", "text": "مرحبا عبر النفق"},
                   ensure_ascii=False).encode()
pl, flags = protocol.encrypt_message(keys, ack["cipher"], ack.get("integrity", True), plain)
t.send_frame(protocol.pack_frame(protocol.T_MESSAGE, pl, flags))
print(f"✅ 4) أُرسلت رسالة {ack['cipher']} عبر الرابط العام")

# نستقبل رد السيرفر (بثّ للمرسل نفسه)
sock.settimeout(10)
try:
    for _ in range(6):
        fr = t.recv_frame()
        ft, fl, pl2 = protocol.unpack_frame(fr)
        if ft == protocol.T_SYSTEM:
            print("   SYSTEM:", pl2.decode())
        elif ft == protocol.T_MESSAGE:
            pt = protocol.decrypt_message(keys, ack["cipher"], ack.get("integrity", True), pl2, fl)
            m = json.loads(pt.decode())
            print(f"✅ 5) استُقبلت رسالة مشفّرة من {m['name']}: {m['text']}")
            break
except (socket.timeout, TimeoutError):
    print("❌ لم تصل رسالة من السيرفر خلال المهلة")
    sys.exit(1)

print("=== النشر يعمل طرفاً لطرف عبر الرابط العام ===")
