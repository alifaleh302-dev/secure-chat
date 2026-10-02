"""
مركز الدردشة (Chat Hub) — قلب السيرفر.

مسؤول عن:
    1) المصافحة (Handshake): تبادل ECDH + توقيع السيرفر + اشتقاق المفاتيح.
    2) إدارة العملاء المتصلين.
    3) إعادة بث الرسائل (broadcast) — كل رسالة تُشفّر لكل عميل بمفتاحه.

نقطة تعليمية مهمة: كل عميل له مفتاحه الخاص (لأن كل جلسة ECDH مستقلة)،
لذا يعيد السيرفر تشفير الرسالة لكل مستلم على حدة. هذا ما يحدث فعلاً في
بروتوكولات الدردشة الآمنة (مثل Signal).
"""

import hashlib
import json
import threading

import config
import protocol
from crypto import auth, kdf, key_exchange


class Client:
    def __init__(self, cid, transport, name, mode, cipher, keys):
        self.id = cid
        self.transport = transport
        self.name = name
        self.mode = mode
        self.cipher = cipher
        self.keys = keys

    def send_frame(self, ftype, payload=b"", flags=0):
        self.transport.send_frame(protocol.pack_frame(ftype, payload, flags))

    def send_system(self, text: str):
        # إشعارات النظام تُرسل غير مشفّرة — لكي تراها بوضوح في Wireshark
        self.send_frame(protocol.T_SYSTEM, text.encode("utf-8"))

    def send_chat(self, sender: str, text: str):
        plaintext = json.dumps({"name": sender, "text": text}, ensure_ascii=False).encode()
        if config.ENCRYPTION and self.cipher != "NONE":
            payload, flags = protocol.encrypt_message(
                self.keys, self.cipher, config.INTEGRITY, plaintext
            )
        else:
            payload, flags = plaintext, 0
        self.send_frame(protocol.T_MESSAGE, payload, flags)


class ChatHub:
    def __init__(self):
        self._clients: list[Client] = []
        self._lock = threading.Lock()
        self._counter = 0
        self.identity_key = auth.load_or_create_server_key()

    # ---------- الاستعلام ----------
    @property
    def clients(self) -> list[Client]:
        with self._lock:
            return list(self._clients)

    def snapshot(self) -> list[dict]:
        return [
            {"id": c.id, "name": c.name, "mode": c.mode, "cipher": c.cipher}
            for c in self.clients
        ]

    # ---------- المصافحة ----------
    def register(self, transport, mode: str) -> Client:
        frame = transport.recv_frame()
        ftype, _flags, payload = protocol.unpack_frame(frame)
        if ftype != protocol.T_HELLO:
            raise ValueError("متوقع إطار HELLO")

        hello = json.loads(payload.decode("utf-8"))
        client_pub = bytes.fromhex(hello["pubkey"])
        mode = hello.get("mode", mode)
        name = hello.get("name") or f"user-{self._counter + 1}"

        # اختيار الخوارزمية: إعدادات السيرفر تحكم. المتصفح (Web Crypto) يدعم
        # AES-GCM، وفيجينير مكتوبة بجافاسكربت. أي وضع آخر لا يتوفّر في المتصفح
        # (RC4/ECB/CBC/CTR) → نرجع إلى AES-GCM.
        BROWSER_CIPHERS = {"AES-GCM", "VIGENERE"}
        cipher = config.CIPHER
        if mode == "browser" and cipher not in BROWSER_CIPHERS:
            cipher = "AES-GCM"

        # --- تبادل المفاتيح ---
        if config.KEY_EXCHANGE == "HARDCODED":
            server_pub = b""
            shared = config.HARDCODED_SECRET
            salt = hashlib.sha256(b"hardcoded-salt").digest()
        else:
            server_priv, server_pub = key_exchange.generate_keypair_p256()
            shared = key_exchange.compute_shared_p256(server_priv, client_pub)
            salt = hashlib.sha256(client_pub + server_pub).digest()

        # --- المصادقة: نوقّع النسخة (transcript) بمفتاح السيرفر ---
        transcript = client_pub + server_pub + bytes([protocol.CIPHER_CODES[cipher]])
        signature = auth.sign(self.identity_key, transcript) if config.AUTHENTICATION else b""

        ack = {
            "pubkey": server_pub.hex(),
            "sig": signature.hex(),
            "cipher": cipher,
            "identity": auth.public_bytes(self.identity_key).hex(),
            "authenticated": config.AUTHENTICATION,
            "encryption": config.ENCRYPTION,
            "integrity": config.INTEGRITY,
        }
        # الشيفرات الكلاسيكية: نُبلّغ المفتاح البشري ليستخدمه العميل/المتصفح.
        # (يظهر في Wireshark — وهذا مقصود تعليمياً، لا سرّياً.)
        if cipher == "VIGENERE":
            ack["classical_key"] = config.CLASSICAL_KEY
        transport.send_frame(
            protocol.pack_frame(protocol.T_HELLO_ACK, json.dumps(ack).encode())
        )

        keys = kdf.derive_keys(shared, salt)

        with self._lock:
            self._counter += 1
            cid = self._counter
        client = Client(cid, transport, name, mode, cipher, keys)
        with self._lock:
            self._clients.append(client)

        self.broadcast_system(f"* {name} انضم إلى الدردشة")
        return client

    # ---------- حلقة الخدمة ----------
    def serve(self, client: Client) -> None:
        try:
            while True:
                frame = client.transport.recv_frame()
                ftype, flags, payload = protocol.unpack_frame(frame)

                if ftype == protocol.T_MESSAGE:
                    try:
                        plaintext = protocol.decrypt_message(
                            client.keys, client.cipher, config.INTEGRITY, payload, flags
                        )
                    except ValueError as exc:
                        client.send_system(f"[!] رُفضت رسالة: {exc}")
                        continue

                    try:
                        data = json.loads(plaintext.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        # حدث ذلك لأن السلامة مطفأة: العبث مرّ دون كشف فأنتج بيانات تالفة
                        msg = ("[!] وصلت بيانات معدّلة/تالفة ولم يُكتشف العبث "
                               "(السلامة INTEGRITY مطفأة)")
                        print(f"[!] {client.name}: {msg}")
                        client.send_system(msg)
                        continue

                    preview = payload[:24].hex()
                    print(f"[msg] {client.name} ({client.cipher}, flags={flags:#05b}) "
                          f"→ «{data.get('text','')}»  | أول بايتات على الشبكة: {preview}…")
                    self.relay(client, data.get("text", ""))

                elif ftype == protocol.T_BYE:
                    break

        except (ConnectionError, OSError):
            pass
        finally:
            self.remove(client)

    def relay(self, sender: Client, text: str) -> None:
        for c in self.clients:
            try:
                c.send_chat(sender.name, text)
            except Exception:
                pass

    def broadcast_system(self, text: str) -> None:
        for c in self.clients:
            try:
                c.send_system(text)
            except Exception:
                pass

    def remove(self, client: Client) -> None:
        with self._lock:
            if client in self._clients:
                self._clients.remove(client)
            else:
                return
        client.transport.close()
        self.broadcast_system(f"* {client.name} خرج من الدردشة")

    def disconnect_all(self) -> None:
        for c in self.clients:
            try:
                c.send_frame(protocol.T_BYE)
                c.transport.close()
            except Exception:
                pass
        with self._lock:
            self._clients.clear()
