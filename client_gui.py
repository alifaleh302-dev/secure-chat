"""
واجهة العميل — tkinter (المكتبة القياسية).

عميل دردشة رسومي يربط نفس منطق client.py (مصافحة ECDH + تشفير + HMAC)
بواجهة نافذة بدل الطرفية.

التشغيل:
    python client_gui.py
    python client_gui.py --host 127.0.0.1 --port 5000 --name ali
"""

import argparse
import queue
import threading
import tkinter as tk

import config
import gui_common as g
from gui_common import COLORS
from client import ChatClient
import protocol


class ClientGUI:
    def __init__(self, root: tk.Tk, host: str, port: int, name: str):
        self.root = root
        self.client = None
        self.connected = False
        self.logq = queue.Queue()

        root.title("عميل الدردشة الآمنة")
        root.geometry("720x600")
        g.apply_theme(root)

        self._build_connect_bar(host, port, name)
        self._build_info_bar()
        self._build_log()
        self._build_compose()

        self._refresh_loop()

    # ---------- بناء الواجهة ----------
    def _build_connect_bar(self, host, port, name):
        bar = tk.Frame(self.root, bg=COLORS["panel"])
        bar.pack(fill="x", padx=10, pady=(10, 6))
        g.label(bar, "اتصال", bg=COLORS["panel"], font=g.FONT_TITLE).pack(side="right", padx=10, pady=6)

        g.label(bar, "الخادم:", bg=COLORS["panel"]).pack(side="left", padx=(8, 2))
        self.e_host = g.entry(bar, width=12)
        self.e_host.insert(0, host)
        self.e_host.pack(side="left")

        g.label(bar, "المنفذ:", bg=COLORS["panel"]).pack(side="left", padx=(8, 2))
        self.e_port = g.entry(bar, width=6)
        self.e_port.insert(0, str(port))
        self.e_port.pack(side="left")

        g.label(bar, "الاسم:", bg=COLORS["panel"]).pack(side="left", padx=(8, 2))
        self.e_name = g.entry(bar, width=10)
        self.e_name.insert(0, name)
        self.e_name.pack(side="left")

        self.btn = g.button(bar, "اتصال", self.toggle_connection, color=COLORS["ok"])
        self.btn.pack(side="left", padx=8)

    def _build_info_bar(self):
        bar = tk.Frame(self.root, bg=COLORS["bg"])
        bar.pack(fill="x", padx=10)
        self.lbl_status = g.label(bar, "غير متصل", fg=COLORS["err"])
        self.lbl_status.pack(side="right", padx=6)
        self.lbl_cipher = g.label(bar, "الخوارزمية: —", fg=COLORS["accent"])
        self.lbl_cipher.pack(side="left", padx=6)
        self.lbl_auth = g.label(bar, "المصادقة: —", fg=COLORS["accent"])
        self.lbl_auth.pack(side="left", padx=6)

    def _build_log(self):
        box = tk.LabelFrame(self.root, text=" المحادثة ", bg=COLORS["bg"], fg=COLORS["text"], font=g.FONT)
        box.pack(fill="both", expand=True, padx=10, pady=6)
        self.log = g.LogView(box)
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

    def _build_compose(self):
        bar = tk.Frame(self.root, bg=COLORS["bg"])
        bar.pack(fill="x", padx=10, pady=(0, 10))
        self.e_msg = g.entry(bar)
        self.e_msg.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=6)
        self.e_msg.bind("<Return>", lambda _e: self.send())
        self.btn_send = g.button(bar, "إرسال", self.send, color=COLORS["accent"])
        self.btn_send.pack(side="left")

    # ---------- منطق ----------
    def _on_message(self, kind, text):
        self.logq.put((kind, text))

    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        host = self.e_host.get().strip()
        name = self.e_name.get().strip() or "gui-user"
        try:
            port = int(self.e_port.get().strip())
        except ValueError:
            self.log.append("[!] منفذ غير صالح", "error")
            return

        self.client = ChatClient(host, port, name, on_message=self._on_message)
        self.log.append(f"[*] جارٍ الاتصال بـ {host}:{port} …", "info")

        def do_connect():
            try:
                self.client.connect()
                threading.Thread(target=self.client.receive_loop, daemon=True).start()
                self.connected = True
                self.logq.put(("ok", f"[*] متصل كـ «{name}»"))
                self.logq.put(("info", f"    الخوارزمية: {self.client.cipher}"))
            except Exception as exc:
                self.logq.put(("error", f"[!] فشل الاتصال: {exc}"))
                self.connected = False

        threading.Thread(target=do_connect, daemon=True).start()

    def disconnect(self):
        if self.client:
            try:
                self.client.transport.send_frame(protocol.pack_frame(protocol.T_BYE))
            except Exception:
                pass
            try:
                self.client.transport.close()
            except Exception:
                pass
        self.connected = False
        self.log.append("[*] انقطع الاتصال", "system")

    def send(self):
        text = self.e_msg.get().strip()
        if not text or not self.connected:
            return
        self.e_msg.delete(0, "end")
        try:
            self.client.send(text)
        except Exception as exc:
            self.log.append(f"[!] فشل الإرسال: {exc}", "error")

    def _refresh_loop(self):
        # حالة الاتصال
        if self.connected and self.client:
            self.lbl_status.configure(text="متصل", fg=COLORS["ok"])
            self.btn.configure(text="قطع", bg=COLORS["err"])
            self.lbl_cipher.configure(text=f"الخوارزمية: {self.client.cipher}")
            self.lbl_auth.configure(text="المصادقة: ✅" if config.AUTHENTICATION else "المصادقة: ✗")
        else:
            self.lbl_status.configure(text="غير متصل", fg=COLORS["err"])
            self.btn.configure(text="اتصال", bg=COLORS["ok"])
        # سجل
        while True:
            try:
                kind, text = self.logq.get_nowait()
            except queue.Empty:
                break
            self.log.append(text, kind)
        self.root.after(500, self._refresh_loop)

    def on_close(self):
        self.disconnect()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="واجهة العميل (tkinter)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--name", default="gui-user")
    args = parser.parse_args()

    root = tk.Tk()
    app = ClientGUI(root, args.host, args.port, args.name)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
