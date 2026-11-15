"""Tiny dependency-free PDF writer (vector shapes + Helvetica text).

Coordinates are in points (72 per inch) with the origin at the TOP-LEFT of
the page and y growing downward, which is easier for layout code.
"""

from __future__ import annotations

import zlib

LETTER = (612.0, 792.0)

# Standard Helvetica AFM widths for ASCII 32..126 (per 1000 em)
_HELV = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
         556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
         1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
         667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
         333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
         556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]
_HELV_B = [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
           556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
           975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
           667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
           333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
           611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584]

FONTS = {
    "F1": ("Helvetica", _HELV),
    "F2": ("Helvetica-Bold", _HELV_B),
    "F3": ("Helvetica-Oblique", _HELV),
    "F4": ("Helvetica-BoldOblique", _HELV_B),
}
KAPPA = 0.5522847498

# Extra WinAnsiEncoding widths (per 1000 em) for typography symbols
_EXTRA_WIDTHS = {
    "\u2013": (556, 556),    # en-dash
    "\u2014": (1000, 1000),  # em-dash
    "\u2018": (222, 278),    # left single quote
    "\u2019": (222, 278),    # right single quote
    "\u201c": (333, 474),    # left double quote
    "\u201d": (333, 474),    # right double quote
    "\u2022": (350, 350),    # bullet
    "\u2122": (1000, 1000),  # trademark sign
    "\u00d7": (584, 584),    # multiplication sign
}


def text_width(s: str, size: float, bold: bool = False) -> float:
    table = _HELV_B if bold else _HELV
    w = 0
    for ch in s:
        o = ord(ch)
        if 32 <= o <= 126:
            w += table[o - 32]
        elif ch in _EXTRA_WIDTHS:
            w += _EXTRA_WIDTHS[ch][1 if bold else 0]
        else:
            w += 556
    return w * size / 1000.0


def wrap(s: str, size: float, width: float, bold: bool = False) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if text_width(trial, size, bold) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _esc(s: str) -> str:
    raw = s.encode("cp1252", "replace")
    out = []
    for b in raw:
        if b == 0x5C:
            out.append("\\\\")
        elif b == 0x28:
            out.append("\\(")
        elif b == 0x29:
            out.append("\\)")
        elif 32 <= b <= 126:
            out.append(chr(b))
        else:
            out.append(f"\\{b:03o}")
    return "".join(out)


def _rgb(c):
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[k:k + 2], 16) / 255.0 for k in (0, 2, 4))
    return c


