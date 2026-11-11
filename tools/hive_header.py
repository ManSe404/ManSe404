# /// script
# requires-python = ">=3.12"
# dependencies = ["fonttools>=4.50", "brotli>=1.1"]
# ///
# ruff: noqa: E501  (the SVG template is markup; its lines stay whole)
"""Build the hive header of the profile README, one SVG per theme.

The look follows Mission Control's "hive": honey on warm dark wood at night,
honey on cream paper by day, pointy-top hexagons and a faint honeycomb.

GitHub shows README images as <img>, which cannot load web fonts, so the
fonts are embedded: Figtree and JetBrains Mono (SIL Open Font License 1.1),
pinned on jsDelivr, cut to the weights and letters the header uses.

Run from anywhere:  uv run tools/hive_header.py
uv reads the dependencies from the block above.
"""

from __future__ import annotations

import argparse
import base64
import io
import math
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

FONT_URLS = {
    "figtree": "https://cdn.jsdelivr.net/npm/@fontsource-variable/figtree@5.3.0/files/figtree-latin-wght-normal.woff2",
    "mono": "https://cdn.jsdelivr.net/npm/@fontsource-variable/jetbrains-mono@5.3.0/files/jetbrains-mono-latin-wght-normal.woff2",
}

WIDTH, HEIGHT = 1200, 340

# Text of the header. Change it here, then run the script again.
KICKER = "BELGRADE · AI & DATA"
NAME = "Stefan Seman"
HEADLINE = "Head of AI · ML engineer · PhD researcher"
SUB = ("I lead an AI and data team", "and still build the systems myself.")

# Cells of the comb: (column offset, row offset, label lines, filled with honey).
CELLS = [
    (0, 0, ("AI",), True),
    (1, 0, ("RAG",), False),
    (-1, 0, ("Agents",), False),
    (-0.5, -1, ("Document", "AI"), True),
    (0.5, -1, ("Evals",), False),
    (-0.5, 1, ("Data", "platforms"), False),
    (0.5, 1, ("Cardiology",), True),
]


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    surface: str
    line: str
    line_strong: str
    text: str
    muted: str
    honey: str
    honey_deep: str
    accent: str
    on_honey: str
    comb_opacity: float
    glow_opacity: float


# Values copied from Mission Control's design tokens (light-dark pairs).
DARK = Theme(
    "dark",
    "#13100a",
    "#1d1810",
    "#3a301f",
    "#54452b",
    "#f7edd9",
    "#cdb98f",
    "#ffb627",
    "#f59e0b",
    "#ffc048",
    "#2a1c00",
    0.9,
    0.55,
)
LIGHT = Theme(
    "light",
    "#fbf5e7",
    "#fffdf7",
    "#e6d5ad",
    "#d5bf8c",
    "#2a1f0e",
    "#634f2c",
    "#f2a900",
    "#d68a00",
    "#a35f00",
    "#2a1c00",
    1.0,
    0.35,
)


def fetch(url: str, font_dir: Path | None) -> bytes:
    if font_dir is not None:
        return (font_dir / url.rsplit("/", 1)[1]).read_bytes()
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def static_font(data: bytes, weight: int) -> TTFont:
    font = TTFont(io.BytesIO(data))
    return instancer.instantiateVariableFont(font, {"wght": weight})


def embed(font: TTFont, text: str) -> str:
    options = Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga"]
    options.name_IDs = ["*"]
    subsetter = Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    buffer = io.BytesIO()
    font.flavor = "woff2"
    font.save(buffer)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def measure(font: TTFont, text: str, size: float, tracking: float = 0.0) -> float:
    """Width of text in px from advance widths (kerning ignored)."""
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    units = font["head"].unitsPerEm
    advance = sum(hmtx[cmap[ord(char)]][0] for char in text)
    return advance * size / units + tracking * (len(text) - 1)


def hexagon(cx: float, cy: float, radius: float) -> str:
    points = []
    for corner in range(6):
        angle = math.radians(60 * corner - 90)
        points.append(
            f"{cx + radius * math.cos(angle):.1f},{cy + radius * math.sin(angle):.1f}"
        )
    return " ".join(points)


