"""
visuals.py -- Component 5: Publication figures & GPU spreading GIF generator.

Generates all 6 static 300-DPI publication figures (PNG + vector PDF) plus the
side-by-side GPU die-spreading animation (`figures/gpu_spread.gif`).

Uses a crisp, dependency-free SVG -> rsvg-convert pipeline for vector PDFs and
300-DPI PNGs, and a 2x supersampled Pillow canvas for the animated GIF.
All physics arrays come directly from `params.py`, `rheology_models.py`,
`thermal_coupling.py`, and `diagnostics.py` (strict one-way pipeline).
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import diagnostics as dg
import rheology_models as rm
import thermal_coupling as tc
from params import (BINGHAM, DROPLET, GPU_700W, MOUNT_TIME, NEWTONIAN,
                    SHEAR_THICKENING, SHEAR_THINNING, THERMAL, Bingham,
                    DropletSpec, GPUSpec, Newtonian, PowerLaw, replace)

__all__ = [
    "FIGURES_DIR",
    "fig1_velocity_stress",
    "fig2_pressure_coverage",
    "fig3_thickness_radius",
    "fig4_bingham_plug_map",
    "fig5_gpu_thermal_design_map",
    "fig6_regime_validity",
    "generate_gpu_spread_gif",
    "generate_all_visuals",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"

# Colorblind-safe Okabe-Ito / publication palette
PALETTE = {
    "n04": "#0072B2",      # deep blue
    "n07": "#56B4E9",      # sky blue
    "newt": "#111111",     # black (Newtonian reference)
    "n13": "#E69F00",      # amber / orange
    "bing250": "#009E73",  # teal green
    "bing5k": "#D55E00",   # vermilion red (high-yield stall)
    "plug": "#F0E442",     # soft gold highlight
    "die": "#2B3A4A",      # slate
    "grid": "#E2E6EC",     # light grid
    "axis": "#1F2933",     # dark charcoal
    "muted": "#616E7C",
    "danger": "#C81E1E",
    "ok": "#0E7C5B",
}


# =========================================================================== #
# Lightweight publication SVG canvas + rsvg-convert (vector PDF + 300 DPI PNG)
# =========================================================================== #
def _esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class SVGFigure:
    """Publication-quality vector SVG builder with axes, math-like labels, and colormaps."""

    def __init__(self, width_in: float = 11.0, height_in: float = 4.6, bg: str = "#FFFFFF"):
        self.width_in = width_in
        self.height_in = height_in
        self.w = width_in * 100.0
        self.h = height_in * 100.0
        self.bg = bg
        self.defs: List[str] = []
        self.items: List[str] = []

    def add(self, raw: str) -> None:
        self.items.append(raw)

    def rect(self, x: float, y: float, w: float, h: float, fill: str = "none",
             stroke: str = "none", sw: float = 1.0, rx: float = 0.0,
             opacity: float = 1.0, dash: str = "") -> None:
        d_attr = f' stroke-dasharray="{dash}"' if dash else ""
        op_attr = f' opacity="{opacity:.3f}"' if opacity < 1.0 else ""
        rx_attr = f' rx="{rx:.2f}"' if rx > 0 else ""
        self.add(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.2f}"{rx_attr}{d_attr}{op_attr}/>'
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = "#000",
             sw: float = 1.2, dash: str = "", opacity: float = 1.0) -> None:
        d_attr = f' stroke-dasharray="{dash}"' if dash else ""
        op_attr = f' opacity="{opacity:.3f}"' if opacity < 1.0 else ""
        self.add(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linecap="round"{d_attr}{op_attr}/>'
        )

    def circle(self, cx: float, cy: float, r: float, fill: str = "none",
               stroke: str = "none", sw: float = 1.2, dash: str = "",
               opacity: float = 1.0) -> None:
        d_attr = f' stroke-dasharray="{dash}"' if dash else ""
        op_attr = f' opacity="{opacity:.3f}"' if opacity < 1.0 else ""
        self.add(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw:.2f}"{d_attr}{op_attr}/>'
        )

    def polyline(self, pts: Sequence[Tuple[float, float]], stroke: str = "#000",
                 sw: float = 2.0, dash: str = "", fill: str = "none",
                 opacity: float = 1.0) -> None:
        if len(pts) < 2:
            return
        coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        d_attr = f' stroke-dasharray="{dash}"' if dash else ""
        op_attr = f' opacity="{opacity:.3f}"' if opacity < 1.0 else ""
        self.add(
            f'<polyline points="{coords}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw:.2f}" stroke-linejoin="round" stroke-linecap="round"{d_attr}{op_attr}/>'
        )

    def polygon(self, pts: Sequence[Tuple[float, float]], fill: str = "#000",
                stroke: str = "none", sw: float = 1.0, opacity: float = 1.0) -> None:
        if len(pts) < 3:
            return
        coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        op_attr = f' opacity="{opacity:.3f}"' if opacity < 1.0 else ""
        self.add(
            f'<polygon points="{coords}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw:.2f}"{op_attr}/>'
        )

    def text(self, x: float, y: float, txt: str, size: float = 11.0,
             fill: str = "#1F2933", anchor: str = "middle", weight: str = "normal",
             italic: bool = False, rotate: float = 0.0, family: str = "DejaVu Sans") -> None:
        style = "italic" if italic else "normal"
        tf = f' transform="rotate({rotate:.1f} {x:.2f} {y:.2f})"' if rotate != 0.0 else ""
        self.add(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}, sans-serif" '
            f'font-size="{size:.2f}" font-weight="{weight}" font-style="{style}" '
            f'fill="{fill}" text-anchor="{anchor}" dominant-baseline="central"{tf}>{_esc(txt)}</text>'
        )

    def save(self, stem: Path) -> Tuple[Path, Path]:
        """Write vector PDF and 300-DPI PNG via rsvg-convert or matplotlib SVG renderer."""
        stem.parent.mkdir(parents=True, exist_ok=True)
        svg_str = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width_in:.3f}in" height="{self.height_in:.3f}in" '
            f'viewBox="0 0 {self.w:.2f} {self.h:.2f}">\n'
            f'<defs>{"".join(self.defs)}</defs>\n'
            f'<rect x="0" y="0" width="{self.w:.2f}" height="{self.h:.2f}" fill="{self.bg}"/>\n'
            + "\n".join(self.items)
            + "\n</svg>\n"
        )
        png_path = stem.with_suffix(".png")
        pdf_path = stem.with_suffix(".pdf")
        if shutil.which("rsvg-convert"):
            tmp_svg = stem.with_suffix(".tmp.svg")
            tmp_svg.write_text(svg_str, encoding="utf-8")
            try:
                px_w = int(round(self.width_in * 300))
                px_h = int(round(self.height_in * 300))
                subprocess.run(
                    ["rsvg-convert", "-f", "png", "-d", "300", "-p", "300",
                     "-w", str(px_w), "-h", str(px_h), "-o", str(png_path), str(tmp_svg)],
                    check=True,
                )
                subprocess.run(
                    ["rsvg-convert", "-f", "pdf", "-o", str(pdf_path), str(tmp_svg)],
                    check=True,
                )
                with Image.open(png_path) as im:
                    im.save(png_path, dpi=(300, 300))
            finally:
                if tmp_svg.exists():
                    tmp_svg.unlink()
        else:
            self._save_via_matplotlib(png_path, pdf_path)
        return png_path, pdf_path

    def _save_via_matplotlib(self, png_path: Path, pdf_path: Path) -> None:
        """Render the exact SVG primitives to vector PDF and 300-DPI PNG via matplotlib."""
        import re
        import xml.etree.ElementTree as ET
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

        root = ET.fromstring(
            f'<svg width="{self.w}" height="{self.h}">'
            + "".join(self.items)
            + "</svg>"
        )
        fig = plt.figure(figsize=(self.width_in, self.height_in), dpi=300, facecolor=self.bg)
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], frameon=False)
        ax.set_xlim(0.0, self.w)
        ax.set_ylim(self.h, 0.0)
        ax.set_aspect("equal")
        ax.axis("off")

        PT = 72.0 / 100.0  # 1 SVG unit = 1/100 inch = 0.72 pt

        def _ls(dash: str, sw_pt: float):
            if not dash:
                return "-"
            parts = [max(float(v) * PT / max(sw_pt, 0.5), 0.5) for v in dash.split(",") if v.strip()]
            return (0, tuple(parts))

        for el in root:
            tag = el.tag
            op = float(el.attrib.get("opacity", "1.0"))
            fill = el.attrib.get("fill", "none")
            stroke = el.attrib.get("stroke", "none")
            sw = float(el.attrib.get("stroke-width", "1.0")) * PT
            dash = el.attrib.get("stroke-dasharray", "")
            fc = "none" if fill == "none" else fill
            ec = "none" if stroke == "none" else stroke

            if tag == "rect":
                x = float(el.attrib["x"])
                y = float(el.attrib["y"])
                w = float(el.attrib["width"])
                h = float(el.attrib["height"])
                rx = float(el.attrib.get("rx", "0.0"))
                if rx > 0:
                    p = FancyBboxPatch(
                        (x, y), w, h,
                        boxstyle=f"round,pad=0,rounding_size={rx}",
                        facecolor=fc, edgecolor=ec, linewidth=sw,
                        linestyle=_ls(dash, sw), alpha=op,
                    )
                else:
                    p = Rectangle(
                        (x, y), w, h,
                        facecolor=fc, edgecolor=ec, linewidth=sw,
                        linestyle=_ls(dash, sw), alpha=op,
                    )
                ax.add_patch(p)
            elif tag == "line":
                x1, y1 = float(el.attrib["x1"]), float(el.attrib["y1"])
                x2, y2 = float(el.attrib["x2"]), float(el.attrib["y2"])
                ax.plot(
                    [x1, x2], [y1, y2],
                    color=ec if ec != "none" else "#000000",
                    linewidth=sw, linestyle=_ls(dash, sw),
                    alpha=op, solid_capstyle="round",
                )
            elif tag == "circle":
                cx, cy, r = float(el.attrib["cx"]), float(el.attrib["cy"]), float(el.attrib["r"])
                c = Circle(
                    (cx, cy), r,
                    facecolor=fc, edgecolor=ec, linewidth=sw,
                    linestyle=_ls(dash, sw), alpha=op,
                )
                ax.add_patch(c)
            elif tag == "polyline":
                pts = [tuple(map(float, pair.split(","))) for pair in el.attrib["points"].split() if "," in pair]
                if len(pts) >= 2:
                    xs, ys = zip(*pts)
                    ax.plot(
                        xs, ys,
                        color=ec if ec != "none" else "#000000",
                        linewidth=sw, linestyle=_ls(dash, sw),
                        alpha=op, solid_capstyle="round", solid_joinstyle="round",
                    )
            elif tag == "polygon":
                pts = [tuple(map(float, pair.split(","))) for pair in el.attrib["points"].split() if "," in pair]
                if len(pts) >= 3:
                    poly = Polygon(
                        pts, closed=True,
                        facecolor=fc, edgecolor=ec, linewidth=sw, alpha=op,
                    )
                    ax.add_patch(poly)
            elif tag == "text":
                x, y = float(el.attrib["x"]), float(el.attrib["y"])
                sz = float(el.attrib.get("font-size", "11.0")) * PT
                wt = el.attrib.get("font-weight", "normal")
                st = el.attrib.get("font-style", "normal")
                col = el.attrib.get("fill", "#1F2933")
                anc = el.attrib.get("text-anchor", "middle")
                ha = {"start": "left", "middle": "center", "end": "right"}.get(anc, "center")
                tf = el.attrib.get("transform", "")
                rot = 0.0
                m = re.search(r"rotate\(([-\d.]+)", tf)
                if m:
                    rot = -float(m.group(1))
                ax.text(
                    x, y, el.text or "",
                    fontsize=sz, fontweight=wt, fontstyle=st, color=col,
                    ha=ha, va="center", rotation=rot, rotation_mode="anchor",
                    family="DejaVu Sans",
                )

        fig.savefig(pdf_path, format="pdf")
        fig.savefig(png_path, format="png", dpi=300)
        plt.close(fig)


class PlotBox:
    """2D Cartesian or log-scaled plot panel embedded inside an SVGFigure."""

    def __init__(self, fig: SVGFigure, x: float, y: float, w: float, h: float,
                 xlim: Tuple[float, float], ylim: Tuple[float, float],
                 xscale: str = "linear", yscale: str = "linear"):
        self.fig = fig
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xlim = xlim
        self.ylim = ylim
        self.xscale = xscale
        self.yscale = yscale

    def _tx(self, v: float) -> float:
        x0, x1 = self.xlim
        if self.xscale == "log":
            u = (math.log10(max(v, 1e-300)) - math.log10(x0)) / (math.log10(x1) - math.log10(x0))
        else:
            u = (v - x0) / (x1 - x0)
        return self.x + u * self.w

    def _ty(self, v: float) -> float:
        y0, y1 = self.ylim
        if self.yscale == "log":
            u = (math.log10(max(v, 1e-300)) - math.log10(y0)) / (math.log10(y1) - math.log10(y0))
        else:
            u = (v - y0) / (y1 - y0)
        return self.y + self.h - u * self.h

    def pts(self, xs, ys) -> List[Tuple[float, float]]:
        out = []
        x0, x1 = min(self.xlim), max(self.xlim)
        y0, y1 = min(self.ylim), max(self.ylim)
        for xv, yv in zip(xs, ys):
            if not (np.isfinite(xv) and np.isfinite(yv)):
                continue
            if self.xscale == "log" and xv <= 0:
                continue
            if self.yscale == "log" and yv <= 0:
                continue
            xc = min(max(float(xv), x0), x1)
            yc = min(max(float(yv), y0), y1)
            out.append((self._tx(xc), self._ty(yc)))
        return out

    def draw_frame(self, xticks: Sequence[Tuple[float, str]],
                   yticks: Sequence[Tuple[float, str]],
                   xlabel: str = "", ylabel: str = "", title: str = "",
                   subtitle: str = "", grid: bool = True,
                   fill_bg: bool = True, ylabel_offset: float = 43.0) -> None:
        if fill_bg:
            self.fig.rect(self.x, self.y, self.w, self.h, fill="#FAFBFD", stroke="none")
        if grid:
            for xv, _ in xticks:
                px = self._tx(xv)
                if self.x <= px <= self.x + self.w:
                    self.fig.line(px, self.y, px, self.y + self.h, stroke=PALETTE["grid"], sw=0.8)
            for yv, _ in yticks:
                py = self._ty(yv)
                if self.y <= py <= self.y + self.h:
                    self.fig.line(self.x, py, self.x + self.w, py, stroke=PALETTE["grid"], sw=0.8)
        self.fig.rect(self.x, self.y, self.w, self.h, fill="none", stroke=PALETTE["axis"], sw=1.3)

        for xv, lab in xticks:
            px = self._tx(xv)
            if self.x - 1 <= px <= self.x + self.w + 1:
                self.fig.line(px, self.y + self.h, px, self.y + self.h + 4.5, stroke=PALETTE["axis"], sw=1.1)
                self.fig.text(px, self.y + self.h + 14.0, lab, size=10.0, fill=PALETTE["axis"])

        for yv, lab in yticks:
            py = self._ty(yv)
            if self.y - 1 <= py <= self.y + self.h + 1:
                self.fig.line(self.x - 4.5, py, self.x, py, stroke=PALETTE["axis"], sw=1.1)
                self.fig.text(self.x - 8.0, py, lab, size=10.0, fill=PALETTE["axis"], anchor="end")

        if xlabel:
            self.fig.text(self.x + 0.5 * self.w, self.y + self.h + 33.0, xlabel,
                          size=11.5, weight="bold", fill=PALETTE["axis"])
        if ylabel:
            self.fig.text(self.x - ylabel_offset, self.y + 0.5 * self.h, ylabel,
                          size=11.5, weight="bold", fill=PALETTE["axis"], rotate=-90)
        if title:
            self.fig.text(self.x + 0.5 * self.w, self.y - (24.0 if subtitle else 15.0),
                          title, size=12.5, weight="bold", fill=PALETTE["axis"])
        if subtitle:
            self.fig.text(self.x + 0.5 * self.w, self.y - 9.0,
                          subtitle, size=9.8, fill=PALETTE["muted"])

    def plot(self, xs, ys, color: str = "#000", sw: float = 2.2, dash: str = "",
             opacity: float = 1.0) -> None:
        self.fig.polyline(self.pts(xs, ys), stroke=color, sw=sw, dash=dash, opacity=opacity)

    def hline(self, yv: float, color: str = "#000", sw: float = 1.3, dash: str = "5,4") -> None:
        py = self._ty(yv)
        if self.y <= py <= self.y + self.h:
            self.fig.line(self.x, py, self.x + self.w, py, stroke=color, sw=sw, dash=dash)

    def vline(self, xv: float, color: str = "#000", sw: float = 1.3, dash: str = "5,4") -> None:
        px = self._tx(xv)
        if self.x <= px <= self.x + self.w:
            self.fig.line(px, self.y, px, self.y + self.h, stroke=color, sw=sw, dash=dash)

    def legend(self, entries: Sequence[Tuple[str, str, str]], lx: float, ly: float,
               row_h: float = 15.5, box_w: float = 165.0) -> None:
        bh = len(entries) * row_h + 10.0
        self.fig.rect(lx, ly, box_w, bh, fill="#FFFFFF", stroke="#CBD2D9", sw=0.9, rx=4.0, opacity=0.95)
        for i, (lab, col, dash) in enumerate(entries):
            cy = ly + 11.0 + i * row_h
            self.fig.line(lx + 9.0, cy, lx + 30.0, cy, stroke=col, sw=2.3, dash=dash)
            self.fig.text(lx + 36.0, cy, lab, size=9.6, anchor="start", fill=PALETTE["axis"])


# =========================================================================== #
# Figure 1: Velocity u_r(z/h) & Shear-Stress tau_rz(z/h) gallery
# =========================================================================== #
def fig1_velocity_stress(out_dir: Path = FIGURES_DIR) -> Tuple[Path, Path]:
    """Fig 1: Normalised velocity u_r/<u_r> and shear stress tau_rz(z/h) across
    n = 0.4, 0.7, 1.0, 1.3 and Bingham (shaded plug core)."""
    fig = SVGFigure(width_in=11.0, height_in=4.7)
    fig.text(550, 18, "Figure 1 — Gap-wise Velocity & Shear-Stress Profiles Across Constitutive Models",
             size=14.0, weight="bold")

    h = 120e-6
    R = rm.wetted_radius(h, DROPLET.V0, GPU_700W.R_die)
    r_eval = 0.6 * R
    z = np.linspace(0.0, h, 401)
    zh = z / h

    b_vis = Bingham(mu_p=100.0, tau_y=250.0)
    S_target = (1.0 - 0.40) ** 2 * (2.0 + 0.40) / (2.0 * 0.40)
    W_ref = S_target * b_vis.tau_y * h**2 / (3.0 * b_vis.mu_p * r_eval)
    u_mean = r_eval * W_ref / (2.0 * h)

    models = [
        (PowerLaw(K=100.0, n=0.4), "Power-law n = 0.4 (strong thinning)", PALETTE["n04"], ""),
        (PowerLaw(K=100.0, n=0.7), "Power-law n = 0.7 (mild thinning)", PALETTE["n07"], "6,3"),
        (NEWTONIAN, "Newtonian n = 1.0 (Stefan parabola)", PALETTE["newt"], ""),
        (PowerLaw(K=100.0, n=1.3), "Power-law n = 1.3 (shear-thickening)", PALETTE["n13"], "2,2.5"),
        (b_vis, "Bingham (plug fraction 2z₀/h = 0.40)", PALETTE["bing250"], ""),
    ]

    ax1 = PlotBox(fig, x=75, y=68, w=430, h=335, xlim=(0.0, 1.75), ylim=(0.0, 1.0))
    y_top = ax1._ty(0.70)
    y_bot = ax1._ty(0.30)
    ax1.draw_frame(
        xticks=[(0.0, "0.0"), (0.5, "0.5"), (1.0, "1.0"), (1.5, "1.5")],
        yticks=[(0.0, "0.0"), (0.25, "0.25"), (0.5, "0.50"), (0.75, "0.75"), (1.0, "1.00")],
        xlabel="Normalised radial velocity  u_r(r, z) / ⟨u_r⟩",
        ylabel="Normalised gap coordinate  z / h",
        title="(a) Radial Velocity Profile Across Gap",
        subtitle="Same local volumetric flux  q_r = r(−dh/dt)/2  at  r = 0.6 R",
    )
    fig.rect(ax1.x + 1, y_top, ax1.w - 2, y_bot - y_top, fill=PALETTE["plug"], opacity=0.23)
    ax1.hline(0.30, color=PALETTE["bing250"], sw=1.1, dash="4,3")
    ax1.hline(0.70, color=PALETTE["bing250"], sw=1.1, dash="4,3")
    fig.text(ax1._tx(0.62), 0.5 * (y_top + y_bot),
             "Bingham unyielded plug core  |τ_rz| ≤ τ_y  (∂u_r/∂z = 0)",
             size=9.2, weight="bold", fill="#065F46")

    for fl, _, col, dash in models:
        u = rm.velocity(r_eval, z, h, W_ref, fl) / u_mean
        ax1.plot(u, zh, color=col, sw=2.4 if fl is b_vis or fl is NEWTONIAN else 2.0, dash=dash)

    ax1.legend([(lab, col, dash) for _, lab, col, dash in models],
               lx=ax1.x + 10, ly=ax1.y + 8, row_h=14.8, box_w=230)

    ax2 = PlotBox(fig, x=595, y=68, w=455, h=335, xlim=(-3.0, 3.0), ylim=(0.0, 1.0))
    ax2.draw_frame(
        xticks=[(-3, "−3.0"), (-2, "−2.0"), (-1, "−1.0"), (0, "0.0"),
                (1, "+1.0"), (2, "+2.0"), (3, "+3.0")],
        yticks=[(0.0, "0.0"), (0.25, "0.25"), (0.5, "0.50"), (0.75, "0.75"), (1.0, "1.00")],
        xlabel="Normalised shear stress  τ_rz(r, z) / τ_y   (or τ_rz / τ_w,Newt)",
        ylabel="Normalised gap coordinate  z / h",
        title="(b) Universal Linear Shear-Stress Distribution",
        subtitle="Lubrication momentum balance:  τ_rz = −(−∂p/∂r)(z − h/2)",
    )
    x_m1, x_p1 = ax2._tx(-1.0), ax2._tx(1.0)
    fig.rect(x_m1, ax2.y + 1, x_p1 - x_m1, ax2.h - 2, fill=PALETTE["plug"], opacity=0.23)
    ax2.vline(-1.0, color=PALETTE["bing250"], sw=1.2, dash="4,3")
    ax2.vline(1.0, color=PALETTE["bing250"], sw=1.2, dash="4,3")
    ax2.vline(0.0, color=PALETTE["muted"], sw=0.9, dash="2,2")
    ax2.hline(0.5, color=PALETTE["muted"], sw=0.9, dash="2,2")

    tau_b = rm.shear_stress(r_eval, z, h, W_ref, b_vis) / b_vis.tau_y
    ax2.plot(tau_b, zh, color=PALETTE["bing250"], sw=2.6)

    tau_univ = -2.0 * (zh - 0.5)
    ax2.plot(tau_univ, zh, color=PALETTE["newt"], sw=2.1, dash="6,3")

    fig.circle(ax2._tx(-1.0), ax2._ty(0.70), r=4.2, fill=PALETTE["bing250"], stroke="#FFF", sw=1.2)
    fig.circle(ax2._tx(1.0), ax2._ty(0.30), r=4.2, fill=PALETTE["bing250"], stroke="#FFF", sw=1.2)
    fig.text(ax2._tx(0.0), ax2._ty(0.11), "Yield band  |τ_rz| ≤ τ_y", size=9.5,
             weight="bold", fill="#065F46")
    fig.text(ax2._tx(-1.95), ax2._ty(0.72), "z = h/2 + z₀", size=9.2, fill=PALETTE["bing250"])
    fig.text(ax2._tx(1.95), ax2._ty(0.28), "z = h/2 − z₀", size=9.2, fill=PALETTE["bing250"])

    ax2.legend([
        ("Bingham  τ_rz / τ_y  (wall |τ_w|/τ_y = 2.5)", PALETTE["bing250"], ""),
        ("Universal  τ_rz / τ_w = 1 − 2z/h  (all fluids)", PALETTE["newt"], "6,3"),
    ], lx=ax2.x + 12, ly=ax2.y + 10, row_h=16.0, box_w=255)

    return fig.save(out_dir / "fig1_velocity_stress")


# =========================================================================== #
# Figure 2: Radial pressure p(r) & top-down AI GPU die-coverage schematic
# =========================================================================== #
def fig2_pressure_coverage(out_dir: Path = FIGURES_DIR) -> Tuple[Path, Path]:
    """Fig 2: (a) Radial gauge pressure p(r) showing force-balance equivalence
    and Bingham central cone; (b) Top-down 700 W GPU die coverage schematic."""
    fig = SVGFigure(width_in=11.0, height_in=4.75)
    fig.text(550, 18, "Figure 2 — Radial Pressure Distribution p(r) & 700 W AI GPU Die-Coverage Footprint",
             size=14.0, weight="bold")

    h = 100e-6
    R = float(rm.wetted_radius(h, DROPLET.V0, GPU_700W.R_die))
    p_mean = GPU_700W.F0 / (math.pi * R**2)
    s = np.linspace(0.0, 1.0, 301)
    r = s * R

    b_5k = Bingham(mu_p=100.0, tau_y=5000.0, label="Bingham (τ_y = 5 kPa)")
    p_models = [
        (PowerLaw(K=100.0, n=0.4), "Power-law n = 0.4 (flatter dome)", PALETTE["n04"], ""),
        (PowerLaw(K=100.0, n=0.7), "Power-law n = 0.7", PALETTE["n07"], "6,3"),
        (NEWTONIAN, "Newtonian n = 1.0 (parabolic, p₀/p̄ = 2)", PALETTE["newt"], ""),
        (PowerLaw(K=100.0, n=1.3), "Power-law n = 1.3 (peaked)", PALETTE["n13"], "2,2.5"),
        (BINGHAM, "Bingham τ_y = 250 Pa", PALETTE["bing250"], "5,3"),
        (b_5k, "Bingham τ_y = 5 kPa (conical yield tip)", PALETTE["bing5k"], ""),
    ]

    ax1 = PlotBox(fig, x=75, y=68, w=455, h=340, xlim=(0.0, 1.0), ylim=(0.0, 2.8))
    ax1.draw_frame(
        xticks=[(0.0, "0.0"), (0.2, "0.2"), (0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0")],
        yticks=[(0.0, "0.0"), (0.5, "0.5"), (1.0, "1.0"), (1.5, "1.5"), (2.0, "2.0"), (2.5, "2.5")],
        xlabel="Normalised radial coordinate  r / R(t)",
        ylabel="Normalised gauge pressure  (p − p_∞) / (F₀ / πR²)",
        title="(a) Radial Pressure Profiles at Equal Clamping Load F₀ = 400 N",
        subtitle=f"Instantaneous gap h = 100 μm, R = {R*1e3:.2f} mm, mean pressure p̄ = {p_mean/1e6:.2f} MPa",
    )
    ax1.hline(1.0, color=PALETTE["muted"], sw=1.0, dash="3,3")
    fig.text(ax1._tx(0.24), ax1._ty(1.07), "Mean clamping pressure  p̄ = F₀/(πR²)",
             size=9.0, fill=PALETTE["muted"])

    for fl, _, col, dash in p_models:
        W = float(np.atleast_1d(rm.squeeze_rate(h, fl, GPU_700W.F0, DROPLET.V0, GPU_700W.R_die))[0])
        p_norm = rm.pressure(r, h, R, W, fl) / p_mean
        ax1.plot(s, p_norm, color=col, sw=2.3 if fl in (NEWTONIAN, b_5k) else 1.9, dash=dash)

    fig.text(ax1._tx(0.32), ax1._ty(0.24),
             "All curves satisfy  ∫₀^R (p − p_∞) 2πr dr = F₀ = 400 N",
             size=9.2, weight="bold", fill=PALETTE["axis"])
    ax1.legend([(lab, col, dash) for _, lab, col, dash in p_models],
               lx=ax1.x + 178, ly=ax1.y + 8, row_h=14.5, box_w=268)

    # Panel (b): Top-down AI GPU die-coverage schematic comparing R* vs R_die
    bx, by, bw, bh = 585.0, 68.0, 470.0, 340.0
    fig.rect(bx, by, bw, bh, fill="#FAFBFD", stroke=PALETTE["axis"], sw=1.3)
    fig.text(bx + 0.5 * bw, by - 24.0,
             "(b) Top-Down 700 W AI GPU Die Coverage vs. Bingham Yield Stall",
             size=12.5, weight="bold")
    fig.text(bx + 0.5 * bw, by - 9.0,
             f"A_die = 814 mm² (R_die = {GPU_700W.R_die*1e3:.1f} mm), V₀ = 50 mm³, F₀ = 400 N",
             size=9.8, fill=PALETTE["muted"])

    cx, cy = bx + 165.0, by + 170.0
    scale = 7.8
    r_die_mm = GPU_700W.R_die * 1e3
    r0_mm = DROPLET.R0 * 1e3
    _, r_star_5k, _ = rm.bingham_stall(GPU_700W.F0, 5000.0, DROPLET.V0, GPU_700W.R_die)
    r_star_5k_mm = r_star_5k * 1e3

    pkg_half = 18.2 * scale
    fig.rect(cx - pkg_half, cy - pkg_half, 2 * pkg_half, 2 * pkg_half,
             fill="#E6ECF2", stroke="#829AB1", sw=1.2, rx=6.0)
    fig.circle(cx, cy, r_die_mm * scale, fill="#FEE2E2", stroke=PALETTE["die"], sw=2.2)
    fig.circle(cx, cy, r_star_5k_mm * scale, fill="#A7F3D0", stroke=PALETTE["bing5k"],
               sw=2.2, dash="6,3")
    fig.circle(cx, cy, r0_mm * scale, fill="#3B82F6", stroke="#1D4ED8", sw=1.5, opacity=0.85)
    fig.text(cx, cy, "Pea-dot R₀", size=8.5, weight="bold", fill="#FFFFFF")

    fig.line(cx, cy, cx + r_star_5k_mm * scale * 0.707, cy - r_star_5k_mm * scale * 0.707,
             stroke=PALETTE["bing5k"], sw=1.4)
    fig.text(cx + 42, cy - 52, f"R* = {r_star_5k_mm:.1f} mm", size=9.5,
             weight="bold", fill=PALETTE["bing5k"])

    fig.line(cx, cy, cx + r_die_mm * scale, cy, stroke=PALETTE["die"], sw=1.4, dash="3,3")
    fig.text(cx + 68, cy + 12, f"R_die = {r_die_mm:.1f} mm", size=9.5,
             weight="bold", fill=PALETTE["die"])

    tx = bx + 318.0
    ty = by + 26.0
    fig.rect(tx, ty, 142.0, 288.0, fill="#FFFFFF", stroke="#CBD2D9", sw=1.0, rx=5.0)
    fig.text(tx + 71, ty + 18, "Coverage Regimes", size=10.8, weight="bold")

    tau_crit = float(rm.bingham_critical_yield_stress(GPU_700W.F0, DROPLET.V0, GPU_700W.R_die))
    items = [
        ("#1D4ED8", "Initial pea-dot (t = 0)", f"R₀ = {r0_mm:.2f} mm (6.1%)"),
        (PALETTE["bing250"], f"Newtonian / n<1 / τ_y≤{tau_crit/1e3:.1f} kPa", "R(t) → R_die (100% cov.)"),
        (PALETTE["bing5k"], "Stalled Bingham (τ_y = 5 kPa)", f"R* = {r_star_5k_mm:.2f} mm (79.4%)"),
        ("#EF4444", "Trapped air perimeter", "20.6% area (k_air = 0.026)"),
    ]
    for idx, (col, head, sub) in enumerate(items):
        yy = ty + 45 + idx * 54
        fig.rect(tx + 10, yy - 7, 12, 12, fill=col, stroke=PALETTE["axis"], sw=0.6, rx=2.0)
        fig.text(tx + 27, yy - 1, head, size=8.3, weight="bold", anchor="start")
        fig.text(tx + 27, yy + 14, sub, size=8.1, fill=PALETTE["muted"], anchor="start")

    fig.line(tx + 10, ty + 252, tx + 132, ty + 252, stroke="#E2E8F0", sw=1.0)
    fig.text(tx + 71, ty + 266, "Critical yield threshold:", size=8.6, weight="bold", fill=PALETTE["danger"])
    fig.text(tx + 71, ty + 280, f"τ_y,crit = {tau_crit/1e3:.2f} kPa  for R* = R_die",
             size=8.6, weight="bold", fill=PALETTE["danger"])

    return fig.save(out_dir / "fig2_pressure_coverage")


# =========================================================================== #
# Figure 3: Constant-volume h(t) & R(t)/R_die evolution (log-log & linear)
# =========================================================================== #
def fig3_thickness_radius(out_dir: Path = FIGURES_DIR) -> Tuple[Path, Path]:
    """Fig 3: (a) Log-log bondline thickness h(t) showing Stefan -1/4 slope,
    Scott power-law scaling, die-capping knee, and Bingham stall h*;
    (b) Normalized radius R(t)/R_die and coverage percentage."""
    fig = SVGFigure(width_in=11.0, height_in=4.75)
    fig.text(550, 18, "Figure 3 — Bondline Thickness h(t) & Die-Coverage Evolution R(t)/R_die Under F₀ = 400 N",
             size=14.0, weight="bold")

    t = np.logspace(-3, 2.3, 450)
    b_5k = Bingham(mu_p=100.0, tau_y=5000.0)
    runs = [
        (SHEAR_THINNING, "Shear-thinning (n = 0.5, K = 100)", PALETTE["n04"], ""),
        (NEWTONIAN, "Newtonian (μ = 100 Pa·s, Stefan)", PALETTE["newt"], ""),
        (SHEAR_THICKENING, "Shear-thickening (n = 1.3, K = 100)", PALETTE["n13"], "6,3"),
        (BINGHAM, "Bingham (τ_y = 250 Pa → h* = 5.5 μm)", PALETTE["bing250"], "4,3"),
        (b_5k, "Bingham (τ_y = 5 kPa → stalls at 77.3 μm)", PALETTE["bing5k"], ""),
    ]

    hc_um = rm.cap_thickness(DROPLET.V0, GPU_700W.R_die) * 1e6

    ax1 = PlotBox(fig, x=78, y=68, w=450, h=340, xlim=(1e-3, 200.0), ylim=(5.0, 1100.0),
                  xscale="log", yscale="log")
    ax1.draw_frame(
        xticks=[(1e-3, "10⁻³"), (1e-2, "10⁻²"), (1e-1, "10⁻¹"),
                (1.0, "10⁰"), (10.0, "10¹"), (100.0, "10²")],
        yticks=[(5.0, "5"), (10.0, "10"), (20.0, "20"), (50.0, "50"),
                (100.0, "100"), (300.0, "300"), (1000.0, "1000")],
        xlabel="Squeeze time  t  [s]",
        ylabel="Bondline thickness  h(t)  [μm]",
        title="(a) Log–Log Bondline Thinning & Yield-Stress Stall",
        subtitle=f"Die-edge cap at h_c = V₀/A_die = {hc_um:.1f} μm (transition to F ∝ h⁻³)",
    )
    ax1.hline(hc_um, color=PALETTE["die"], sw=1.2, dash="5,4")
    fig.text(ax1._tx(1.6e-3), ax1._ty(hc_um * 0.84),
             f"Full coverage threshold  h_c = {hc_um:.1f} μm", size=8.6,
             weight="bold", fill=PALETTE["die"], anchor="start")

    for fl, _, col, dash in runs:
        res = rm.solve_squeeze(fl, t, GPU_700W.F0, DROPLET.V0, DROPLET.h0, GPU_700W.R_die)
        ax1.plot(t, res.h * 1e6, color=col, sw=2.3, dash=dash)

    t_ref = np.array([3e-3, 0.4])
    h_ref_newt = 340.0 * (t_ref / t_ref[0]) ** (-0.25)
    ax1.plot(t_ref, h_ref_newt, color=PALETTE["muted"], sw=1.2, dash="2,2")
    fig.text(ax1._tx(0.03), ax1._ty(165.0), "Stefan slope −1/4", size=8.8,
             italic=True, fill=PALETTE["muted"])

    h_star_5k = rm.bingham_stall(GPU_700W.F0, 5000.0, DROPLET.V0, GPU_700W.R_die)[0] * 1e6
    ax1.hline(h_star_5k, color=PALETTE["bing5k"], sw=1.1, dash="2,3")
    fig.text(ax1._tx(185.0), ax1._ty(h_star_5k * 1.25),
             f"Stall limit h* = {h_star_5k:.1f} μm (> h_c: under-covered!)",
             size=8.6, weight="bold", fill=PALETTE["bing5k"], anchor="end")

    ax1.legend([(lab, col, dash) for _, lab, col, dash in runs],
               lx=ax1.x + 8, ly=ax1.y + 205, row_h=14.3, box_w=262)

    ax2 = PlotBox(fig, x=600, y=68, w=450, h=340, xlim=(1e-3, 200.0), ylim=(0.20, 1.06),
                  xscale="log", yscale="linear")
    ax2.draw_frame(
        xticks=[(1e-3, "10⁻³"), (1e-2, "10⁻²"), (1e-1, "10⁻¹"),
                (1.0, "10⁰"), (10.0, "10¹"), (100.0, "10²")],
        yticks=[(0.25, "0.25"), (0.50, "0.50"), (0.75, "0.75"), (0.89, "0.89"), (1.00, "1.00")],
        xlabel="Squeeze time  t  [s]",
        ylabel="Normalised spread radius  R(t) / R_die",
        title="(b) Radial Spreading Front & Die-Perimeter Capping",
        subtitle="Constant-volume spreading  R(t) = √(V₀ / πh)  capped at  R = R_die = 16.1 mm",
    )
    ax2.hline(1.0, color=PALETTE["ok"], sw=1.4, dash="5,3")
    fig.text(ax2._tx(4e-3), ax2._ty(1.032), "100% GPU die coverage  (R = R_die = 16.10 mm)",
             size=9.1, weight="bold", fill=PALETTE["ok"], anchor="start")

    for fl, _, col, dash in runs:
        res = rm.solve_squeeze(fl, t, GPU_700W.F0, DROPLET.V0, DROPLET.h0, GPU_700W.R_die)
        ax2.plot(t, res.R / GPU_700W.R_die, color=col, sw=2.3, dash=dash)

    r_ratio_5k = rm.bingham_stall(GPU_700W.F0, 5000.0, DROPLET.V0, GPU_700W.R_die)[1] / GPU_700W.R_die
    ax2.hline(r_ratio_5k, color=PALETTE["bing5k"], sw=1.1, dash="2,3")
    fig.text(ax2._tx(185.0), ax2._ty(r_ratio_5k - 0.040),
             f"Bingham 5 kPa stalls at R*/R_die = {r_ratio_5k:.2f} (79.4% area)",
             size=8.8, weight="bold", fill=PALETTE["bing5k"], anchor="end")

    fig.text(ax2._tx(2.5e-3), ax2._ty(0.82), "n = 0.5 covers die in 0.14 s",
             size=8.9, weight="bold", fill=PALETTE["n04"], anchor="start")
    fig.text(ax2._tx(4.2), ax2._ty(0.70), "Newtonian covers die in 4.9 s",
             size=8.9, weight="bold", fill=PALETTE["newt"], anchor="start")

    return fig.save(out_dir / "fig3_thickness_radius")


# =========================================================================== #
# Figure 4: 2D (r, z) Bingham pseudo-plug zone map & plug evolution
# =========================================================================== #
def fig4_bingham_plug_map(out_dir: Path = FIGURES_DIR) -> Tuple[Path, Path]:
    """Fig 4: (a) 2D (r, z) cross-section of the Bingham pseudo-plug core
    z_0(r) = tau_y / G(r) vs. yielded shear layers; (b) Evolution of plug boundary
    2 z_0(r)/h as h -> h* (approaching full-gap lock-up)."""
    fig = SVGFigure(width_in=11.0, height_in=4.75)
    fig.text(550, 18, "Figure 4 — 2D (r, z) Bingham Pseudo-Plug Zone Map & Yield-Surface Evolution Toward Stall",
             size=14.0, weight="bold")

    b_fl = Bingham(mu_p=100.0, tau_y=5000.0)
    h_star, R_star, _ = rm.bingham_stall(GPU_700W.F0, b_fl.tau_y, DROPLET.V0, GPU_700W.R_die)

    h_snap = 1.25 * h_star
    R_snap = float(rm.wetted_radius(h_snap, DROPLET.V0, GPU_700W.R_die))
    W_snap = float(rm.bingham_rate(h_snap, GPU_700W.F0, b_fl, DROPLET.V0, GPU_700W.R_die)[0])

    ax1 = PlotBox(fig, x=94, y=68, w=436, h=340, xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    ax1.draw_frame(
        xticks=[(0.0, "0.0"), (0.2, "0.2"), (0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0")],
        yticks=[(0.0, "0.0 (die)"), (0.25, "0.25"), (0.5, "0.50 (mid)"), (0.75, "0.75"), (1.0, "1.0 (sink)")],
        xlabel="Normalised radial position  r / R(t)",
        ylabel="Normalised axial position  z / h(t)",
        title="(a) 2D (r, z) Yielded Shear Zones vs. Central Pseudo-Plug Core",
        subtitle=f"Bingham TIM (τ_y = 5 kPa) at h = 1.25 h* = {h_snap*1e6:.1f} μm",
        grid=False,
        ylabel_offset=64.0,
    )

    fig.rect(ax1.x + 1, ax1.y + 1, ax1.w - 2, ax1.h - 2, fill="#DBEAFE")

    s = np.linspace(0.0, 1.0, 250)
    xi0 = rm.bingham_plug_fraction(3.0 * b_fl.mu_p * (s * R_snap) * W_snap / (b_fl.tau_y * h_snap**2))
    z_upper = 0.5 * (1.0 + xi0)
    z_lower = 0.5 * (1.0 - xi0)

    poly_pts = ax1.pts(s, z_upper) + list(reversed(ax1.pts(s, z_lower)))
    fig.polygon(poly_pts, fill="#FEF08A", stroke=PALETTE["bing5k"], sw=2.0)

    zh_grid = np.linspace(0.04, 0.96, 13)
    u_max = float(rm.velocity(R_snap, 0.5 * h_snap, h_snap, W_snap, b_fl))
    for s0 in (0.30, 0.60, 0.90):
        ax1.vline(s0, color="#94A3B8", sw=0.9, dash="2,2")
        u_prof = rm.velocity(s0 * R_snap, zh_grid * h_snap, h_snap, W_snap, b_fl) / max(u_max, 1e-30)
        prof_pts = ax1.pts(s0 + 0.08 * u_prof, zh_grid)
        fig.polyline(prof_pts, stroke=PALETTE["axis"], sw=1.5)
        for zv, uv in zip(zh_grid[::2], u_prof[::2]):
            px0, py0 = ax1._tx(s0), ax1._ty(zv)
            px1 = ax1._tx(s0 + 0.08 * float(uv))
            fig.line(px0, py0, px1, py0, stroke=PALETTE["axis"], sw=1.1)

    ax1.hline(0.5, color=PALETTE["muted"], sw=0.9, dash="3,3")
    fig.text(ax1._tx(0.46), ax1._ty(0.50),
             "Pseudo-Plug Core  |τ_rz| ≤ τ_y  (z₀ = τ_y / G(r))",
             size=9.8, weight="bold", fill="#92400E")
    fig.text(ax1._tx(0.62), ax1._ty(0.11),
             "Lower yielded shear layer  (τ_y < |τ_rz| ≤ τ_w)",
             size=9.1, weight="bold", fill="#1E40AF")
    fig.text(ax1._tx(0.62), ax1._ty(0.89),
             "Upper yielded shear layer  (τ_y < |τ_rz| ≤ τ_w)",
             size=9.1, weight="bold", fill="#1E40AF")
    fig.text(ax1._tx(0.05), ax1._ty(0.36),
             "Lipscomb–Denn note: ∂u_p/∂r ≠ 0 → weak O(ε) extensional yield",
             size=8.4, italic=True, fill="#78350F", anchor="start")

    ax2 = PlotBox(fig, x=600, y=68, w=450, h=340, xlim=(0.0, 1.0), ylim=(0.0, 1.05))
    ax2.draw_frame(
        xticks=[(0.0, "0.0"), (0.2, "0.2"), (0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0")],
        yticks=[(0.0, "0.0"), (0.2, "0.2"), (0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0")],
        xlabel="Normalised radial position  r / R(t)",
        ylabel="Local plug fraction  ξ₀(r) = 2 z₀(r) / h(t)",
        title="(b) Growth of Unyielded Plug Fraction as h(t) → h*",
        subtitle="At stall (h → h*, Bn → ∞), ξ₀(r) → 1 across the entire die and flow ceases",
    )

    ratios = [
        (3.00, "h / h* = 3.00  (early squeeze, thin core)", PALETTE["n04"], ""),
        (2.00, "h / h* = 2.00", PALETTE["n07"], "6,3"),
        (1.50, "h / h* = 1.50", PALETTE["bing250"], ""),
        (1.20, "h / h* = 1.20", PALETTE["n13"], "4,3"),
        (1.05, "h / h* = 1.05  (near-stall lock-up)", PALETTE["bing5k"], ""),
    ]
    for mult, lab, col, dash in ratios:
        hh = mult * h_star
        RR = float(rm.wetted_radius(hh, DROPLET.V0, GPU_700W.R_die))
        WW = float(rm.bingham_rate(hh, GPU_700W.F0, b_fl, DROPLET.V0, GPU_700W.R_die)[0])
        xi_curve = rm.bingham_plug_fraction(3.0 * b_fl.mu_p * (s * RR) * WW / (b_fl.tau_y * hh**2))
        ax2.plot(s, xi_curve, color=col, sw=2.2, dash=dash)

    ax2.hline(1.0, color=PALETTE["danger"], sw=1.3, dash="3,3")
    fig.text(ax2._tx(0.52), ax2._ty(1.022), "Stall limit  h = h*  (ξ₀ ≡ 1 everywhere, dh/dt = 0)",
             size=9.1, weight="bold", fill=PALETTE["danger"])

    ax2.legend([(lab, col, dash) for _, lab, col, dash in ratios],
               lx=ax2.x + 15, ly=ax2.y + 195, row_h=15.0, box_w=260)

    return fig.save(out_dir / "fig4_bingham_plug_map")


# =========================================================================== #
# Figure 5: 700 W AI GPU Thermal Performance Design Map
# =========================================================================== #
def _viridis_like(u: float) -> str:
    """Smooth perceptual colormap from cool teal/blue (low dT) to warm red (high dT)."""
    u = min(max(float(u), 0.0), 1.0)
    stops = [
        (0.00, (15, 118, 110)),   # deep teal
        (0.25, (56, 189, 248)),   # sky blue
        (0.50, (250, 204, 21)),   # warm gold
        (0.75, (249, 115, 22)),   # orange
        (1.00, (185, 28, 28)),    # crimson
    ]
    for (u0, c0), (u1, c1) in zip(stops[:-1], stops[1:]):
        if u <= u1:
            t = (u - u0) / max(u1 - u0, 1e-12)
            r = int(round(c0[0] + t * (c1[0] - c0[0])))
            g = int(round(c0[1] + t * (c1[1] - c0[1])))
            b = int(round(c0[2] + t * (c1[2] - c0[2])))
            return f"#{r:02X}{g:02X}{b:02X}"
    return "#B91C1C"


def fig5_gpu_thermal_design_map(out_dir: Path = FIGURES_DIR) -> Tuple[Path, Path]:
    """Fig 5: 2D design maps of 700 W GPU junction-to-cooler TIM temperature rise
    Delta T_TIM over (a) Bingham (F0, tau_y) at stall and (b) Power-law (n, V0) at t = 60 s."""
    fig = SVGFigure(width_in=11.0, height_in=4.85)
    fig.text(550, 18, "Figure 5 — 700 W AI GPU Thermal Performance Design Maps: ΔT_TIM & Under-Coverage Boundary",
             size=14.0, weight="bold")

    ax1 = PlotBox(fig, x=75, y=68, w=415, h=340, xlim=(100.0, 800.0), ylim=(0.1, 8.0))
    nx, ny = 60, 60
    F_grid = np.linspace(100.0, 800.0, nx + 1)
    tau_k_grid = np.linspace(0.1, 8.0, ny + 1)

    dT_min, dT_max = 1.0, 35.0
    cw = ax1.w / nx
    ch = ax1.h / ny
    for i in range(nx):
        Fc = 0.5 * (F_grid[i] + F_grid[i + 1])
        for j in range(ny):
            tc_k = 0.5 * (tau_k_grid[j] + tau_k_grid[j + 1])
            tau_pa = tc_k * 1e3
            h_newt_60 = float(rm.newtonian_h(MOUNT_TIME, Fc, BINGHAM.mu_p, DROPLET.V0, DROPLET.h0, GPU_700W.R_die))
            h_st, _, _ = rm.bingham_stall(Fc, tau_pa, DROPLET.V0, GPU_700W.R_die)
            h_eff = math.hypot(h_newt_60, h_st)
            R_eff = float(rm.wetted_radius(h_eff, DROPLET.V0, GPU_700W.R_die))
            gpu_local = replace(GPU_700W, F0=Fc)
            dT = float(tc.delta_T_tim(h_eff, R_eff, gpu_local, THERMAL))
            u = (math.log10(max(dT, dT_min)) - math.log10(dT_min)) / (math.log10(dT_max) - math.log10(dT_min))
            px = ax1._tx(F_grid[i])
            py = ax1._ty(tau_k_grid[j + 1])
            fig.rect(px, py, cw + 0.6, ch + 0.6, fill=_viridis_like(u))

    ax1.draw_frame(
        xticks=[(100, "100"), (200, "200"), (400, "400"), (600, "600"), (800, "800")],
        yticks=[(0.1, "0.1"), (2.0, "2.0"), (4.0, "4.0"), (6.0, "6.0"), (8.0, "8.0")],
        xlabel="Clamping force  F₀  [N]",
        ylabel="Yield stress  τ_y  [kPa]",
        title="(a) Bingham Design Space (F₀, τ_y) at t = 60 s",
        subtitle="White dashed curve: exact coverage limit  R*(F₀, τ_y) = R_die",
        grid=False,
        fill_bg=False,
    )

    F_line = np.linspace(100.0, 800.0, 200)
    tau_crit_k = rm.bingham_critical_yield_stress(F_line, DROPLET.V0, GPU_700W.R_die) / 1e3
    ax1.plot(F_line, tau_crit_k, color="#FFFFFF", sw=3.2)
    ax1.plot(F_line, tau_crit_k, color=PALETTE["axis"], sw=1.8, dash="5,3")

    res_b250_60 = rm.solve_squeeze(BINGHAM, np.array([MOUNT_TIME]), GPU_700W.F0, DROPLET.V0, DROPLET.h0, GPU_700W.R_die)
    dT_b250_60 = float(tc.delta_T_tim(res_b250_60.h[0], res_b250_60.R[0], GPU_700W, THERMAL))
    fig.circle(ax1._tx(400.0), ax1._ty(0.25), r=5.0, fill="#10B981", stroke="#FFFFFF", sw=1.6)
    fig.rect(ax1._tx(412.0), ax1._ty(0.85), 218.0, 20.0, fill="#0F172A", opacity=0.72, rx=3.0)
    fig.text(ax1._tx(418.0), ax1._ty(0.62), f"Benchmark (400 N, 250 Pa): ΔT = {dT_b250_60:.2f} K",
             size=8.6, weight="bold", fill="#FFFFFF", anchor="start")

    fig.circle(ax1._tx(400.0), ax1._ty(5.0), r=5.0, fill="#EF4444", stroke="#FFFFFF", sw=1.6)
    fig.rect(ax1._tx(118.0), ax1._ty(7.35), 235.0, 36.0, fill="#0F172A", opacity=0.74, rx=4.0)
    fig.text(ax1._tx(126.0), ax1._ty(6.95), "UNDER-COVERAGE ZONE  (R* < R_die)",
             size=9.1, weight="bold", fill="#FFFFFF", anchor="start")
    fig.text(ax1._tx(126.0), ax1._ty(6.35), "Perimeter air trap + hotspot > 200 K",
             size=8.4, fill="#FEF08A", anchor="start")

    # Panel (b): Power-law (n in [0.35, 1.4], V0 in [20, 90] mm^3) at t = 60 s, F0 = 400 N
    ax2 = PlotBox(fig, x=565, y=68, w=415, h=340, xlim=(0.35, 1.40), ylim=(20.0, 90.0))
    n_grid = np.linspace(0.35, 1.40, nx + 1)
    V_mm_grid = np.linspace(20.0, 90.0, ny + 1)
    cw2 = ax2.w / nx
    ch2 = ax2.h / ny

    for i in range(nx):
        nc = 0.5 * (n_grid[i] + n_grid[i + 1])
        fl = PowerLaw(K=100.0, n=float(nc))
        for j in range(ny):
            Vc_mm = 0.5 * (V_mm_grid[j] + V_mm_grid[j + 1])
            Vc = Vc_mm * 1e-9
            hh = float(rm.power_law_h(MOUNT_TIME, fl, GPU_700W.F0, Vc, DROPLET.h0, GPU_700W.R_die))
            RR = float(rm.wetted_radius(hh, Vc, GPU_700W.R_die))
            dT = float(tc.delta_T_tim(hh, RR, GPU_700W, THERMAL))
            u = (math.log10(max(dT, dT_min)) - math.log10(dT_min)) / (math.log10(dT_max) - math.log10(dT_min))
            px = ax2._tx(n_grid[i])
            py = ax2._ty(V_mm_grid[j + 1])
            fig.rect(px, py, cw2 + 0.6, ch2 + 0.6, fill=_viridis_like(u))

    ax2.draw_frame(
        xticks=[(0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0"), (1.2, "1.2"), (1.4, "1.4")],
        yticks=[(20, "20"), (35, "35"), (50, "50"), (65, "65"), (80, "80")],
        xlabel="Flow-behaviour index  n  [—]",
        ylabel="Dispensed pea-dot volume  V₀  [mm³]",
        title="(b) Power-Law Design Space (n, V₀) at t = 60 s",
        subtitle="White dashed curve: minimum volume V₀(n) to reach 100% die coverage in 60 s",
        grid=False,
        fill_bg=False,
    )

    n_line = np.linspace(0.75, 1.40, 120)
    V_crit_mm = []
    for nv in n_line:
        fl = PowerLaw(K=100.0, n=float(nv))
        lo, hi = 5.0, 95.0
        for _ in range(35):
            mid = 0.5 * (lo + hi)
            hh = float(rm.power_law_h(MOUNT_TIME, fl, GPU_700W.F0, mid * 1e-9, DROPLET.h0, R_die=None))
            RR = math.sqrt(mid * 1e-9 / (math.pi * hh))
            if RR >= GPU_700W.R_die:
                hi = mid
            else:
                lo = mid
        V_crit_mm.append(0.5 * (lo + hi))
    ax2.plot(n_line, V_crit_mm, color="#FFFFFF", sw=3.2)
    ax2.plot(n_line, V_crit_mm, color=PALETTE["axis"], sw=1.8, dash="5,3")

    fig.circle(ax2._tx(0.5), ax2._ty(50.0), r=5.0, fill="#10B981", stroke="#FFFFFF", sw=1.6)
    fig.rect(ax2._tx(0.40), ax2._ty(59.5), 232.0, 20.0, fill="#0F172A", opacity=0.72, rx=3.0)
    fig.text(ax2._tx(0.415), ax2._ty(57.4), "Shear-thinning (n=0.5, 50 mm³): ΔT = 1.85 K",
             size=8.6, weight="bold", fill="#FFFFFF", anchor="start")

    fig.circle(ax2._tx(1.0), ax2._ty(50.0), r=4.8, fill="#111111", stroke="#FFFFFF", sw=1.5)
    fig.rect(ax2._tx(0.94), ax2._ty(46.5), 172.0, 20.0, fill="#0F172A", opacity=0.72, rx=3.0)
    fig.text(ax2._tx(0.955), ax2._ty(44.4), "Newtonian (n=1.0): ΔT = 4.23 K",
             size=8.5, weight="bold", fill="#FFFFFF", anchor="start")

    cb_x, cb_y, cb_w, cb_h = 1002.0, 68.0, 18.0, 340.0
    n_cb = 80
    for k in range(n_cb):
        u = (k + 0.5) / n_cb
        yy = cb_y + cb_h - (k + 1) * (cb_h / n_cb)
        fig.rect(cb_x, yy, cb_w, cb_h / n_cb + 0.5, fill=_viridis_like(u))
    fig.rect(cb_x, cb_y, cb_w, cb_h, fill="none", stroke=PALETTE["axis"], sw=1.2)
    for val in (1.0, 2.0, 5.0, 10.0, 20.0, 35.0):
        u = (math.log10(val) - math.log10(dT_min)) / (math.log10(dT_max) - math.log10(dT_min))
        py = cb_y + cb_h - u * cb_h
        fig.line(cb_x + cb_w, py, cb_x + cb_w + 4.0, py, stroke=PALETTE["axis"], sw=1.1)
        fig.text(cb_x + cb_w + 7.0, py, f"{val:g} K", size=9.2, anchor="start")
    fig.text(cb_x + 0.5 * cb_w, cb_y - 14.0, "ΔT_TIM [K]", size=10.2, weight="bold")

    return fig.save(out_dir / "fig5_gpu_thermal_design_map")


# =========================================================================== #
# Figure 6: Dimensionless Assumption-Validity Map (eps, Re_sq, Bn)
# =========================================================================== #
def fig6_regime_validity(out_dir: Path = FIGURES_DIR) -> Tuple[Path, Path]:
    """Fig 6: Time trajectories of (a) aspect ratio eps(t) = h/R and squeeze
    Reynolds number Re_sq(t), and (b) Bingham number Bn(t) showing divergence at stall."""
    fig = SVGFigure(width_in=11.0, height_in=4.75)
    fig.text(550, 18, "Figure 6 — Dimensionless Assumption-Validity Map: ε(t) = h/R, Re_sq(t), and Bn(t)",
             size=14.0, weight="bold")

    t = np.logspace(-3, 2.0, 350)
    b_5k = Bingham(mu_p=100.0, tau_y=5000.0)
    models = [
        (SHEAR_THINNING, "Shear-thinning (n = 0.5)", PALETTE["n04"], ""),
        (NEWTONIAN, "Newtonian (n = 1.0)", PALETTE["newt"], ""),
        (SHEAR_THICKENING, "Shear-thickening (n = 1.3)", PALETTE["n13"], "6,3"),
        (BINGHAM, "Bingham (τ_y = 250 Pa)", PALETTE["bing250"], "4,3"),
        (b_5k, "Bingham (τ_y = 5 kPa)", PALETTE["bing5k"], ""),
    ]

    ax1 = PlotBox(fig, x=80, y=68, w=448, h=340, xlim=(1e-3, 100.0), ylim=(1e-12, 1.0),
                  xscale="log", yscale="log")
    ax1.draw_frame(
        xticks=[(1e-3, "10⁻³"), (1e-2, "10⁻²"), (1e-1, "10⁻¹"),
                (1.0, "10⁰"), (10.0, "10¹"), (100.0, "10²")],
        yticks=[(1e-12, "10⁻¹²"), (1e-10, "10⁻¹⁰"), (1e-8, "10⁻⁸"),
                (1e-6, "10⁻⁶"), (1e-4, "10⁻⁴"), (1e-2, "10⁻²"), (1.0, "10⁰")],
        xlabel="Squeeze time  t  [s]",
        ylabel="Dimensionless group magnitude  ε(t),  Re_sq(t)",
        title="(a) Lubrication (ε = h/R ≪ 1) & Creeping-Flow (Re_sq ≪ 1) Validity",
        subtitle="Upper curves: aspect ratio ε(t) ≤ 10⁻²; lower curves: Re_sq(t) ≤ 10⁻⁴",
    )
    ax1.hline(0.1, color=PALETTE["danger"], sw=1.3, dash="4,3")
    fig.text(ax1._tx(2e-3), ax1._ty(0.24),
             "Lubrication breakdown threshold  ε = 0.1  (all trajectories remain ≥ 10× below)",
             size=8.6, weight="bold", fill=PALETTE["danger"], anchor="start")

    for fl, _, col, dash in models:
        res = rm.solve_squeeze(fl, t, GPU_700W.F0, DROPLET.V0, DROPLET.h0, GPU_700W.R_die)
        rep = dg.validity_report(res)
        ax1.plot(t, rep["eps"], color=col, sw=2.2, dash=dash)
        ax1.plot(t, np.maximum(rep["Re_sq"], 1e-13), color=col, sw=1.7, dash="2,2.5")

    fig.text(ax1._tx(3.5), ax1._ty(3.5e-2), "Aspect ratio  ε(t) = h(t)/R(t)",
             size=9.2, weight="bold", fill=PALETTE["axis"])
    fig.text(ax1._tx(1.5e-2), ax1._ty(4e-11), "Squeeze Reynolds  Re_sq(t) = ρ|dh/dt|h / μ_eff",
             size=9.2, weight="bold", fill=PALETTE["axis"], anchor="start")

    ax1.legend([(lab, col, dash) for _, lab, col, dash in models],
               lx=ax1.x + 225, ly=ax1.y + 110, row_h=14.3, box_w=208)

    ax2 = PlotBox(fig, x=600, y=68, w=450, h=340, xlim=(1e-3, 100.0), ylim=(1e-4, 1e4),
                  xscale="log", yscale="log")
    ax2.draw_frame(
        xticks=[(1e-3, "10⁻³"), (1e-2, "10⁻²"), (1e-1, "10⁻¹"),
                (1.0, "10⁰"), (10.0, "10¹"), (100.0, "10²")],
        yticks=[(1e-4, "10⁻⁴"), (1e-2, "10⁻²"), (1.0, "10⁰"), (1e2, "10²"), (1e4, "10⁴")],
        xlabel="Squeeze time  t  [s]",
        ylabel="Bingham number  Bn(t) = τ_y h² / (μ_p R |dh/dt|)",
        title="(b) Bingham Number Trajectory & Plastic-Stall Divergence",
        subtitle="Bn ≪ 1: viscous-dominated squeeze;  Bn ≫ 1: yield-stress-dominated approach to h*",
    )
    ax2.hline(1.0, color=PALETTE["muted"], sw=1.2, dash="4,3")
    fig.text(ax2._tx(2e-3), ax2._ty(1.55), "Viscoplastic crossover  Bn = 1  (Λ = 3/Bn = 3)",
             size=8.9, weight="bold", fill=PALETTE["muted"], anchor="start")

    b_cases = [
        (Bingham(mu_p=100.0, tau_y=50.0), "Bingham τ_y = 50 Pa (low yield)", PALETTE["n04"], "6,3"),
        (BINGHAM, "Bingham τ_y = 250 Pa (nominal paste)", PALETTE["bing250"], ""),
        (Bingham(mu_p=100.0, tau_y=1500.0), "Bingham τ_y = 1.5 kPa (moderate yield)", PALETTE["n13"], "4,3"),
        (b_5k, "Bingham τ_y = 5.0 kPa (stalls at R* < R_die)", PALETTE["bing5k"], ""),
    ]
    for fl, _, col, dash in b_cases:
        res = rm.solve_squeeze(fl, t, GPU_700W.F0, DROPLET.V0, DROPLET.h0, GPU_700W.R_die)
        bn = dg.bingham_number(fl, res.h, res.R, res.W)
        ax2.plot(t, bn, color=col, sw=2.3, dash=dash)

    fig.text(ax2._tx(80.0), ax2._ty(2.2e3), "As h(t) → h*, dh/dt → 0 ⇒ Bn(t) → ∞",
             size=9.1, weight="bold", fill=PALETTE["bing5k"], anchor="end")
    ax2.legend([(lab, col, dash) for _, lab, col, dash in b_cases],
               lx=ax2.x + 12, ly=ax2.y + 12, row_h=15.0, box_w=255)

    return fig.save(out_dir / "fig6_regime_validity")


# =========================================================================== #
# Side-by-Side Real-Time GPU Spreading GIF Animation (`figures/gpu_spread.gif`)
# =========================================================================== #
def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    if os.path.exists(path):
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def generate_gpu_spread_gif(out_dir: Path = FIGURES_DIR, n_frames: int = 36) -> Path:
    """Side-by-side real-time animation of the pea-dot spreading over the 700 W GPU die
    for Newtonian, Shear-Thinning (n=0.5), and Bingham pastes with live h(t),
    coverage %, and Delta T_TIM readouts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    gif_path = out_dir / "gpu_spread.gif"

    S = 2
    W, H = 960 * S, 410 * S
    f_title = _load_font(17 * S, bold=True)
    f_sub = _load_font(12 * S, bold=False)
    f_head = _load_font(14 * S, bold=True)
    f_metric = _load_font(12 * S, bold=True)
    f_small = _load_font(11 * S, bold=False)

    t_frames = np.concatenate([[0.0], np.logspace(-2.5, math.log10(MOUNT_TIME), n_frames - 1)])

    b_5k = Bingham(mu_p=100.0, tau_y=5000.0)
    panels = [
        ("Newtonian (μ = 100 Pa·s)", NEWTONIAN, (37, 99, 235)),
        ("Shear-Thinning (n = 0.5, K = 100)", SHEAR_THINNING, (5, 150, 105)),
        ("Bingham (τ_y = 250 Pa vs. 5 kPa)", BINGHAM, (217, 119, 6)),
    ]

    histories = [
        rm.solve_squeeze(fl, t_frames, GPU_700W.F0, DROPLET.V0, DROPLET.h0, GPU_700W.R_die)
        for _, fl, _ in panels
    ]
    thermals = [tc.thermal_state(res.h, res.R, GPU_700W, THERMAL) for res in histories]
    res_b5k = rm.solve_squeeze(b_5k, t_frames, GPU_700W.F0, DROPLET.V0, DROPLET.h0, GPU_700W.R_die)
    th_b5k = tc.thermal_state(res_b5k.h, res_b5k.R, GPU_700W, THERMAL)

    frames: List[Image.Image] = []
    for k, tk in enumerate(t_frames):
        im = Image.new("RGB", (W, H), (248, 250, 252))
        dr = ImageDraw.Draw(im)

        dr.rectangle([0, 0, W, 56 * S], fill=(15, 23, 42))
        dr.text((22 * S, 10 * S),
                "700 W AI GPU Thermal-Paste Squeeze Flow — Constant Clamping Load F₀ = 400 N, V₀ = 50 mm³",
                fill=(255, 255, 255), font=f_title)
        dr.text((22 * S, 33 * S),
                f"Elapsed mount time:  t = {tk:6.2f} s   |   Die area A_die = 814 mm² (R_die = 16.10 mm, q'' = 86 W/cm²)",
                fill=(148, 163, 184), font=f_sub)

        for p_idx, (title, _, col) in enumerate(panels):
            px0 = (18 + p_idx * 312) * S
            py0 = 68 * S
            pw, ph = 298 * S, 326 * S
            dr.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=8 * S,
                                 fill=(255, 255, 255), outline=(203, 213, 225), width=2)
            dr.text((px0 + 14 * S, py0 + 10 * S), title, fill=(15, 23, 42), font=f_head)

            cx = px0 + pw // 2
            cy = py0 + 132 * S
            r_die_px = int(round(82 * S))

            sq = int(round(92 * S))
            dr.rounded_rectangle([cx - sq, cy - sq, cx + sq, cy + sq], radius=6 * S,
                                 fill=(226, 232, 240), outline=(148, 163, 184), width=2)

            dr.ellipse([cx - r_die_px, cy - r_die_px, cx + r_die_px, cy + r_die_px],
                       fill=(254, 226, 226), outline=(51, 65, 85), width=3)

            res = histories[p_idx]
            th = thermals[p_idx]
            r_frac = float(res.R[k] / GPU_700W.R_die)
            r_px = max(int(round(r_frac * r_die_px)), 3 * S)

            fill_rgb = tuple(int(0.25 * c + 0.75 * 255) for c in col)
            dr.ellipse([cx - r_px, cy - r_px, cx + r_px, cy + r_px],
                       fill=fill_rgb, outline=col, width=3 * S)

            if p_idx == 2:
                r5_frac = float(res_b5k.R[k] / GPU_700W.R_die)
                r5_px = max(int(round(r5_frac * r_die_px)), 3 * S)
                dr.ellipse([cx - r5_px, cy - r5_px, cx + r5_px, cy + r5_px],
                           outline=(220, 38, 38), width=3 * S)

            my = py0 + 232 * S
            dr.line([px0 + 12 * S, my, px0 + pw - 12 * S, my], fill=(226, 232, 240), width=2)

            h_um = float(res.h[k] * 1e6)
            cov_pct = float(th.coverage[k] * 100.0)
            dT_val = float(th.dT_tim[k])

            dr.text((px0 + 14 * S, my + 8 * S),
                    f"Bondline  h(t):   {h_um:6.1f} μm", fill=(15, 23, 42), font=f_metric)
            dr.text((px0 + 14 * S, my + 28 * S),
                    f"Die coverage:     {cov_pct:5.1f} %",
                    fill=(5, 150, 105) if cov_pct >= 99.9 else (180, 83, 9), font=f_metric)
            if p_idx < 2:
                dr.text((px0 + 14 * S, my + 48 * S),
                        f"TIM temp rise ΔT: {dT_val:5.2f} K", fill=col, font=f_metric)
                status = "100% covered (squeezing excess)" if cov_pct >= 99.9 else "Spreading across die..."
                dr.text((px0 + 14 * S, my + 69 * S), status, fill=(100, 116, 139), font=f_small)
            else:
                h5_um = float(res_b5k.h[k] * 1e6)
                cov5 = float(th_b5k.coverage[k] * 100.0)
                dT5 = float(th_b5k.dT_tim[k])
                dr.text((px0 + 14 * S, my + 48 * S),
                        f"τ_y=250 Pa: ΔT={dT_val:4.2f} K (100% cov)",
                        fill=col, font=f_small)
                dr.text((px0 + 14 * S, my + 66 * S),
                        f"τ_y=5 kPa (red): h*={h5_um:4.1f} μm, {cov5:4.1f}%, ΔT={dT5:4.1f} K",
                        fill=(220, 38, 38), font=f_small)

        small = im.resize((W // S, H // S), resample=Image.Resampling.LANCZOS)
        frames.append(small.quantize(colors=128, method=Image.Quantize.MEDIANCUT))

    durations = [110] * len(frames)
    durations[0] = 550
    durations[-1] = 1400
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    return gif_path


def generate_all_visuals(out_dir: Path = FIGURES_DIR) -> List[Path]:
    """Generate all 6 publication figures (PNG + PDF) and the GPU spreading GIF."""
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    for builder in (
        fig1_velocity_stress,
        fig2_pressure_coverage,
        fig3_thickness_radius,
        fig4_bingham_plug_map,
        fig5_gpu_thermal_design_map,
        fig6_regime_validity,
    ):
        png, pdf = builder(out_dir)
        outputs.extend([png, pdf])
    gif = generate_gpu_spread_gif(out_dir)
    outputs.append(gif)
    return outputs


if __name__ == "__main__":
    paths = generate_all_visuals()
    for p in paths:
        print(f"Generated: {p.relative_to(REPO_ROOT)}  ({p.stat().st_size / 1024:.1f} KB)")
