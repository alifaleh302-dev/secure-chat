"""
عناصر مشتركة بين واجهتي الخادم والعميل.

الواجهتان مكتوبتان بـ tkinter (المكتبة القياسية) — بلا تبعيات خارجية.

دعم العربية (مهم):
    tkinter يعتمد على الخطوط المثبّتة في النظام. إن طلبنا خطاً غير موجود
    (مثل "Segoe UI" على لينكس) يستبدله النظام بخط لا يحوي محارف عربية،
    فتظهر الحروف متقطّعة (منفصلة) أو كمربّعات فارغة.

    الحل: نكتشف تلقائياً أول خط متاح يدعم العربية من قائمة مرتّبة،
    ونسمح بتجاوزه عبر:
        - متغيّر البيئة  SC_GUI_FONT="Noto Naskh Arabic"
        - أو المعامل    --font "Noto Naskh Arabic"

    على Debian/Ubuntu ثبّت خطاً عربياً مرة واحدة:
        sudo apt install fonts-noto-core fonts-noto-arabic

ملاحظة: tkinter ليس جزءاً من كل توزيعات لينكس؛ على Debian/Ubuntu قد
تحتاج: sudo apt install python3-tk
"""

import os
import tkinter as tk
import tkinter.font as tkfont

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
    # ألوان فقاعات الدردشة (مطابقة لواجهة الويب)
    "bubble_me": "#2f81f7",
    "bubble_me_fg": "#ffffff",
    "bubble_other": "#21262d",
    "bubble_other_fg": "#e6edf3",
}

# خطوط مرشّحة للعربية — الأولى المتوفّرة تُختار.
_ARABIC_FONTS = (
    "Noto Naskh Arabic", "Noto Sans Arabic", "Noto Kufi Arabic",
    "Amiri", "Cairo", "Tajawal", "Almarai", "Scheherazade New",
    "Segoe UI", "Tahoma", "Arial", "DejaVu Sans", "FreeSans",
    "Liberation Sans", "sans-serif",
)
_MONO_FONTS = (
    "Consolas", "DejaVu Sans Mono", "Liberation Mono", "Courier New", "monospace",
)

# قيم مبدئية؛ تُحدَّث فعلياً داخل init_fonts() بعد إنشاء النافذة.
FONT = ("TkDefaultFont", 11)
FONT_MONO = ("TkFixedFont", 10)
FONT_TITLE = ("TkDefaultFont", 14, "bold")
FONT_SMALL = ("TkDefaultFont", 9)


def _available_families() -> set:
    try:
        return set(tkfont.families())
    except Exception:
        return set()


def _pick_font(candidates, fallback, size, weight=None):
    """يختار أول خط متاح من القائمة، مع احترام تجاوز SC_GUI_FONT."""
    override = os.environ.get("SC_GUI_FONT")
    families = _available_families()
    for name in ([override] if override else []) + list(candidates):
        if name and name in families:
            return (name, size, weight) if weight else (name, size)
    try:
        base = tkfont.nametofont(fallback).actual("family")
    except Exception:
        base = "sans-serif"
    return (base, size, weight) if weight else (base, size)


def init_fonts(root=None):
    """يضبط الخطوط العالمية على أول خط متاح يدعم العربية."""
    global FONT, FONT_MONO, FONT_TITLE, FONT_SMALL
    FONT = _pick_font(_ARABIC_FONTS, "TkDefaultFont", 11)
    FONT_TITLE = _pick_font(_ARABIC_FONTS, "TkDefaultFont", 14, "bold")
    FONT_SMALL = _pick_font(_ARABIC_FONTS, "TkDefaultFont", 9)
    FONT_MONO = _pick_font(_MONO_FONTS, "TkFixedFont", 10)
    return FONT


def apply_theme(root: tk.Tk) -> None:
    root.configure(bg=COLORS["bg"])
    init_fonts(root)


