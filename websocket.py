"""
WebSocket يدوي (RFC 6455) — مكتوب من الصفر.

المتصفح لا يستطيع فتح TCP خام، لكنه يستطيع فتح WebSocket. و WebSocket
يبدأ بـ "مصافحة" هي رسالة HTTP عادية، ثم "ترقية" الاتصال. نكتبها هنا
بأنفسنا فوق socket — لا مكتبات جاهزة.

المصافحة:
    1) المتصفح يرسل HTTP GET مع ترويسة Sec-WebSocket-Key.
    2) السيرفر يرد 101 Switching Protocols مع Accept = base64(sha1(key+GUID)).
    3) بعدها يتحوّل الاتصال إلى إطارات ثنائية ثنائية الاتجاه.

الإطارات:
    إطار العميل (من المتصفح) دائماً مُقنّع (masked) — إلزامي حسب RFC.
    إطار السيرفر غير مُقنّع.
"""

import base64
import hashlib
import os
import struct

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_CONT = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA


def accept_key(key: str) -> str:
    """حساب Sec-WebSocket-Accept حسب RFC 6455."""
    digest = hashlib.sha1((key + GUID).encode()).digest()
    return base64.b64encode(digest).decode()


def recv_exact(sock, n: int) -> bytes:
    """قراءة n بايت بالضبط (TCP قد يجزّئ القراءة)."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("انقطع الاتصال أثناء القراءة")
        buf += chunk
    return buf


class WebSocket:
    """يغلّف socket مفتوحاً بعد إتمام المصافحة."""

    def __init__(self, sock):
        self.sock = sock

    # ---------- المصافحة ----------
    def handshake(self, request: bytes) -> None:
        headers = {}
        for line in request.decode("latin-1").split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        key = headers.get("sec-websocket-key")
        if not key:
            raise ValueError("طلب WebSocket بلا Sec-WebSocket-Key")

        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key(key)}\r\n"
            "\r\n"
        )
        self.sock.sendall(response.encode())

    # ---------- الإطارات ----------
    def send(self, opcode: int, payload: bytes = b"") -> None:
        """إرسال إطار غير مُقنّع (السيرفر لا يُقنّع)."""
        header = bytearray([0x80 | opcode])  # FIN + opcode
        n = len(payload)
        if n < 126:
            header.append(n)
        elif n < 65536:
            header.append(126)
            header += struct.pack(">H", n)
        else:
            header.append(127)
            header += struct.pack(">Q", n)
        self.sock.sendall(bytes(header) + payload)

    def send_binary(self, data: bytes) -> None:
        self.send(OP_BINARY, data)

    def send_text(self, text: str) -> None:
        self.send(OP_TEXT, text.encode("utf-8"))

    def recv(self) -> tuple[int, bytes]:
        """قراءة إطار واحد وفكّ التقسيم (fragmentation)."""
        opcode = None
        payload = b""

        while True:
            b1, b2 = recv_exact(self.sock, 2)
            fin = b1 & 0x80
            op = b1 & 0x0F
            masked = b2 & 0x80
            length = b2 & 0x7F

            if length == 126:
                length = struct.unpack(">H", recv_exact(self.sock, 2))[0]
            elif length == 127:
                length = struct.unpack(">Q", recv_exact(self.sock, 8))[0]

            mask = recv_exact(self.sock, 4) if masked else None
            data = recv_exact(self.sock, length) if length else b""

            if mask:
                data = bytes(c ^ mask[i % 4] for i, c in enumerate(data))

            if op == OP_CLOSE:
                return OP_CLOSE, b""
            if op == OP_PING:
                self.send(OP_PONG, data)
                continue
            if op == OP_PONG:
                continue

            if op != OP_CONT:
                opcode = op
            payload += data
            if fin:
                return opcode, payload

    def recv_binary(self) -> bytes:
        op, data = self.recv()
        if op == OP_CLOSE:
            raise ConnectionError("أغلق المتصفح الاتصال")
        return data

    def close(self) -> None:
        try:
            self.send(OP_CLOSE)
        except Exception:
            pass
