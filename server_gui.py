"""
واجهة إدارة الخادم — tkinter (المكتبة القياسية).

تُشغّل سيرفر الدردشة داخل نفس العملية وتتحكّم به:
    - بدء/إيقاف السيرفر
    - تعديل إعدادات الأمان الحيّة (تشفير، سلامة، مصادقة، خوارزمية، مفتاح فيجينير)
    - مراقبة العملاء المتصلين والرسائل لحظياً

التشغيل:
    python server_gui.py
    python server_gui.py --port 5000
"""

import argparse
import os
import queue
import threading
import tkinter as tk
import webbrowser

import config
import gui_common as g
from gui_common import COLORS
from hub import ChatHub
import server as server_mod

CIPHERS = ["NONE", "RC4", "AES-ECB", "AES-CBC", "AES-CTR", "AES-GCM", "VIGENERE"]


class ServerAdminGUI:
    def __init__(self, root: tk.Tk, host: str, port: int):
        self.root = root
        self.host, self.port = host, port
        self.hub = ChatHub()
        self.stop_event = None
        self.server_sock = None
        self.server_thread = None
        self.running = False
        self.logq = queue.Queue()

        root.title("إدارة الخادم — الدردشة الآمنة")
        root.geometry("880x640")
        g.apply_theme(root)

        self._build_header()
        self._build_settings()
        self._build_clients()
        self._build_log()
        self._build_footer()

        self._refresh_loop()

    # ---------- بناء الواجهة ----------
    def _build_header(self):
        bar = tk.Frame(self.root, bg=COLORS["panel"])
        bar.pack(fill="x", padx=10, pady=(10, 6))
        g.label(bar, "لوحة إدارة الخادم", bg=COLORS["panel"], font=g.FONT_TITLE).pack(side="right", padx=10, pady=6)

        self.status = g.label(bar, "متوقف", bg=COLORS["panel"], fg=COLORS["err"], font=g.FONT)
        self.status.pack(side="left", padx=10)

        self.btn_toggle = g.button(bar, "تشغيل السيرفر", self.toggle_server, color=COLORS["ok"])
        self.btn_toggle.pack(side="left", padx=4)

        g.button(bar, "فتح لوحة التحكم", self._open_settings, color=COLORS["muted"]).pack(side="left", padx=4)
        g.button(bar, "فتح الدردشة", self._open_chat, color=COLORS["muted"]).pack(side="left", padx=4)

    def _build_settings(self):
        box = tk.LabelFrame(self.root, text=" إعدادات الأمان ", bg=COLORS["bg"], fg=COLORS["text"], font=g.FONT)
        box.pack(fill="x", padx=10, pady=6)

        self.v_enc = tk.BooleanVar(value=config.ENCRYPTION)
        self.v_int = tk.BooleanVar(value=config.INTEGRITY)
        self.v_auth = tk.BooleanVar(value=config.AUTHENTICATION)
        self.v_cipher = tk.StringVar(value=config.CIPHER)
        self.v_ckey = tk.StringVar(value=config.CLASSICAL_KEY)

        g.checkbox(box, "التشفير", self.v_enc).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        g.checkbox(box, "السلامة (HMAC)", self.v_int).grid(row=0, column=1, sticky="w", padx=8, pady=4)
        g.checkbox(box, "المصادقة", self.v_auth).grid(row=0, column=2, sticky="w", padx=8, pady=4)

        g.label(box, "الخوارزمية:").grid(row=1, column=0, sticky="e", padx=8)
        dd = tk.OptionMenu(box, self.v_cipher, *CIPHERS)
        dd.configure(bg=COLORS["field"], fg=COLORS["text"], font=g.FONT, relief="flat",
                     highlightthickness=0, activebackground=COLORS["muted"])
        dd["menu"].configure(bg=COLORS["field"], fg=COLORS["text"], font=g.FONT)
        dd.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        g.label(box, "مفتاح فيجينير:").grid(row=1, column=2, sticky="e", padx=8)
        g.entry(box, textvariable=self.v_ckey, width=14).grid(row=1, column=3, sticky="w", padx=8)

        g.button(box, "تطبيق", self.apply_settings).grid(row=0, column=3, padx=8, sticky="e")

    def _build_clients(self):
        box = tk.LabelFrame(self.root, text=" العملاء المتصلون ", bg=COLORS["bg"], fg=COLORS["text"], font=g.FONT)
        box.pack(fill="x", padx=10, pady=6)
        self.clients_lbl = g.label(box, "لا يوجد أحد.", anchor="w", justify="right")
        self.clients_lbl.pack(fill="x", padx=10, pady=8)

    def _build_log(self):
        box = tk.LabelFrame(self.root, text=" سجل الرسائل ", bg=COLORS["bg"], fg=COLORS["text"], font=g.FONT)
        box.pack(fill="both", expand=True, padx=10, pady=6)
        self.log = g.LogView(box)
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

    def _build_footer(self):
        bar = tk.Frame(self.root, bg=COLORS["bg"])
        bar.pack(fill="x", padx=10, pady=(0, 10))
        g.button(bar, "مسح السجل", lambda: self.log.clear(), color=COLORS["muted"]).pack(side="left")

    # ---------- منطق ----------
    def toggle_server(self):
        if self.running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if self.running:
            return
        config.HOST, config.PORT = self.host, self.port
        self.stop_event = threading.Event()

        def bound(sock):
            self.server_sock = sock

        def run():
            try:
                server_mod.run_chat_server(self.hub, self.stop_event, bound)
            except Exception as exc:  # منفذ مشغول مثلاً
                self.logq.put(("error", f"[!] تعذّر تشغيل السيرفر: {exc}"))
                self.running = False
                self._update_status()
                return
            self.logq.put(("info", "[*] أُوقف السيرفر."))

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        self.running = True
        self._update_status()
        self.logq.put(("ok", f"[*] السيرفر يعمل على المنفذ {self.port}"))
        self.logq.put(("info", f"    لوحة التحكم: http://localhost:{self.port}/settings"))

    def stop_server(self):
        if not self.running:
            return
        self.stop_event.set()
        try:
            if self.server_sock:
                self.server_sock.close()
        except Exception:
            pass
        self.hub.disconnect_all()
        self.running = False
        self._update_status()

    def _update_status(self):
        if self.running:
            self.status.configure(text=g.rtl("يعمل"), fg=COLORS["ok"])
            self.btn_toggle.configure(text=g.rtl("إيقاف السيرفر"), bg=COLORS["err"])
        else:
            self.status.configure(text=g.rtl("متوقف"), fg=COLORS["err"])
            self.btn_toggle.configure(text=g.rtl("تشغيل السيرفر"), bg=COLORS["ok"])

    def apply_settings(self):
        config.update({
            "ENCRYPTION": self.v_enc.get(),
            "INTEGRITY": self.v_int.get(),
            "AUTHENTICATION": self.v_auth.get(),
            "CIPHER": self.v_cipher.get(),
            "CLASSICAL_KEY": self.v_ckey.get(),
        })
        self.logq.put(("ok", f"[*] طُبّقت الإعدادات: {self.v_cipher.get()} "
                            f"(تشفير={self.v_enc.get()}, سلامة={self.v_int.get()}, مصادقة={self.v_auth.get()})"))

    def _open_settings(self):
        webbrowser.open(f"http://localhost:{self.port}/settings")

    def _open_chat(self):
        webbrowser.open(f"http://localhost:{self.port}/chat")

    def _refresh_loop(self):
        # عملاء
        snap = self.hub.snapshot()
        if snap:
            txt = " • ".join(f"{c['name']} ({c['mode']}, {c['cipher']})" for c in snap)
        else:
            txt = "لا يوجد أحد."
        self.clients_lbl.configure(text=txt)
        # سجل
        while True:
            try:
                kind, text = self.logq.get_nowait()
            except queue.Empty:
                break
            self.log.append(text, kind)
        self.root.after(1000, self._refresh_loop)

    def on_close(self):
        self.stop_server()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="واجهة إدارة الخادم (tkinter)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--font", default=None, help="اسم خط يدعم العربية (مثل: 'Noto Naskh Arabic')")
    args = parser.parse_args()

    if args.font:
        os.environ["SC_GUI_FONT"] = args.font

    root = tk.Tk()
    app = ServerAdminGUI(root, args.host, args.port)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
