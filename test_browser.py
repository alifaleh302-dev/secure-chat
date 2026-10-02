"""اختبار مسار المتصفح: مصافحة WebSocket يدوية + ECDH P-256 + AES-GCM."""
import base64
import hashlib
import json
import os
import socket

import config
import protocol
from crypto import auth, kdf, key_exchange
from transports import WSTransport
from websocket import WebSocket

# 1) اتصال TCP خام + مصافحة WebSocket يدوية
sock = socket.create_connection((config.HOST, config.PORT))
ws_key = base64.b64encode(os.urandom(16)).decode()
req = (
    "GET / HTTP/1.1\r\n"
    f"Host: {config.HOST}:{config.PORT}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {ws_key}\r\n"
    "Sec-WebSocket-Version: 13\r\n\r\n"
)
sock.sendall(req.encode())

resp = sock.recv(1024).decode()
assert "101 Switching Protocols" in resp, f"فشلت المصافحة:\n{resp}"
expected = base64.b64encode(hashlib.sha1((ws_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
assert expected in resp, "Sec-WebSocket-Accept غير مطابق!"
print("✅ مصافحة WebSocket اليدوية نجحت (101 + Accept صحيح)")

ws = WebSocket(sock)
t = WSTransport(ws)

# 2) HELLO
priv, pub = key_exchange.generate_keypair_p256()
hello = {"pubkey": pub.hex(), "mode": "browser", "name": "browser-sim"}
t.send_frame(protocol.pack_frame(protocol.T_HELLO, json.dumps(hello).encode()))

frame = t.recv_frame()
_, _, payload = protocol.unpack_frame(frame)
ack = json.loads(payload.decode())
server_pub = bytes.fromhex(ack["pubkey"])
print(f"✅ استقبلنا HELLO_ACK: cipher={ack['cipher']}, authenticated={ack['authenticated']}")

# 3) التحقق من التوقيع + ECDH + HKDF
transcript = pub + server_pub + bytes([protocol.CIPHER_CODES[ack["cipher"]]])
ok = auth.verify(bytes.fromhex(ack["identity"]), bytes.fromhex(ack["sig"]), transcript)
print(f"✅ التحقق من توقيع السيرفر: {ok}")
assert ok

shared = key_exchange.compute_shared_p256(priv, server_pub)
salt = hashlib.sha256(pub + server_pub).digest()
keys = kdf.derive_keys(shared, salt)
print(f"✅ اشتقاق المفاتيح: enc={len(keys['enc'])}B, mac={len(keys['mac'])}B")

# 4) إرسال رسالة مشفّرة AES-GCM عبر WebSocket
pt = json.dumps({"name": "browser-sim", "text": "مرحبا من المتصفح"}, ensure_ascii=False).encode()
payload, flags = protocol.encrypt_message(keys, ack["cipher"], True, pt)
t.send_frame(protocol.pack_frame(protocol.T_MESSAGE, payload, flags))
print("✅ أُرسلت رسالة AES-GCM عبر WebSocket")

# 5) نقرأ ردود النظام (انضم/...)
sock.settimeout(1.0)
try:
    for _ in range(3):
        f = t.recv_frame()
        ft, fl, pl = protocol.unpack_frame(f)
        if ft == protocol.T_SYSTEM:
            print(f"   SYSTEM: {pl.decode()}")
except (socket.timeout, TimeoutError):
    pass

ws.close()
print("=== اختبار المتصفح ناجح ===")
