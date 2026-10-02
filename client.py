"""
عميل بايثون — TCP خام + طرفية.

هذا العميل هو مختبرك التعليمي: يستخدم أوضاع التشفير كاملة (RC4, ECB, CBC,
CTR, GCM) مع HMAC المكتوب من الصفر — كل شيء تراه في Wireshark.

التشغيل:
    python client.py --name ali
    python client.py --name ali --cipher AES-ECB     # لتجربة كشف الأنماط
    ENCRYPTION=0 python client.py                    # نص واضح تماماً
"""

import argparse
import json
import socket
import threading

import config
import protocol
from crypto import auth, kdf, key_exchange
from transports import RawTransport


class ChatClient:
    def __init__(self, host, port, name, mode="python"):
        self.host, self.port, self.name, self.mode = host, port, name, mode
        self.sock = None
        self.transport = None
        self.keys = {}
        self.cipher = config.CIPHER
        self.encryption = config.ENCRYPTION
        self.integrity = config.INTEGRITY

    # ---------- المصافحة ----------
    def connect(self):
        self.sock = socket.create_connection((self.host, self.port))
        self.transport = RawTransport(self.sock)

        # 1) توليد مفتاح مؤقّت وإرسال HELLO
        priv, pub = key_exchange.generate_keypair_p256()
        hello = {"pubkey": pub.hex(), "mode": self.mode, "name": self.name}
        self.transport.send_frame(
            protocol.pack_frame(protocol.T_HELLO, json.dumps(hello).encode())
        )

        # 2) استقبال HELLO_ACK والتحقق من توقيع السيرفر
        frame = self.transport.recv_frame()
        _ftype, _flags, payload = protocol.unpack_frame(frame)
        ack = json.loads(payload.decode())

        server_pub = bytes.fromhex(ack["pubkey"])
        self.cipher = ack["cipher"]
        # السيرفر هو مصدر الحقيقة: يخبر العميل بالإعدادات الفعّالة
        self.encryption = ack.get("encryption", True)
        self.integrity = ack.get("integrity", True)
        # الشيفرات الكلاسيكية: نأخذ المفتاح البشري من السيرفر
        if ack.get("classical_key"):
            config.CLASSICAL_KEY = ack["classical_key"]
        # نُحدّث الإعداد المحلي ليعكس ما تفاوضنا عليه فعلاً (للعرض الصحيح)
        config.CIPHER = self.cipher
        config.INTEGRITY = self.integrity

        if ack["authenticated"]:
            pinned = auth.load_pinned_public()
            identity = bytes.fromhex(ack["identity"])
            if pinned and pinned != identity:
                raise SystemExit("[!] تحذير: هوية السيرفر لا تطابق المثبّتة — إيقاف (MITM؟)")
            transcript = pub + server_pub + bytes([protocol.CIPHER_CODES[self.cipher]])
            ok = auth.verify(identity, bytes.fromhex(ack["sig"]), transcript)
            print(f"[*] التحقق من توقيع السيرفر: {'✅ نجح' if ok else '❌ فشل!'}")
            if not ok and config.AUTHENTICATION:
                raise SystemExit("[!] توقيع السيرفر غير صالح — إيقاف")
        else:
            print("[*] المصادقة مطفأة — لا نتحقق من هوية السيرفر")

        # 3) اشتقاق المفاتيح
        if config.KEY_EXCHANGE == "HARDCODED":
            shared, salt = config.HARDCODED_SECRET, __import__("hashlib").sha256(b"hardcoded-salt").digest()
        else:
            shared = key_exchange.compute_shared_p256(priv, server_pub)
            import hashlib
            salt = hashlib.sha256(pub + server_pub).digest()
        self.keys = kdf.derive_keys(shared, salt)

        print(config.describe())
        print(f"[*] متصل بـ {self.host}:{self.port} كـ «{self.name}»")

    # ---------- الاستقبال ----------
    def receive_loop(self):
        try:
            while True:
                frame = self.transport.recv_frame()
                ftype, flags, payload = protocol.unpack_frame(frame)

                if ftype == protocol.T_SYSTEM:
                    print(f"\r{payload.decode('utf-8')}")

                elif ftype == protocol.T_MESSAGE:
                    try:
                        plain = protocol.decrypt_message(
                            self.keys, self.cipher, self.integrity, payload, flags
                        )
                    except ValueError as exc:
                        print(f"\r[!] {exc}")
                        continue
                    msg = json.loads(plain.decode())
                    print(f"\r[{msg['name']}] {msg['text']}")

                elif ftype == protocol.T_BYE:
                    break

        except (ConnectionError, OSError):
            pass
        print("\r[*] انتهى الاتصال")

    # ---------- الإرسال ----------
    def send(self, text: str):
        plain = json.dumps({"name": self.name, "text": text}, ensure_ascii=False).encode()
        if self.encryption and self.cipher != "NONE":
            payload, flags = protocol.encrypt_message(
                self.keys, self.cipher, self.integrity, plain
            )
        else:
            payload, flags = plain, 0
        self.transport.send_frame(protocol.pack_frame(protocol.T_MESSAGE, payload, flags))

    def run(self):
        self.connect()
        threading.Thread(target=self.receive_loop, daemon=True).start()
        print("[*] اكتب رسالتك (أو 'exit' للخروج):")
        try:
            while True:
                line = input()
                if line.strip().lower() in ("exit", "quit", "خروج"):
                    break
                if line:
                    self.send(line)
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            try:
                self.transport.send_frame(protocol.pack_frame(protocol.T_BYE))
            except Exception:
                pass
            self.transport.close()


def main():
    parser = argparse.ArgumentParser(description="عميل الدردشة الآمن (تعليمي)")
    parser.add_argument("--host", default=config.HOST if config.HOST != "0.0.0.0" else "127.0.0.1")
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--name", default="python-user")
    args = parser.parse_args()

    ChatClient(args.host, args.port, args.name).run()


if __name__ == "__main__":
    main()
