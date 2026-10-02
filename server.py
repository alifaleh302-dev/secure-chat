"""
السيرفر الرئيسي — كل شيء على منفذ واحد.

يخدم ثلاث حالات على نفس المنفذ، ويميّزها من أول 4 بايتات:
    "GET " + Upgrade: websocket → دردشة المتصفح (مصافحة WebSocket يدوية)
    "GET " عادي                → لوحة التحكم / صفحات الويب (HTTP)
    "SCP1"                     → عميل بايثون (TCP خام)

هذا يجعل الاستضافة بسيطة: منفذ واحد فقط.

التشغيل:
    python server.py                 # منفذ 5000
    python server.py --port 8000
"""

import argparse
import socket
import threading

import config
import protocol
import webui
from hub import ChatHub
from transports import RawTransport, WSTransport
from websocket import WebSocket


def _read_http_request(sock: socket.socket) -> bytes:
    """قراءة ترويسات طلب HTTP حتى نهاية السطرين الفارغين."""
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(1024)
        if not chunk:
            raise ConnectionError("انتهى الطلب قبل اكتمال المصافحة")
        data += chunk
    return data


def _handle_http(conn: socket.socket, hub: ChatHub) -> None:
    request = _read_http_request(conn)
    text = request.decode("latin-1")
    first_line = text.split("\r\n", 1)[0]
    parts = first_line.split(" ")
    method = parts[0] if parts else "GET"
    path = parts[1] if len(parts) > 1 else "/"

    if "upgrade: websocket" in text.lower():
        # دردشة المتصفح: نكمل مصافحة WebSocket يدوياً
        ws = WebSocket(conn)
        ws.handshake(request)
        client = hub.register(WSTransport(ws), "browser")
        print(f"[+] {client.name} (browser) — تشفير: {client.cipher}")
        hub.serve(client)
        print(f"[-] {client.name} انقطع")
        return

    # طلب HTTP عادي: صفحات الويب وواجهات API
    content_length = 0
    headers: dict[str, str] = {}
    head_text, _, rest = text.partition("\r\n\r\n")
    for line in head_text.split("\r\n")[1:]:
        name, sep, value = line.partition(":")
        if sep:
            headers[name.strip().lower()] = value.strip()
    if "content-length" in headers:
        content_length = int(headers["content-length"])
    body = b""
    if content_length:
        body = rest.encode("latin-1")
        while len(body) < content_length:
            body += conn.recv(content_length - len(body))

    status, ctype, payload, extra = webui.route(method, path, body, hub, headers)
    reason = {200: "OK", 302: "Found", 400: "Bad Request", 401: "Unauthorized",
              404: "Not Found"}.get(status, "OK")
    response = (
        f"HTTP/1.1 {status} {reason}\r\n"
        f"Content-Type: {ctype}\r\n"
        f"Content-Length: {len(payload)}\r\n"
    )
    for name, value in extra.items():
        response += f"{name}: {value}\r\n"
    response += "Connection: close\r\n\r\n"
    conn.sendall(response.encode() + payload)
    conn.close()


def _handle_connection(conn: socket.socket, hub: ChatHub) -> None:
    try:
        head = conn.recv(4, socket.MSG_PEEK)

        # إطارنا الثنائي يبدأ بـ "SCP1" → عميل بايثون. أي شيء آخر = HTTP.
        if not head.startswith(protocol.MAGIC):
            _handle_http(conn, hub)
            return

        # عميل بايثون: TCP خام
        client = hub.register(RawTransport(conn), "python")
        print(f"[+] {client.name} (python) — تشفير: {client.cipher}")
        hub.serve(client)
        print(f"[-] {client.name} انقطع")

    except Exception as exc:
        print(f"[!] خطأ في الاتصال: {exc}")
        try:
            conn.close()
        except Exception:
            pass


def run_chat_server(hub: ChatHub) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((config.HOST, config.PORT))
    srv.listen(32)
    print(f"[*] السيرفر يعمل على المنفذ {config.PORT}")
    print(f"    - لوحة التحكم : http://localhost:{config.PORT}/settings")
    print(f"    - دردشة المتصفح: http://localhost:{config.PORT}/chat")
    print(f"    - عميل بايثون : python client.py")
    while True:
        conn, addr = srv.accept()
        threading.Thread(
            target=_handle_connection, args=(conn, hub), daemon=True
        ).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="سيرفر الدردشة الآمن (تعليمي)")
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--host", default=config.HOST)
    args = parser.parse_args()

    config.PORT = args.port
    config.HOST = args.host

    print(config.describe())
    if config.ADMIN_PASSWORD_GENERATED:
        print("[!] لم يُضبط ADMIN_PASSWORD → وُلّدت كلمة مرور عشوائية لهذه الجلسة.")
        print(f"[*] كلمة مرور لوحة التحكم (مؤقتة): {config.ADMIN_PASSWORD}")
        print("    اضبط ADMIN_PASSWORD في متغيرات البيئة لتثبيتها.")
    else:
        print(f"[*] كلمة مرور اللوحة: مقروءة من متغير البيئة ADMIN_PASSWORD "
              f"(المستخدم: {config.ADMIN_USER}، الطول: {len(config.ADMIN_PASSWORD)} حرفاً)")

    hub = ChatHub()
    try:
        run_chat_server(hub)
    except KeyboardInterrupt:
        print("\n[*] إيقاف السيرفر...")
        hub.disconnect_all()


if __name__ == "__main__":
    main()
