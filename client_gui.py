"""
واجهة العميل — tkinter (المكتبة القياسية).

واجهة دردشة فورية كاملة تحاكي واجهة الويب: فقاعات، RTL، أسماء مرسلين،
شريط حالة (الخوارزمية/المصادقة/السلامة)، وشريط إعدادات حيّ.

تستخدم نفس منطق client.py (مصافحة ECDH + تشفير + HMAC) — لا تكرّر المنطق.

التشغيل:
    python client_gui.py
    python client_gui.py --host 127.0.0.1 --port 5000 --name ali
    python client_gui.py --name ali --cipher AES-CBC --no-encryption

متغيّرات البيئة (كما في client.py):
    CIPHER=AES-ECB python client_gui.py
    ENCRYPTION=0 python client_gui.py
"""

import argparse
import os
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
        self._last_cipher = None

        root.title("عميل الدردشة الآمنة")
        root.geometry("820x680")
        root.minsize(560, 480)
        g.apply_theme(root)

        self._build_connect_bar(host, port, name)
        self._build_status_bar()
        self._build_chat()
        self._build_compose()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._refresh_loop()

    # ---------- بناء الواجهة ----------
    def _build_connect_bar(self, host, port, name):
        bar = tk.Frame(self.root, bg=COLORS["panel"])
        bar.pack(fill="x", padx=10, pady=(10, 6))

        g.label(bar, "اتصال", bg=COLORS["panel"], font=g.FONT_TITLE).pack(side="right", padx=10, pady=6)

        self.btn = g.button(bar, "اتصال", self.toggle_connection, color=COLORS["ok"])
        self.btn.pack(side="left", padx=8)

        self.e_name = g.entry(bar, width=10)
        self.e_name.insert(0, name)
        self.e_name.pack(side="left")
        g.label(bar, "الاسم:", bg=COLORS["panel"]).pack(side="left", padx=(8, 2))

        self.e_port = g.entry(bar, width=6)
        self.e_port.insert(0, str(port))
        self.e_port.pack(side="left")
        g.label(bar, "المنفذ:", bg=COLORS["panel"]).pack(side="left", padx=(8, 2))

        self.e_host = g.entry(bar, width=12)
        self.e_host.insert(0, host)
        self.e_host.pack(side="left")
        g.label(bar, "الخادم:", bg=COLORS["panel"]).pack(side="left", padx=(8, 2))

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=COLORS["bg"])
        bar.pack(fill="x", padx=10)

        self.lbl_status = g.badge(bar, "غير متصل", COLORS["err"])
        self.lbl_status.pack(side="right", padx=4)
        self.lbl_cipher = g.badge(bar, "الخوارزمية: —")
        self.lbl_cipher.pack(side="left", padx=4)
        self.lbl_integrity = g.badge(bar, "السلامة: —")
        self.lbl_integrity.pack(side="left", padx=4)
        self.lbl_auth = g.badge(bar, "المصادقة: —")
        self.lbl_auth.pack(side="left", padx=4)

    def _build_chat(self):
        box = tk.Frame(self.root, bg=COLORS["bg"])
        box.pack(fill="both", expand=True, padx=10, pady=6)
        self.chat = g.ChatView(box)
        self.chat.pack(fill="both", expand=True)

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
            self.chat.add_system("[!] منفذ غير صالح")
            return

        self.client = ChatClient(host, port, name, on_message=self._on_message)
        self.chat.add_system(f"* جارٍ الاتصال بـ {host}:{port} …")

        def do_connect():
            try:
                self.client.connect()
                threading.Thread(target=self.client.receive_loop, daemon=True).start()
                self.connected = True
                self.logq.put(("ok", f"* متصل كـ «{name}»"))
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
        self.chat.add_system("* انقطع الاتصال")

    def send(self):
        text = self.e_msg.get().strip()
        if not text or not self.connected:
            return
        self.e_msg.delete(0, "end")
        try:
            self.client.send(text)
            # الويب لا يعرض رسالة المرسل محلياً (hub يعيد البث للجميع)،
            # لذا نعتمد على استقبالها من السيرفر لتجنّب التكرار.
        except Exception as exc:
            self.chat.add_system(f"[!] فشل الإرسال: {exc}")

    def _update_status(self):
        if self.connected and self.client:
            self.lbl_status.configure(text=g.rtl("متصل"), fg=COLORS["ok"])
            self.btn.configure(text=g.rtl("قطع"), bg=COLORS["err"])
            self.lbl_cipher.configure(text=g.rtl(f"الخوارزمية: {self.client.cipher}"))
            self.lbl_integrity.configure(
                text=g.rtl("السلامة: ✅" if self.client.integrity else "السلامة: ✗"),
                fg=COLORS["ok"] if self.client.integrity else COLORS["warn"],
            )
            self.lbl_auth.configure(
                text=g.rtl("المصادقة: ✅" if config.AUTHENTICATION else "المصادقة: ✗"),
                fg=COLORS["ok"] if config.AUTHENTICATION else COLORS["warn"],
            )
        else:
            self.lbl_status.configure(text=g.rtl("غير متصل"), fg=COLORS["err"])
            self.btn.configure(text=g.rtl("اتصال"), bg=COLORS["ok"])
            self.lbl_cipher.configure(text=g.rtl("الخوارزمية: —"))
            self.lbl_integrity.configure(text=g.rtl("السلامة: —"), fg=COLORS["muted"])
            self.lbl_auth.configure(text=g.rtl("المصادقة: —"), fg=COLORS["muted"])

    def _refresh_loop(self):
        self._update_status()
        while True:
            try:
                kind, text = self.logq.get_nowait()
            except queue.Empty:
                break
            if kind == "chat":
                # التنسيق: "اسم: نص" (كما يرسله client.receive_loop)
                sender, _, body = text.partition(": ")
                mine = bool(self.client and sender == self.client.name)
                self.chat.add_message(sender, body, mine=mine)
            else:
                self.chat.add_system(text)
        self.root.after(300, self._refresh_loop)

    def on_close(self):
        self.disconnect()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="واجهة العميل (tkinter)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--name", default="gui-user")
    parser.add_argument("--cipher", default=None, help="تجاوز خوارزمية التشفير (NONE/RC4/AES-ECB/AES-CBC/AES-CTR/AES-GCM/VIGENERE)")
    parser.add_argument("--no-encryption", action="store_true", help="إطفاء التشفير (نص واضح)")
    parser.add_argument("--no-integrity", action="store_true", help="إطفاء السلامة (HMAC)")
    parser.add_argument("--font", default=None, help="اسم خط يدعم العربية (مثل: 'Noto Naskh Arabic')")
    args = parser.parse_args()

    if args.font:
        os.environ["SC_GUI_FONT"] = args.font
    if args.cipher:
        config.CIPHER = args.cipher
    if args.no_encryption:
        config.ENCRYPTION = False
    if args.no_integrity:
        config.INTEGRITY = False

    root = tk.Tk()
    ClientGUI(root, args.host, args.port, args.name)
    root.mainloop()


if __name__ == "__main__":
    main()
