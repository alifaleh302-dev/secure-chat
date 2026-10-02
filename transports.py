"""
طبقة النقل — تجريد موحّد فوق TCP الخام و WebSocket.

السيرفر يخدم نوعين من العملاء:
    - عميل بايثون  → TCP خام (RawTransport)
    - عميل متصفح   → WebSocket يدوي (WSTransport)

كلاهما يتبادل نفس "الإطارات" من protocol.py، لذا منطق الدردشة لا يفرّق بينهما.
"""

import protocol


class RawTransport:
    """نقل فوق TCP خام — يُستخدمه عميل بايثون."""

    def __init__(self, sock):
        self.sock = sock

    def _recv_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("انقطع اتصال TCP")
            buf += chunk
        return buf

    def recv_frame(self) -> bytes:
        header = self._recv_exact(protocol.HEADER.size)
        length = protocol.HEADER.unpack(header)[-1]
        payload = self._recv_exact(length) if length else b""
        return header + payload

    def send_frame(self, data: bytes) -> None:
        self.sock.sendall(data)

    def close(self) -> None:
        try:
            self.sock.close()
        except Exception:
            pass


class WSTransport:
    """نقل فوق WebSocket يدوي — يُستخدمه المتصفح."""

    def __init__(self, ws):
        self.ws = ws

    def recv_frame(self) -> bytes:
        return self.ws.recv_binary()

    def send_frame(self, data: bytes) -> None:
        self.ws.send_binary(data)

    def close(self) -> None:
        self.ws.close()
