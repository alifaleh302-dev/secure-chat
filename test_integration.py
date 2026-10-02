"""اختبار تكاملي مؤقت: عميلان بايثون يتبادلان رسائل + عميل WebSocket."""
import json
import socket
import struct
import time

import config
import protocol
from crypto import auth, kdf, key_exchange
from transports import RawTransport


def make_client(name):
    sock = socket.create_connection((config.HOST, config.PORT))
    t = RawTransport(sock)
    priv, pub = key_exchange.generate_keypair_p256()
    hello = {"pubkey": pub.hex(), "mode": "python", "name": name}
    t.send_frame(protocol.pack_frame(protocol.T_HELLO, json.dumps(hello).encode()))
    frame = t.recv_frame()
    _, _, payload = protocol.unpack_frame(frame)
    ack = json.loads(payload.decode())
    server_pub = bytes.fromhex(ack["pubkey"])
    cipher = ack["cipher"]
    # verify signature
    transcript = pub + server_pub + bytes([protocol.CIPHER_CODES[cipher]])
    ok = auth.verify(bytes.fromhex(ack["identity"]), bytes.fromhex(ack["sig"]), transcript)
    shared = key_exchange.compute_shared_p256(priv, server_pub)
    import hashlib
    salt = hashlib.sha256(pub + server_pub).digest()
    keys = kdf.derive_keys(shared, salt)
    return sock, t, keys, cipher, ok


def drain(t, keys, cipher, label):
    t.sock.settimeout(1.0)
    try:
        while True:
            frame = t.recv_frame()
            ftype, flags, payload = protocol.unpack_frame(frame)
            if ftype == protocol.T_SYSTEM:
                print(f"  [{label}] SYSTEM: {payload.decode()}")
            elif ftype == protocol.T_MESSAGE:
                pt = protocol.decrypt_message(keys, cipher, True, payload, flags)
                m = json.loads(pt.decode())
                print(f"  [{label}] MESSAGE from {m['name']}: {m['text']}")
    except (socket.timeout, TimeoutError):
        pass


print("=== Test 1: client A connects ===")
sockA, tA, keysA, cipherA, okA = make_client("A")
print(f"  cipher={cipherA}, server signature verified={okA}")
time.sleep(0.3)

print("=== Test 2: client B connects ===")
sockB, tB, keysB, cipherB, okB = make_client("B")
print(f"  cipher={cipherB}, server signature verified={okB}")
time.sleep(0.3)

keys_global, cipher_global = keysA, cipherA

print("=== Test 3: A sends message, B receives ===")
plain = json.dumps({"name": "A", "text": "hello from A"}, ensure_ascii=False).encode()
payload, flags = protocol.encrypt_message(keysA, cipherA, True, plain)
tA.send_frame(protocol.pack_frame(protocol.T_MESSAGE, payload, flags))
time.sleep(0.3)
drain(tB, keysB, cipherB, "B")

print("=== Test 4: tampered message is rejected ===")
plain = json.dumps({"name": "A", "text": "original"}, ensure_ascii=False).encode()
payload, flags = protocol.encrypt_message(keysA, cipherA, True, plain)
bad = bytearray(payload)
bad[0] ^= 0xFF  # tamper
tA.send_frame(protocol.pack_frame(protocol.T_MESSAGE, bytes(bad), flags))
time.sleep(0.3)
drain(tA, keysA, cipherA, "A")

sockA.close()
sockB.close()
print("=== ALL TESTS DONE ===")