# ---------- دعم العربية: التشكيل (Shaping) والاتجاه (Bidi) ----------
# Tk على لينكس/X11 لا يمرّ عبر harfbuzz/fribidi، فلا يوصل الحروف العربية
# ولا يرتّب الجمل المختلطة. الحل: نكتشف ذلك تلقائياً، وإن كان ناقصاً
# نعالج النص بأنفسنا عبر arabic_reshaper (وصل الحروف) + python-bidi
# (الترتيب البصري). على ويندوز يكتشف أن Tk يشكّل فلا يعالج شيئاً.
_RLE = "\u202b"   # بداية تضمين من اليمين
_PDF = "\u202c"   # نهاية التضمين الاتجاهي

_ARABIC_RANGES = (
    ("\u0600", "\u06ff"),   # Arabic
    ("\u0750", "\u077f"),   # Arabic Supplement
    ("\u08a0", "\u08ff"),   # Arabic Extended-A
    ("\ufb50", "\ufdff"),   # Arabic Presentation Forms-A
    ("\ufe70", "\ufeff"),   # Arabic Presentation Forms-B
)

_SHAPING = None       # None = لم يُحدَّد بعد، True/False بعد الفحص
_RESHAFER = None


def has_arabic(text: str) -> bool:
    """هل النص يحوي محارف عربية؟"""
    return any(lo <= ch <= hi for ch in text for lo, hi in _ARABIC_RANGES)


def _shaping_supported() -> bool:
    """يكتشف هل Tk/النظام يشكّل العربية (يوصل الحروف).

    الطريقة: نقيس عرض كلمة عربية. إن كانت متصلة، عرضها أقل بكثير من
    مجموع عرض حروفها منفصلة. هذا اختبار عام يعمل على كل الأنظمة.
    """
    global _SHAPING
    if _SHAPING is not None:
        return _SHAPING
    override = os.environ.get("SC_GUI_SHAPE")
    if override is not None:
        _SHAPING = override.strip().lower() not in ("0", "false", "no", "off")
        return _SHAPING
    try:
        import tkinter.font as tkfont
        f = tkfont.Font(family=FONT[0], size=22)
        word = "مرحبا"
        joined = f.measure(word)
        isolated = sum(f.measure(c) for c in word)
        _SHAPING = joined < isolated * 0.9
    except Exception:
        _SHAPING = False
    return _SHAPING


def _reshaper():
    global _RESHAFER
    if _RESHAFER is None:
        import arabic_reshaper
        _RESHAFER = arabic_reshaper.ArabicReshaper(
            configuration={"delete_harakat": False, "support_ligatures": True}
        )
    return _RESHAFER


def _visual(text: str) -> str:
    """يحوّل العربية إلى أشكال متصلة مرتّبة بصرياً (حين لا يشكّل Tk)."""
    try:
        from bidi.algorithm import get_display
        return get_display(_reshaper().reshape(text))
    except Exception:
        return text


def rtl(text: str) -> str:
    """يهيّئ النص العربي للعرض الصحيح داخل Tk.

    - إن كان Tk يشكّل (ويندوز عادةً): نغلّف بعلامات الاتجاه فقط.
    - إن لم يكن (لينكس/X11): نطبّق وصل الحروف + الترتيب البصري بأنفسنا.
    يُطفأ كلياً بـ SC_GUI_BIDI=0.
    """
    if os.environ.get("SC_GUI_BIDI", "1").strip().lower() in ("0", "false", "no", "off"):
        return text
    if not has_arabic(text):
        return text
    if _shaping_supported():
        return _RLE + text + _PDF
    return _visual(text)


# ---------- عناصر أساسية ----------
def label(master, text, **kw):
    kw.setdefault("bg", COLORS["bg"])
    kw.setdefault("fg", COLORS["text"])
    kw.setdefault("font", FONT)
    return tk.Label(master, text=rtl(text), **kw)


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
    kw.setdefault("font", (FONT[0], 11, "bold"))
    kw.setdefault("relief", "flat")
    kw.setdefault("activebackground", COLORS["muted"])
    kw.setdefault("cursor", "hand2")
    kw.setdefault("padx", 12)
    kw.setdefault("pady", 5)
    return tk.Button(master, text=rtl(text), command=command, **kw)


