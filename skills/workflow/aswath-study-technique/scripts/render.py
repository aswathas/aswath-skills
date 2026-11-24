"""
Render an Excalidraw scene (legacy .excalidraw JSON) to PNG so a drawing can be
checked for clipping, overlap and legibility before it is shipped.

Approximate by design: it draws the same boxes, arrows and text the plugin draws,
using Pillow's font metrics. It is a layout check, not an Excalidraw clone.
"""

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCALE = 1.0
MARGIN = 30


def load_font(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except OSError:
                continue
    return ImageFont.load_default()


def color(value: str, default=(30, 30, 30, 255)):
    if not value or value == "transparent":
        return None
    v = value.lstrip("#")
    if len(v) == 6:
        return tuple(int(v[i : i + 2], 16) for i in (0, 2, 4)) + (255,)
    return default


def draw_arrow(draw, el):
    pts = el.get("points") or [[0, 0], [1, 1]]
    ox, oy = el["x"], el["y"]
    abs_pts = [(ox + p[0], oy + p[1]) for p in pts]
    c = color(el.get("strokeColor"), (71, 85, 105, 255))
    width = max(1, int(el.get("strokeWidth", 2)))
    draw.line(abs_pts, fill=c, width=width, joint="curve")
    (x1, y1), (x2, y2) = abs_pts[-2], abs_pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 11
    a1 = ang + math.radians(155)
    a2 = ang - math.radians(155)
    p1 = (x2 + size * math.cos(a1), y2 + size * math.sin(a1))
    p2 = (x2 + size * math.cos(a2), y2 + size * math.sin(a2))
    draw.polygon([(x2, y2), p1, p2], fill=c)


def main(scene_path: str, out_path: str):
    scene = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    els = scene.get("elements", [])

    max_x = max((e["x"] + e.get("width", 0) for e in els), default=800)
    max_y = max((e["y"] + e.get("height", 0) for e in els), default=600)
    W = int(max_x + MARGIN * 2)
    H = int(max_y + MARGIN * 2)

    bg = scene.get("appState", {}).get("viewBackgroundColor") or "#ffffff"
    img = Image.new("RGB", (W, H), color(bg, (255, 255, 255, 255))[:3])
    draw = ImageDraw.Draw(img)

    for el in els:
        t = el["type"]
        if t == "rectangle":
            fill = color(el.get("backgroundColor"))
            stroke = color(el.get("strokeColor"))
            box = [el["x"], el["y"], el["x"] + el["width"], el["y"] + el["height"]]
            radius = 10 if el.get("roundness") else 0
            if radius:
                draw.rounded_rectangle(
                    box,
                    radius=radius,
                    fill=fill[:3] if fill else None,
                    outline=stroke[:3] if stroke else None,
                    width=max(1, int(el.get("strokeWidth", 2))),
                )
            else:
                draw.rectangle(
                    box,
                    fill=fill[:3] if fill else None,
                    outline=stroke[:3] if stroke else None,
                    width=max(1, int(el.get("strokeWidth", 2))),
                )
        elif t == "arrow":
            draw_arrow(draw, el)

    for el in els:
        if el["type"] != "text":
            continue
        size = int(el.get("fontSize", 16))
        f = load_font(size, bold=el.get("strokeColor", "").lower() in ("#1e1e1e", "#2563eb", "#b91c1c"))
        c = color(el.get("strokeColor"), (30, 30, 30, 255))[:3]
        txt = el.get("text", "")
        draw.multiline_text(
            (el["x"], el["y"]),
            txt,
            font=f,
            fill=c,
            spacing=int(size * 0.28),
            align="left",
        )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"{out_path}  {W}x{H}  elements={len(els)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
