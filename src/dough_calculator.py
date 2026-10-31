#!/usr/bin/env python3
"""
Dough Calculator - desktop GUI (Tkinter) + CLI.

Layout mirrors the public Dough Guy calculator page. Constants were fitted to
readings from that calculator (6 pizzas at 16" regular/thin/thick/GF, plus GF
at 10" and 20"). Colours, tips, instructions and bake times are my own approximations.

Run:  python dough_calculator.py          (GUI)
      python dough_calculator.py --cli --size 14 --count 4 --thickness thin
"""

import argparse
import math
from dataclasses import dataclass

try:
    import tkinter as tk
except ImportError:
    tk = None

# ---- dough model ------------------------------------------------------------
GRAMS_PER_SQ_IN = {"thin": 2.0342, "regular": 2.3874, "thick": 3.1135}
GF_BALL_MULT = 1.1715
FLOUR_FRACTION = 0.592
HYDRATION = {"normal": 0.62, "gluten_free": 0.80}
YEAST_PCT, SALT_PCT, SUGAR_PCT, OIL_PCT = 0.004, 0.025, 0.02, 0.033


@dataclass
class Recipe:
    size: int
    count: int
    thickness: str
    gluten_free: bool
    ball_g: int
    flour_g: int
    water_g: int
    yeast_g: float
    salt_g: float
    sugar_g: float
    oil_g: float
    hydration_pct: int

    def rows(self):
        flour = "GF flour" if self.gluten_free else "Bread flour"
        pct = lambda x: f"{x * 100:g}%"
        return [
            (flour, f"{self.flour_g} g", "100%"),
            ("Water", f"{self.water_g} g", f"{self.hydration_pct}%"),
            ("Yeast", f"{self.yeast_g:.1f} g", pct(YEAST_PCT)),
            ("Salt", f"{self.salt_g:.0f} g", pct(SALT_PCT)),
            ("Sugar", f"{self.sugar_g:.0f} g", pct(SUGAR_PCT)),
            ("Olive oil", f"{self.oil_g:.0f} g", pct(OIL_PCT)),
        ]

    def kind(self):
        return "Gluten-free dough" if self.gluten_free else "Regular dough"

    def meta(self):
        return f'{self.count} balls · {self.size}" · {self.thickness}'

    def text(self):
        lines = [f'{self.count}x {self.size}" pizza · Dough ball: {self.ball_g}g', ""]
        lines += [f"{n}: {a.replace(' ', '')}" for n, a, _ in self.rows()]
        return "\n".join(lines)


def calculate(size=16, count=6, thickness="regular", gluten_free=False) -> Recipe:
    if thickness not in GRAMS_PER_SQ_IN:
        raise ValueError(f"thickness must be one of {list(GRAMS_PER_SQ_IN)}")
    area = math.pi * (size / 2) ** 2
    ball = area * GRAMS_PER_SQ_IN[thickness] * (GF_BALL_MULT if gluten_free else 1)
    flour = ball * count * FLOUR_FRACTION
    hyd = HYDRATION["gluten_free" if gluten_free else "normal"]
    return Recipe(
        size, count, thickness, gluten_free, round(ball),
        round(flour), round(flour * hyd),
        flour * YEAST_PCT, flour * SALT_PCT, flour * SUGAR_PCT, flour * OIL_PCT,
        round(hyd * 100),
    )


# ---- look & feel --------------------------------------------------------------
BG, CARD, FIELD = "#121212", "#1b1b1b", "#262626"
FG, MUTED, ACCENT, ACCENT_FG, TRACK = "#f4f1ea", "#8d8d8d", "#F5C842", "#111111", "#3a3a3a"
FONT = "Helvetica"

S = 1.0  # UI scale factor, set from screen DPI in run_gui()


def px(n):
    """Scale a pixel measurement by the current DPI factor."""
    return int(round(n * S))


INSTRUCTIONS = [
    "Cool water to under 16°C",
    "Mix water + active dry yeast",
    "Add flour + olive oil, mix 2 min",
    "Add sugar and salt on low",
    "Mix 10 more minutes",
    "Cover, rest 1–3 hours",
    "Shape into balls, seal seam",
    "Refrigerate 2–4 days (3 ideal)",
    "Bring to room temp before using",
]