def badge(master, text, color=None):
    """شارة صغيرة (للحالة/الخوارزمية/المصادقة)."""
    return tk.Label(
        master, text=rtl(text), bg=COLORS["field"], fg=color or COLORS["muted"],
        font=FONT_SMALL, padx=8, pady=2,
    )


def checkbox(master, text, variable):
    return tk.Checkbutton(
        master, text=rtl(text), variable=variable,
        bg=COLORS["bg"], fg=COLORS["text"], font=FONT,
        selectcolor=COLORS["panel"], activebackground=COLORS["bg"],
        activeforeground=COLORS["text"], anchor="w", highlightthickness=0,
    )


class LogView(tk.Frame):
    """منطقة سجل ملوّنة بأنواع الرسائل (للواجهة الإدارية)."""

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
        sb.pack(side="left", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        for tag, color in self.TAGS.items():
            self.text.tag_configure(tag, foreground=color)

    def append(self, text: str, kind: str = "chat") -> None:
        self.text.configure(state="normal")
        self.text.insert("end", rtl(text) + "\n", kind)
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


class ChatView(tk.Frame):
    """واجهة دردشة بفقاعات — تحاكي واجهة الويب (RTL).

    - رسائلي على اليمين بلون مميّز.
    - رسائل الآخرين على اليسار مع اسم المرسل.
    - رسائل النظام في الوسط بلون باهت.
    """

    def __init__(self, master, **kw):
        super().__init__(master, bg=COLORS["panel"], **kw)
        self.canvas = tk.Canvas(self, bg=COLORS["panel"], highlightthickness=0, bd=0)
        self.sb = tk.Scrollbar(self, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.sb.pack(side="left", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=COLORS["panel"])
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)

        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind_all(seq, self._on_wheel)

    # ---------- أحداث ----------
    def _on_inner(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._scroll_end()

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)

    def _on_wheel(self, event):
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -1 if getattr(event, "delta", 0) > 0 else 1
        self.canvas.yview_scroll(delta, "units")
        return "break"

    def _scroll_end(self):
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _wrap(self) -> int:
        width = self.canvas.winfo_width()
        return max(240, int(width * 0.68)) if width > 10 else 420

    # ---------- الإضافة ----------
    def add_message(self, sender: str, text: str, mine: bool = False) -> None:
        row = tk.Frame(self.inner, bg=COLORS["panel"])
        row.pack(fill="x", padx=10, pady=4)

        bg = COLORS["bubble_me"] if mine else COLORS["bubble_other"]
        fg = COLORS["bubble_me_fg"] if mine else COLORS["bubble_other_fg"]
        bubble = tk.Frame(row, bg=bg, padx=12, pady=8)
        bubble.pack(side="right" if mine else "left")

        if sender and not mine:
            tk.Label(
                bubble, text=rtl(sender), bg=bg, fg=COLORS["accent"],
                font=FONT_SMALL, anchor="e", justify="right",
            ).pack(fill="x", pady=(0, 2))

        tk.Label(
            bubble, text=rtl(text), bg=bg, fg=fg, font=FONT,
            wraplength=self._wrap(), justify="right", anchor="e",
        ).pack(fill="x")

        self._scroll_end()

    def add_system(self, text: str) -> None:
        tk.Label(
            self.inner, text=rtl(text), bg=COLORS["panel"], fg=COLORS["muted"],
            font=FONT_SMALL, justify="center", wraplength=self._wrap(),
        ).pack(pady=3, padx=10)
        self._scroll_end()

    def clear(self) -> None:
        for child in self.inner.winfo_children():
            child.destroy()
