"""
عناصر مشتركة بين واجهتي الخادم والعميل.

الواجهتان مكتوبتان بـ tkinter (المكتبة القياسية في بايثون) — بلا أي
تبعيات خارجية، فتعملان على ويندوز/لينكس/ماك مباشرة بعد تثبيت بايثون.

ملاحظة: tkinter ليس جزءاً من كل توزيعات لينكس؛ على Debian/Ubuntu قد
تحتاج: sudo apt install python3-tk
"""

import tkinter as tk

COLORS = {
    "bg": "#0f172a",
    "panel": "#1e293b",
    "field": "#334155",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
    "accent": "#38bdf8",
    "ok": "#22c55e",
    "warn": "#f59e0b",
    "err": "#ef4444",
    "me": "#a78bfa",
}

FONT = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")


def apply_theme(root: tk.Tk) -> None:
    root.configure(bg=COLORS["bg"])


def label(master, text, **kw):
    kw.setdefault("bg", COLORS["bg"])
    kw.setdefault("fg", COLORS["text"])
    kw.setdefault("font", FONT)
    return tk.Label(master, text=text, **kw)


def entry(master, **kw):
    kw.setdefault("bg", COLORS["field"])
    kw.setdefault("fg", COLORS["text"])
    kw.setdefault("font", FONT)
    kw.setdefault("insertbackground", COLORS["text"])
    kw.setdefault("relief", "flat")
    return tk.Entry(master, **kw)


def button(master, text, command, color=None, **kw):
    kw.setdefault("bg", color or COLORS["accent"])
    kw.setdefault("fg", "#0b1220")
    kw.setdefault("font", ("Segoe UI", 11, "bold"))
    kw.setdefault("relief", "flat")
    kw.setdefault("activebackground", COLORS["muted"])
    kw.setdefault("padx", 10)
    kw.setdefault("pady", 4)
    return tk.Button(master, text=text, command=command, **kw)


def checkbox(master, text, variable):
    return tk.Checkbutton(
        master, text=text, variable=variable,
        bg=COLORS["bg"], fg=COLORS["text"], font=FONT,
        selectcolor=COLORS["panel"], activebackground=COLORS["bg"],
        activeforeground=COLORS["text"], anchor="w", highlightthickness=0,
    )


class LogView(tk.Frame):
    """منطقة سجل ملوّنة بأنواع الرسائل."""

    TAGS = {
        "system": COLORS["muted"],
        "chat": COLORS["text"],
        "me": COLORS["me"],
        "error": COLORS["err"],
        "info": COLORS["accent"],
        "ok": COLORS["ok"],
    }

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.text = tk.Text(
            self, wrap="word", bg=COLORS["panel"], fg=COLORS["text"],
            font=FONT, relief="flat", padx=8, pady=6,
            insertbackground=COLORS["text"], state="disabled",
        )
        sb = tk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        for tag, color in self.TAGS.items():
            self.text.tag_configure(tag, foreground=color)

    def append(self, text: str, kind: str = "chat") -> None:
        self.text.configure(state="normal")
        self.text.insert("end", text + "\n", kind)
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