BAKE = {
    "thin": ("275 °C", "5–7 min"),
    "regular": ("260 °C", "7–9 min"),
    "thick": ("230 °C", "12–15 min"),
}
BAKE_NOTE = ("Preheat the oven (and any steel or stone) for 45–60 minutes. "
             "Gluten-free dough: add 1–2 min. Ovens vary - bake until the crust is golden.")
PRO_TIP = ("Let the dough balls come to room temperature before stretching - "
           "cold dough snaps back and tears.")


def make_button(parent, text, command, primary=False):
    bg, fg = (ACCENT, ACCENT_FG) if primary else (FIELD, FG)
    b = tk.Label(parent, text=text, bg=bg, fg=fg, font=(FONT, 10, "bold"),
                 padx=px(16), pady=px(8), cursor="hand2")
    b.bind("<Button-1>", lambda _e: command())
    return b


_Canvas = tk.Canvas if tk else object
_Frame = tk.Frame if tk else object


class CanvasSlider(_Canvas):
    """Flat slider: grey track, yellow fill and knob, labelled ticks."""

    def __init__(self, parent, lo, hi, value, ticks, command, width=340):
        super().__init__(parent, width=px(width), height=px(48), bg=CARD, highlightthickness=0)
        self.lo, self.hi, self.value, self.ticks, self.command = lo, hi, value, ticks, command
        self.pad = px(12)
        self.bind("<Configure>", lambda _e: self.draw())
        self.bind("<Button-1>", self._click)
        self.bind("<B1-Motion>", self._click)

    def _x(self, v):
        w = self.winfo_width()
        return self.pad + (v - self.lo) / (self.hi - self.lo) * (w - 2 * self.pad)

    def draw(self):
        self.delete("all")
        w, y = self.winfo_width(), px(16)
        self.create_line(self.pad, y, w - self.pad, y, width=px(6), fill=TRACK, capstyle="round")
        self.create_line(self.pad, y, self._x(self.value), y, width=px(6), fill=ACCENT, capstyle="round")
        x = self._x(self.value)
        r = px(9)
        self.create_oval(x - r, y - r, x + r, y + r, fill=ACCENT, outline=CARD, width=px(3))
        for v, label in self.ticks:
            self.create_text(self._x(v), px(38), text=label, fill=MUTED, font=(FONT, 9))

    def _click(self, e):
        w = self.winfo_width()
        frac = min(1, max(0, (e.x - self.pad) / (w - 2 * self.pad)))
        v = round(self.lo + frac * (self.hi - self.lo))
        if v != self.value:
            self.value = v
            self.draw()
            self.command(v)


class Segmented(_Frame):
    """Pill-style choice selector (Thin / Regular / Thick)."""

    def __init__(self, parent, options, value, command):
        super().__init__(parent, bg=FIELD)
        self.command, self.labels, self.value = command, {}, value
        for o in options:
            lab = tk.Label(self, text=o.title(), font=(FONT, 10, "bold"),
                           padx=px(18), pady=px(7), cursor="hand2")
            lab.pack(side="left", padx=px(2), pady=px(2))
            lab.bind("<Button-1>", lambda _e, o=o: self.select(o))
            self.labels[o] = lab
        self._paint()

    def select(self, o):
        self.value = o
        self._paint()
        self.command(o)

    def _paint(self):
        for o, lab in self.labels.items():
            on = o == self.value
            lab.config(bg=ACCENT if on else FIELD, fg=ACCENT_FG if on else MUTED)


class Toggle(_Canvas):
    def __init__(self, parent, value, command):
        super().__init__(parent, width=px(46), height=px(26), bg=CARD,
                         highlightthickness=0, cursor="hand2")
        self.value, self.command = value, command
        self.bind("<Button-1>", self._flip)
        self.draw()

    def draw(self):
        self.delete("all")
        col = ACCENT if self.value else TRACK
        self.create_oval(2, 2, 24, 24, fill=col, outline=col)
        self.create_oval(22, 2, 44, 24, fill=col, outline=col)
        self.create_rectangle(13, 2, 33, 24, fill=col, outline=col)
        x = 33 if self.value else 13
        self.create_oval(x - 9, 4, x + 9, 22, fill="#fff", outline="#fff")
        self.scale("all", 0, 0, S, S)

    def _flip(self, _e):
        self.value = not self.value
        self.draw()
        self.command(self.value)


