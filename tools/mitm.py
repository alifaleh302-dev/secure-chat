"""
أداة رجل-في-المنتصف (MITM) — تعليمية.

تجلس بين العميل والسيرفر وتمرّر البيانات، ويمكنها "العبث" ببايتات
رسالة العميل لتُظهر لك عملياً كيف تعمل السلامة (Integrity).

السيناريو التعليمي:
    1) شغّل السيرفر، ثم هذه الأداة، ثم العميل موجّهاً إلى منفذ الأداة.
    2) مع INTEGRITY=ON  → الرسالة المعدّلة تُرفض (HMAC يكشفها).
    3) مع INTEGRITY=OFF → الرسالة المعدّلة تمرّ (لأن لا شيء يتحقق).

التشغيل:
    python tools/mitm.py --listen 6000 --target 5000 --tamper
    python client.py --port 6000 --name victim
"""

import argparse
import os
import socket
import sys
import threading

# نسمح للأداة باستيراد وحدات المشروع من المجلد الأب
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import protocol


def pipe(src: socket.socket, dst: socket.socket, tamper: bool, label: str) -> None:
    """ينقل البايتات من src إلى dst، مع إمكانية العبث بأول رسالة دردشة."""
    buffer = bytearray()
    tamped = False
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            buffer += data

            if tamper and not tamped and label == "client→server":
                # ننتظر إطاراً كاملاً من نوع T_MESSAGE ثم نقلب بايتاً في حمولته
                while len(buffer) >= protocol.HEADER.size:
                    if not bytes(buffer[:4]) == protocol.MAGIC:
                        buffer.pop(0)
                        continue
                    length = protocol.HEADER.unpack(bytes(buffer[:protocol.HEADER.size]))[-1]
                    total = protocol.HEADER.size + length
                    if len(buffer) < total:
                        break
                    ftype = buffer[5]
                    if ftype == protocol.T_MESSAGE:
                        pos = protocol.HEADER.size
                        original = buffer[pos]
                        buffer[pos] ^= 0x01
                        tamped = True
                        print(f"[MITM] 🕵️  عبثنا ببايت في الرسالة: {original:#04x} → {buffer[pos]:#04x}")
                    break

            print(f"[MITM] {label}: {len(buffer)} بايت")
            dst.sendall(bytes(buffer))
            buffer.clear()
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(client: socket.socket, target_host: str, target_port: int, tamper: bool) -> None:
    server = socket.create_connection((target_host, target_port))
    threading.Thread(target=pipe, args=(client, server, tamper, "client→server"), daemon=True).start()
    pipe(server, client, False, "server→client")


def main() -> None:
    parser = argparse.ArgumentParser(description="أداة MITM تعليمية")
    parser.add_argument("--listen", type=int, default=6000)
    parser.add_argument("--target-host", default="127.0.0.1")
    parser.add_argument("--target", type=int, default=5000)
    parser.add_argument("--tamper", action="store_true", help="العبث بأول رسالة")
    args = parser.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", args.listen))
    srv.listen(8)
    print(f"[MITM] يستمع على {args.listen} ويحوّل إلى {args.target_host}:{args.target}")
    print(f"[MITM] العبث: {'مُفعّل 🕵️' if args.tamper else 'معطّل'}")
    print(f"[MITM] وجّه العميل: python client.py --port {args.listen}")
    while True:
        conn, _ = srv.accept()
        threading.Thread(
            target=handle, args=(conn, args.target_host, args.target, args.tamper), daemon=True
        ).start()


if __name__ == "__main__":
    main()
