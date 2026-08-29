#!/usr/bin/env python3
"""Regenerate tab-bar and reaction icons from the visual tokens.

Colors match docs/miniprogram/visual.md. Run:

    python3 -m venv .venv && .venv/bin/pip install Pillow
    .venv/bin/python scripts/export-brand-icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TAB_DIR = ROOT / "miniprogram" / "assets" / "tab"
ICON_DIR = ROOT / "miniprogram" / "assets" / "icon"

ORANGE = (240, 120, 60, 255)
MUTED = (163, 152, 142, 255)
CLEAR = (0, 0, 0, 0)
LIKE = (240, 120, 60, 255)
FAVORITE = (240, 176, 72, 255)
REPLY = (240, 120, 60, 255)
SHARE = (240, 120, 60, 255)
CREAM = (255, 251, 246, 255)
SHINE = (255, 255, 255, 200)

TAB_SIZE = 81
TAB_SCALE = 4
REACT_SIZE = 64
REACT_SCALE = 4


def new_canvas(px: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (px, px), CLEAR)
    return img, ImageDraw.Draw(img)


def down(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.Resampling.LANCZOS)


def draw_home(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    m = int(s * 0.18)
    body_l, body_t, body_r, body_b = m + s * 0.08, int(s * 0.42), s - m - s * 0.08, s - m
    d.rounded_rectangle((body_l, body_t, body_r, body_b), radius=s * 0.08, fill=c)
    roof = [
        (s * 0.18, s * 0.46),
        (s * 0.50, s * 0.18),
        (s * 0.82, s * 0.46),
    ]
    d.polygon(roof, fill=c)
    door_w = s * 0.16
    d.rounded_rectangle(
        (s / 2 - door_w / 2, body_b - s * 0.22, s / 2 + door_w / 2, body_b),
        radius=s * 0.04,
        fill=(255, 251, 246, 255),
    )
    d.ellipse((s * 0.46, s * 0.30, s * 0.54, s * 0.38), fill=(255, 251, 246, 255))


def draw_album(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.rounded_rectangle((s * 0.20, s * 0.26, s * 0.80, s * 0.74), radius=s * 0.10, fill=c)
    d.rounded_rectangle((s * 0.28, s * 0.34, s * 0.72, s * 0.66), radius=s * 0.06, fill=(255, 251, 246, 255))
    d.ellipse((s * 0.34, s * 0.40, s * 0.46, s * 0.52), fill=c)
    d.polygon([(s * 0.44, s * 0.62), (s * 0.56, s * 0.44), (s * 0.70, s * 0.62)], fill=c)


def draw_create(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.ellipse((s * 0.16, s * 0.16, s * 0.84, s * 0.84), fill=c)
    bar = s * 0.10
    d.rounded_rectangle((s * 0.30, s / 2 - bar / 2, s * 0.70, s / 2 + bar / 2), radius=bar / 2, fill=(255, 251, 246, 255))
    d.rounded_rectangle((s / 2 - bar / 2, s * 0.30, s / 2 + bar / 2, s * 0.70), radius=bar / 2, fill=(255, 251, 246, 255))


def draw_plaza(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.rounded_rectangle((s * 0.20, s * 0.22, s * 0.80, s * 0.64), radius=s * 0.16, fill=c)
    d.polygon([(s * 0.32, s * 0.60), (s * 0.28, s * 0.78), (s * 0.50, s * 0.62)], fill=c)
    d.ellipse((s * 0.34, s * 0.38, s * 0.42, s * 0.46), fill=(255, 251, 246, 255))
    d.ellipse((s * 0.46, s * 0.38, s * 0.54, s * 0.46), fill=(255, 251, 246, 255))
    d.ellipse((s * 0.58, s * 0.38, s * 0.66, s * 0.46), fill=(255, 251, 246, 255))


def draw_me(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.ellipse((s * 0.36, s * 0.18, s * 0.64, s * 0.46), fill=c)
    d.rounded_rectangle((s * 0.24, s * 0.50, s * 0.76, s * 0.82), radius=s * 0.18, fill=c)


def export_tab(name: str, painter) -> None:
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    big = TAB_SIZE * TAB_SCALE
    for suffix, color in (("", MUTED), ("-active", ORANGE)):
        img, draw = new_canvas(big)
        painter(draw, color, big)
        down(img, TAB_SIZE).save(TAB_DIR / f"{name}{suffix}.png")


def export_react(name: str, painter, color) -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    big = REACT_SIZE * REACT_SCALE
    for suffix, tint in (("", MUTED), ("-active", color)):
        img, draw = new_canvas(big)
        painter(draw, tint, big)
        down(img, REACT_SIZE).save(ICON_DIR / f"react-{name}{suffix}.png")


def draw_like(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.ellipse((s * 0.14, s * 0.18, s * 0.56, s * 0.62), fill=c)
    d.ellipse((s * 0.44, s * 0.18, s * 0.86, s * 0.62), fill=c)
    d.polygon([(s * 0.16, s * 0.46), (s * 0.50, s * 0.90), (s * 0.84, s * 0.46)], fill=c)
    d.ellipse((s * 0.24, s * 0.28, s * 0.38, s * 0.42), fill=SHINE)


def draw_reply(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.rounded_rectangle((s * 0.14, s * 0.16, s * 0.86, s * 0.66), radius=s * 0.24, fill=c)
    d.ellipse((s * 0.22, s * 0.54, s * 0.44, s * 0.84), fill=c)
    dot = s * 0.07
    for x in (0.34, 0.50, 0.66):
        d.ellipse((s * x - dot, s * 0.36, s * x + dot, s * 0.36 + dot * 2), fill=CREAM)


def draw_favorite(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.polygon(
        [
            (s * 0.30, s * 0.16),
            (s * 0.70, s * 0.16),
            (s * 0.70, s * 0.88),
            (s * 0.50, s * 0.68),
            (s * 0.30, s * 0.88),
        ],
        fill=c,
    )
    d.rounded_rectangle((s * 0.30, s * 0.14, s * 0.70, s * 0.42), radius=s * 0.10, fill=c)
    d.ellipse((s * 0.44, s * 0.26, s * 0.56, s * 0.38), fill=CREAM)


def draw_share(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    r = s * 0.11
    d.line([(s * 0.30, s * 0.50), (s * 0.70, s * 0.30)], fill=c, width=int(s * 0.09))
    d.line([(s * 0.30, s * 0.50), (s * 0.70, s * 0.72)], fill=c, width=int(s * 0.09))
    d.ellipse((s * 0.16, s * 0.39, s * 0.16 + r * 2, s * 0.39 + r * 2), fill=c)
    d.ellipse((s * 0.62, s * 0.18, s * 0.62 + r * 2, s * 0.18 + r * 2), fill=c)
    d.ellipse((s * 0.62, s * 0.62, s * 0.62 + r * 2, s * 0.62 + r * 2), fill=c)


def draw_gift(d: ImageDraw.ImageDraw, c: tuple[int, int, int, int], s: int) -> None:
    d.rounded_rectangle((s * 0.22, s * 0.38, s * 0.78, s * 0.80), radius=s * 0.08, fill=c)
    d.rounded_rectangle((s * 0.18, s * 0.30, s * 0.82, s * 0.44), radius=s * 0.06, fill=c)
    d.rectangle((s * 0.46, s * 0.30, s * 0.54, s * 0.80), fill=(255, 251, 246, 255))
    d.ellipse((s * 0.30, s * 0.16, s * 0.50, s * 0.36), outline=c, width=int(s * 0.06))
    d.ellipse((s * 0.50, s * 0.16, s * 0.70, s * 0.36), outline=c, width=int(s * 0.06))


def main() -> None:
    export_tab("home", draw_home)
    export_tab("album", draw_album)
    export_tab("create", draw_create)
    export_tab("plaza", draw_plaza)
    export_tab("me", draw_me)
    export_react("like", draw_like, LIKE)
    export_react("reply", draw_reply, REPLY)
    export_react("favorite", draw_favorite, FAVORITE)
    export_react("share", draw_share, SHARE)
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    big = REACT_SIZE * REACT_SCALE
    img, draw = new_canvas(big)
    draw_gift(draw, ORANGE, big)
    down(img, REACT_SIZE).save(ICON_DIR / "gift.png")
    print(f"wrote icons in {TAB_DIR} and {ICON_DIR}")


if __name__ == "__main__":
    main()