class App:
    def __init__(self, root):
        self.root = root
        self.size, self.count, self.thick, self.gf = 16, 6, "regular", False
        root.title("Dough Calculator")
        root.configure(bg=BG)
        root.minsize(px(940), px(480))
        root.geometry(f"{px(1000)}x{px(760)}")

        # scrollable page
        outer = tk.Frame(root, bg=BG)
        outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        bar = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        page = tk.Frame(self.canvas, bg=BG)
        self.page_win = self.canvas.create_window((0, 0), window=page, anchor="nw")
        page.bind("<Configure>", lambda _e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.page_win, width=e.width))
        self.page = page
        root.bind_all("<MouseWheel>", self._wheel)
        root.bind_all("<Button-4>", lambda _e: self._scroll(-1))
        root.bind_all("<Button-5>", lambda _e: self._scroll(1))

        # header
        hero = tk.Frame(page, bg=BG)
        hero.pack(anchor="w", padx=px(32), pady=(px(28), px(0)))
        title = tk.Frame(hero, bg=BG)
        title.pack(anchor="w")
        tk.Label(title, text="Dough ", bg=BG, fg=FG, font=(FONT, 34, "bold")).pack(side="left")
        tk.Label(title, text="Calculator.", bg=BG, fg=ACCENT,
                 font=(FONT, 34, "bold italic")).pack(side="left")
        tk.Label(hero, text="Dial in your size, quantity, and thickness.\nGet exact ingredient weights.",
                 bg=BG, fg=MUTED, font=(FONT, 11), justify="left").pack(anchor="w")

        body = tk.Frame(page, bg=BG)
        body.pack(fill="both", expand=True, padx=px(32), pady=px(20))
        body.columnconfigure(1, weight=1)
        self._settings(body).grid(row=0, column=0, sticky="n", padx=(px(0), px(20)))
        self._results(body).grid(row=0, column=1, sticky="nsew")
        self._bottom(page)
        self.update()

    def _scroll(self, units):
        if self.page.winfo_reqheight() > self.canvas.winfo_height():
            self.canvas.yview_scroll(units, "units")

    def _wheel(self, e):
        d = e.delta
        self._scroll(-int(d / 120) if abs(d) >= 120 else -d)

    # ---- left column: settings ----
    def _settings(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=px(22), pady=px(20))
        tk.Label(card, text="YOUR PIZZA SETTINGS", bg=CARD, fg=MUTED,
                 font=(FONT, 9, "bold")).pack(anchor="w", pady=(px(0), px(14)))

        def slider_block(label, lo, hi, val, ticks, cb):
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x")
            tk.Label(row, text=label, bg=CARD, fg=FG, font=(FONT, 11)).pack(side="left")
            valLbl = tk.Label(row, bg=CARD, fg=ACCENT, font=(FONT, 16, "bold"))
            valLbl.pack(side="right")
            CanvasSlider(card, lo, hi, val, ticks, cb).pack(fill="x", pady=(px(2), px(14)))
            return valLbl

        self.size_lbl = slider_block("Pizza size", 10, 20, self.size,
                                     [(10, '10"'), (15, '15"'), (20, '20"')], self._set_size)
        self.count_lbl = slider_block("Number of pizzas", 1, 10, self.count,
                                      [(1, "1"), (5, "5"), (10, "10")], self._set_count)

        tk.Label(card, text="Thickness", bg=CARD, fg=FG, font=(FONT, 11)).pack(anchor="w")
        Segmented(card, ["thin", "regular", "thick"], self.thick,
                  self._set_thick).pack(anchor="w", pady=(px(6), px(16)))

        gf = tk.Frame(card, bg=CARD)
        gf.pack(fill="x", pady=(px(0), px(16)))
        Toggle(gf, self.gf, self._set_gf).pack(side="left")
        txt = tk.Frame(gf, bg=CARD)
        txt.pack(side="left", padx=px(12))
        tk.Label(txt, text="Gluten free", bg=CARD, fg=FG, font=(FONT, 11, "bold")).pack(anchor="w")
        tk.Label(txt, text="GF flour + adjusted hydration", bg=CARD, fg=MUTED,
                 font=(FONT, 9)).pack(anchor="w")

        tip = tk.Frame(card, bg=FIELD, padx=px(12), pady=px(10))
        tip.pack(fill="x")
        tk.Label(tip, text="PRO TIP", bg=FIELD, fg=ACCENT, font=(FONT, 9, "bold")).pack(anchor="w")
        tk.Label(tip, text=PRO_TIP, bg=FIELD, fg=FG, font=(FONT, 10),
                 wraplength=px(300), justify="left").pack(anchor="w", pady=(px(2), px(0)))
        return card

    # ---- right column: results ----
    def _results(self, parent):
        card = tk.Frame(parent, bg=CARD, padx=px(22), pady=px(20))

        tiles = tk.Frame(card, bg=CARD)
        tiles.pack(fill="x")
        self.tiles = {}
        for i, (key, label, unit) in enumerate([
                ("ball", "Dough ball", "grams each"), ("flour", "Total flour", "grams"),
                ("water", "Total water", "grams"), ("hyd", "Hydration", "percent")]):
            tiles.columnconfigure(i, weight=1, uniform="t")
            t = tk.Frame(tiles, bg=FIELD, padx=px(12), pady=px(10))
            t.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else px(8), 0))
            tk.Label(t, text=label, bg=FIELD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
            v = tk.Label(t, bg=FIELD, fg=ACCENT, font=(FONT, 22, "bold"))
            v.pack(anchor="w")
            tk.Label(t, text=unit, bg=FIELD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
            self.tiles[key] = v

        self.kind_lbl = tk.Label(card, bg=CARD, fg=FG, font=(FONT, 12, "bold"))
        self.kind_lbl.pack(anchor="w", pady=(px(18), px(0)))
        self.meta_lbl = tk.Label(card, bg=CARD, fg=MUTED, font=(FONT, 10))
        self.meta_lbl.pack(anchor="w", pady=(px(0), px(10)))

        self.table = tk.Frame(card, bg=CARD)
        self.table.pack(fill="x")
        self.table.columnconfigure(0, weight=1)

        btns = tk.Frame(card, bg=CARD)
        btns.pack(anchor="w", pady=px(16))
        self.copy_btn = make_button(btns, "Copy recipe", self.copy, primary=True)
        self.copy_btn.pack(side="left")
        make_button(btns, "Print / save", self.save).pack(side="left", padx=px(8))
        return card

    # ---- bottom row: instructions + bake notes ----
    def _bottom(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill="x", padx=px(32), pady=(0, px(32)))
        wrap.columnconfigure(0, weight=3, uniform="b")
        wrap.columnconfigure(1, weight=2, uniform="b")

        steps = tk.Frame(wrap, bg=CARD, padx=px(22), pady=px(20))
        steps.grid(row=0, column=0, sticky="nsew", padx=(0, px(20)))
        tk.Label(steps, text="Dough making instructions", bg=CARD, fg=FG,
                 font=(FONT, 14, "bold")).pack(anchor="w", pady=(0, px(10)))
        for i, step in enumerate(INSTRUCTIONS, 1):
            row = tk.Frame(steps, bg=CARD)
            row.pack(fill="x", pady=px(6))
            tk.Label(row, text=f"{i:02d}", bg=CARD, fg=ACCENT, font=(FONT, 11, "bold"),
                     width=3, anchor="w").pack(side="left")
            tk.Label(row, text=step, bg=CARD, fg=FG, font=(FONT, 11),
                     anchor="w").pack(side="left")
            if i < len(INSTRUCTIONS):
                tk.Frame(steps, bg=TRACK, height=1).pack(fill="x")

        bake = tk.Frame(wrap, bg=CARD, padx=px(22), pady=px(20))
        bake.grid(row=0, column=1, sticky="nsew")
        tk.Label(bake, text="Oven & bake notes", bg=CARD, fg=FG,
                 font=(FONT, 14, "bold")).pack(anchor="w", pady=(0, px(10)))
        grid = tk.Frame(bake, bg=CARD)
        grid.pack(fill="x")
        for c, h in enumerate(["THICKNESS", "TEMP", "TIME"]):
            grid.columnconfigure(c, weight=1, uniform="bk")
            tk.Label(grid, text=h, bg=CARD, fg=MUTED, font=(FONT, 9, "bold"),
                     anchor="w").grid(row=0, column=c, sticky="ew", pady=(0, px(4)))
        self.bake_labels = {}
        for r, (name, (temp, mins)) in enumerate(BAKE.items(), 1):
            labs = [tk.Label(grid, text=t, font=(FONT, 11, "bold"), anchor="w",
                             padx=px(6), pady=px(7))
                    for t in (name.title(), temp, mins)]
            for c, lab in enumerate(labs):
                lab.grid(row=r, column=c, sticky="ew")
            self.bake_labels[name] = labs
        tk.Label(bake, text=BAKE_NOTE, bg=CARD, fg=MUTED, font=(FONT, 10),
                 wraplength=px(330), justify="left").pack(anchor="w", pady=(px(12), 0))

    def _paint_bake(self):
        for name, labs in self.bake_labels.items():
            on = name == self.thick
            for lab in labs:
                lab.config(bg=ACCENT if on else CARD, fg=ACCENT_FG if on else FG)

    def _set_size(self, v): self.size = v; self.update()
    def _set_count(self, v): self.count = v; self.update()
    def _set_thick(self, v): self.thick = v; self.update()
    def _set_gf(self, v): self.gf = v; self.update()

    def update(self):
        r = self.recipe = calculate(self.size, self.count, self.thick, self.gf)
        self.size_lbl.config(text=f'{r.size}"')
        self.count_lbl.config(text=str(r.count))
        self.tiles["ball"].config(text=str(r.ball_g))
        self.tiles["flour"].config(text=str(r.flour_g))
        self.tiles["water"].config(text=str(r.water_g))
        self.tiles["hyd"].config(text=str(r.hydration_pct))
        self.kind_lbl.config(text=f"{r.kind()}  ·  Cold ferment 2–4 days")
        self.meta_lbl.config(text=r.meta())
        self._paint_bake()
        for w in self.table.winfo_children():
            w.destroy()
        for c, h in enumerate(["INGREDIENT", "AMOUNT", "BAKER'S %"]):
            tk.Label(self.table, text=h, bg=CARD, fg=MUTED, font=(FONT, 9, "bold"),
                     anchor="w" if c == 0 else "e", width=0 if c == 0 else 12
                     ).grid(row=0, column=c, sticky="ew", pady=(px(0), px(4)))
        for i, (name, amt, pct) in enumerate(r.rows(), 1):
            tk.Frame(self.table, bg=TRACK, height=1).grid(row=2 * i - 1, column=0,
                                                          columnspan=3, sticky="ew")
            tk.Label(self.table, text=name, bg=CARD, fg=FG, font=(FONT, 11),
                     anchor="w").grid(row=2 * i, column=0, sticky="ew", pady=px(6))
            tk.Label(self.table, text=amt, bg=CARD, fg=ACCENT, font=(FONT, 11, "bold"),
                     anchor="e", width=12).grid(row=2 * i, column=1, sticky="e")
            tk.Label(self.table, text=pct, bg=CARD, fg=MUTED, font=(FONT, 11),
                     anchor="e", width=12).grid(row=2 * i, column=2, sticky="e")

    def copy(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.recipe.text())
        self.copy_btn.config(text="Copied ✓")
        self.root.after(1500, lambda: self.copy_btn.config(text="Copy recipe"))

    def save(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="dough_recipe.txt",
                                            filetypes=[("Text file", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.recipe.text() + "\n\nInstructions:\n"
                        + "\n".join(f"{i:02d} {s}" for i, s in enumerate(INSTRUCTIONS, 1))
                        + f"\n\nBake ({self.thick}): {BAKE[self.thick][0]}, {BAKE[self.thick][1]}\n")


def run_gui():
    global S
    if tk is None:
        raise SystemExit("Tkinter is not installed. On Debian/Ubuntu: sudo apt install python3-tk")
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    dpi = root.winfo_fpixels("1i")
    S = max(1.0, dpi / 96.0)
    root.tk.call("tk", "scaling", dpi / 72.0)
    App(root)
    root.mainloop()


def main():
    p = argparse.ArgumentParser(description="Dough calculator")
    p.add_argument("--cli", action="store_true", help="print a recipe instead of opening the GUI")
    p.add_argument("--size", type=int, default=16, help="inches (10-20)")
    p.add_argument("--count", type=int, default=6, help="number of pizzas (1-10)")
    p.add_argument("--thickness", choices=list(GRAMS_PER_SQ_IN), default="regular")
    p.add_argument("--gf", action="store_true", help="gluten free")
    a = p.parse_args()
    if a.cli:
        print(calculate(a.size, a.count, a.thickness, a.gf).text())
        return
    run_gui()


if __name__ == "__main__":
    main()