def build(theme: Theme, fonts: dict[str, str]) -> str:
    radius = 60.0
    step_x = math.sqrt(3) * radius
    step_y = 1.5 * radius
    cx0, cy0 = WIDTH - 64 - 1.5 * step_x, HEIGHT / 2

    cells = []
    for col, row, lines, filled in CELLS:
        cx, cy = cx0 + col * step_x, cy0 + row * step_y
        fill = theme.honey if filled else theme.surface
        stroke = theme.honey_deep if filled else theme.line_strong
        ink = theme.on_honey if filled else theme.accent
        size = 34 if lines == ("AI",) else 17
        weight = 750 if lines == ("AI",) else 600
        cells.append(
            f'<polygon points="{hexagon(cx, cy, radius - 5)}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        first = cy - (len(lines) - 1) * size * 0.6
        for index, line in enumerate(lines):
            y = first + index * size * 1.2
            cells.append(
                f'<text x="{cx:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'style="font: {weight} {size}px HiveSans, Figtree, \'Segoe UI\', sans-serif" fill="{ink}">{line}</text>'
            )

    glow = hexagon(cx0, cy0, radius + 6)
    kicker_hex = hexagon(72, 86, 8)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">{NAME}</title>
<desc id="desc">{HEADLINE}. {" ".join(SUB)}</desc>
<defs>
<style>
@font-face {{ font-family: HiveSans; font-weight: 750; src: url(data:font/woff2;base64,{fonts["sans750"]}) format("woff2"); }}
@font-face {{ font-family: HiveSans; font-weight: 600; src: url(data:font/woff2;base64,{fonts["sans600"]}) format("woff2"); }}
@font-face {{ font-family: HiveSans; font-weight: 500; src: url(data:font/woff2;base64,{fonts["sans500"]}) format("woff2"); }}
@font-face {{ font-family: HiveMono; font-weight: 500; src: url(data:font/woff2;base64,{fonts["mono500"]}) format("woff2"); }}
.pulse {{ animation: pulse 5s ease-in-out infinite; }}
@keyframes pulse {{ 0%, 100% {{ opacity: 0.35; }} 50% {{ opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{ .pulse {{ animation: none; opacity: 0.7; }} }}
</style>
<clipPath id="frame"><rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="20"/></clipPath>
<pattern id="comb" width="28" height="48" patternUnits="userSpaceOnUse" patternTransform="scale(1.75)">
<path d="M14 0L28 8V24L14 32L0 24V8ZM14 32V48" fill="none" stroke="{theme.line}" stroke-width="0.8"/>
</pattern>
<linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset="0.45" stop-color="#fff" stop-opacity="0.15"/>
<stop offset="1" stop-color="#fff" stop-opacity="1"/>
</linearGradient>
<mask id="combMask"><rect width="{WIDTH}" height="{HEIGHT}" fill="url(#fade)"/></mask>
<radialGradient id="honeyGlow" cx="{cx0 / WIDTH:.3f}" cy="0.5" r="0.32">
<stop offset="0" stop-color="{theme.honey}" stop-opacity="{theme.glow_opacity * 0.5:.2f}"/>
<stop offset="1" stop-color="{theme.honey}" stop-opacity="0"/>
</radialGradient>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
</defs>
<g clip-path="url(#frame)">
<rect width="{WIDTH}" height="{HEIGHT}" fill="{theme.bg}"/>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#comb)" mask="url(#combMask)" opacity="{theme.comb_opacity}"/>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#honeyGlow)"/>
<polygon class="pulse" points="{glow}" fill="{theme.honey}" opacity="{theme.glow_opacity}" filter="url(#blur)"/>
{chr(10).join(cells)}
<polygon points="{kicker_hex}" fill="{theme.honey}"/>
<text x="90" y="86" dominant-baseline="central" style="font: 500 17px HiveMono, 'JetBrains Mono', ui-monospace, monospace; letter-spacing: 3px" fill="{theme.accent}">{KICKER.replace("&", "&amp;")}</text>
<text x="62" y="172" style="font: 750 76px HiveSans, Figtree, 'Segoe UI', sans-serif; letter-spacing: -1.5px" fill="{theme.text}">{NAME}</text>
<text x="64" y="222" style="font: 500 28px HiveSans, Figtree, 'Segoe UI', sans-serif" fill="{theme.text}">{HEADLINE}</text>
<text x="64" y="266" style="font: 500 21px HiveSans, Figtree, 'Segoe UI', sans-serif" fill="{theme.muted}">{SUB[0]}</text>
<text x="64" y="295" style="font: 500 21px HiveSans, Figtree, 'Segoe UI', sans-serif" fill="{theme.muted}">{SUB[1]}</text>
</g>
<rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="20" fill="none" stroke="{theme.line}" stroke-width="2"/>
</svg>
"""


def hex_icon(theme: Theme) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="20" viewBox="0 0 18 20" aria-hidden="true">'
        f'<polygon points="{hexagon(9, 10, 9)}" fill="{theme.honey}" stroke="{theme.honey_deep}" stroke-width="1"/>'
        "</svg>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--font-dir",
        type=Path,
        help="folder with the two .woff2 files, instead of downloading them",
    )
    args = parser.parse_args()

    sans_data = fetch(FONT_URLS["figtree"], args.font_dir)
    mono_data = fetch(FONT_URLS["mono"], args.font_dir)

    cell_text = "".join("".join(lines) for _, _, lines, _ in CELLS)
    sans_text = NAME + HEADLINE + "".join(SUB) + cell_text

    measured = static_font(sans_data, 750)
    right_edge = 64 + max(
        measure(measured, NAME, 76, -1.5),
        measure(static_font(sans_data, 500), HEADLINE, 28),
        *(measure(static_font(sans_data, 500), line, 21) for line in SUB),
    )
    comb_left = WIDTH - 64 - 3 * math.sqrt(3) * 60
    print(f"text ends at {right_edge:.0f}px, comb starts at {comb_left:.0f}px")
    if right_edge > comb_left - 40:
        raise SystemExit("header text runs into the comb; shorten the text")

    fonts = {
        "sans750": embed(static_font(sans_data, 750), NAME + "AI"),
        "sans600": embed(static_font(sans_data, 600), cell_text),
        "sans500": embed(static_font(sans_data, 500), sans_text),
        "mono500": embed(static_font(mono_data, 500), KICKER),
    }

    ASSETS.mkdir(exist_ok=True)
    for theme in (DARK, LIGHT):
        path = ASSETS / f"hive-header-{theme.name}.svg"
        path.write_text(build(theme, fonts), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")
    (ASSETS / "hex.svg").write_text(hex_icon(DARK), encoding="utf-8")
    print("wrote assets/hex.svg")


if __name__ == "__main__":
    main()