class Page:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.ops: list[str] = []

    # -- state -------------------------------------------------------------
    def _y(self, y):
        return self.h - y

    def save(self):
        self.ops.append("q")

    def restore(self):
        self.ops.append("Q")

    def stroke_color(self, c):
        r, g, b = _rgb(c)
        self.ops.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def fill_color(self, c):
        r, g, b = _rgb(c)
        self.ops.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def line_width(self, w):
        self.ops.append(f"{w:.2f} w")

    def dash(self, on=0, off=0):
        self.ops.append(f"[{on} {off}] 0 d" if on else "[] 0 d")

    def line_cap(self, cap):
        self.ops.append(f"{cap} J")

    # -- paths -------------------------------------------------------------
    def _paint(self, fill, stroke):
        self.ops.append("B" if fill and stroke else "f" if fill else "S")

    def line(self, x1, y1, x2, y2):
        self.ops.append(f"{x1:.2f} {self._y(y1):.2f} m {x2:.2f} {self._y(y2):.2f} l S")

    def rect(self, x, y, w, h, fill=False, stroke=True):
        self.ops.append(f"{x:.2f} {self._y(y + h):.2f} {w:.2f} {h:.2f} re")
        self._paint(fill, stroke)

    def round_rect(self, x, y, w, h, r, fill=False, stroke=True):
        r = min(r, w / 2, h / 2)
        k = r * KAPPA
        Y = self._y
        o = self.ops
        o.append(f"{x + r:.2f} {Y(y):.2f} m")
        o.append(f"{x + w - r:.2f} {Y(y):.2f} l")
        o.append(f"{x + w - r + k:.2f} {Y(y):.2f} {x + w:.2f} {Y(y + r - k):.2f} {x + w:.2f} {Y(y + r):.2f} c")
        o.append(f"{x + w:.2f} {Y(y + h - r):.2f} l")
        o.append(f"{x + w:.2f} {Y(y + h - r + k):.2f} {x + w - r + k:.2f} {Y(y + h):.2f} {x + w - r:.2f} {Y(y + h):.2f} c")
        o.append(f"{x + r:.2f} {Y(y + h):.2f} l")
        o.append(f"{x + r - k:.2f} {Y(y + h):.2f} {x:.2f} {Y(y + h - r + k):.2f} {x:.2f} {Y(y + h - r):.2f} c")
        o.append(f"{x:.2f} {Y(y + r):.2f} l")
        o.append(f"{x:.2f} {Y(y + r - k):.2f} {x + r - k:.2f} {Y(y):.2f} {x + r:.2f} {Y(y):.2f} c h")
        self._paint(fill, stroke)

    def circle(self, cx, cy, r, fill=False, stroke=True):
        k = r * KAPPA
        Y = self._y
        o = self.ops
        o.append(f"{cx + r:.2f} {Y(cy):.2f} m")
        o.append(f"{cx + r:.2f} {Y(cy + k):.2f} {cx + k:.2f} {Y(cy + r):.2f} {cx:.2f} {Y(cy + r):.2f} c")
        o.append(f"{cx - k:.2f} {Y(cy + r):.2f} {cx - r:.2f} {Y(cy + k):.2f} {cx - r:.2f} {Y(cy):.2f} c")
        o.append(f"{cx - r:.2f} {Y(cy - k):.2f} {cx - k:.2f} {Y(cy - r):.2f} {cx:.2f} {Y(cy - r):.2f} c")
        o.append(f"{cx + k:.2f} {Y(cy - r):.2f} {cx + r:.2f} {Y(cy - k):.2f} {cx + r:.2f} {Y(cy):.2f} c h")
        self._paint(fill, stroke)

    def polygon(self, pts, fill=False, stroke=True):
        first = True
        for x, y in pts:
            self.ops.append(f"{x:.2f} {self._y(y):.2f} {'m' if first else 'l'}")
            first = False
        self.ops.append("h")
        self._paint(fill, stroke)

    # -- text --------------------------------------------------------------
    def text(self, x, y, s, size=10, bold=False, align="left", color=None, italic=False):
        """Draw text with its BASELINE at y."""
        if color is not None:
            self.fill_color(color)
        w = text_width(s, size, bold)
        if align == "center":
            x -= w / 2
        elif align == "right":
            x -= w
        font = ("F4" if bold else "F3") if italic else ("F2" if bold else "F1")
        self.ops.append(f"BT /{font} {size:.2f} Tf {x:.2f} {self._y(y):.2f} Td ({_esc(s)}) Tj ET")

    def text_centered_in(self, cx, cy, s, size, bold=True, color=None):
        """Center text both ways on (cx, cy) using cap-height approximation."""
        self.text(cx, cy + size * 0.36, s, size, bold, "center", color)

    def paragraph(self, x, y, s, size, width, bold=False, leading=1.25, color=None, italic=False):
        """Wrapped text; returns the y below the last line."""
        for ln in wrap(s, size, width, bold):
            y += size * leading
            self.text(x, y - size * (leading - 1.0) - 0.0, ln, size, bold, color=color, italic=italic)
        return y

    def rich_paragraph(self, x, y, spans, size, width, leading=1.24, default_color="#222222"):
        """Wrap and draw mixed-style inline spans [(text, bold, italic, color), ...].
        Returns the y below the last line.
        """
        tokens = []
        for sp in spans:
            txt = sp[0]
            bold = sp[1] if len(sp) > 1 else False
            italic = sp[2] if len(sp) > 2 else False
            color = (sp[3] if len(sp) > 3 and sp[3] is not None else default_color)
            for w in txt.split():
                tokens.append((w, bold, italic, color))
        if not tokens:
            return y

        lines = []
        cur_line = []
        cur_w = 0.0
        space_w = text_width(" ", size, False)
        for w, bold, italic, color in tokens:
            ww = text_width(w, size, bold)
            needed = ww if not cur_line else (cur_w + space_w + ww)
            if needed <= width or not cur_line:
                cur_line.append((w, bold, italic, color, ww))
                cur_w = needed
            else:
                lines.append(cur_line)
                cur_line = [(w, bold, italic, color, ww)]
                cur_w = ww
        if cur_line:
            lines.append(cur_line)

        for ln in lines:
            y += size * leading
            baseline = y - size * (leading - 1.0)
            cx = x
            for idx, (w, bold, italic, color, ww) in enumerate(ln):
                if idx > 0:
                    cx += space_w
                self.text(cx, baseline, w, size, bold=bold, color=color, italic=italic)
                cx += ww
        return y


class PDF:
    def __init__(self, size=LETTER, title="Document"):
        self.size = size
        self.title = title
        self.pages: list[Page] = []

    def new_page(self) -> Page:
        p = Page(*self.size)
        self.pages.append(p)
        return p

    def save(self, path):
        objs: list[bytes] = []

        def add(b) -> int:
            objs.append(b if isinstance(b, bytes) else b.encode("latin-1"))
            return len(objs)

        cat_id = add("")  # placeholder
        pages_id = add("")
        font_ids = {}
        for key, (name, _) in FONTS.items():
            font_ids[key] = add(f"<< /Type /Font /Subtype /Type1 /BaseFont /{name} "
                                f"/Encoding /WinAnsiEncoding >>")
        res = "<< /Font << " + " ".join(f"/{k} {v} 0 R" for k, v in font_ids.items()) + " >> >>"
        page_ids = []
        for pg in self.pages:
            data = zlib.compress("\n".join(pg.ops).encode("latin-1"))
            cid = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(data) + data + b"\nendstream")
            pid = add(f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {pg.w:.0f} {pg.h:.0f}] "
                      f"/Resources {res} /Contents {cid} 0 R >>")
            page_ids.append(pid)
        objs[pages_id - 1] = (f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] "
                              f"/Count {len(page_ids)} >>").encode()
        objs[cat_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
        info_id = add(f"<< /Title ({_esc(self.title)}) /Producer (sudoku4) >>")

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for n, ob in enumerate(objs, 1):
            offsets.append(len(out))
            out += f"{n} 0 obj\n".encode() + ob + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
        for off in offsets:
            out += f"{off:010d} 00000 n \n".encode()
        out += (f"trailer\n<< /Size {len(objs) + 1} /Root {cat_id} 0 R /Info {info_id} 0 R >>\n"
                f"startxref\n{xref}\n%%EOF\n").encode()
        with open(path, "wb") as f:
            f.write(out)

