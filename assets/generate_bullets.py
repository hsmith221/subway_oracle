"""
Generates train bullet BMP files if they don't exist.
Called automatically by display modules on first run.
"""

import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))

BULLETS = [
    ("6",   "#00933C", "white", "6"),
    ("Q",   "#FCCC0A", "white", "Q"),
    ("RW",  "#FCCC0A", "white", "R/W"),
]

SIZES = [
    ("small", 18),
    ("large", 60),
]


def _draw_bullet(label, fill, text_color, text, size):
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    draw.ellipse([0, 0, size - 1, size - 1], fill=fill)

    font_size = max(6, int(size * 0.38)) if len(text) > 1 else max(8, int(size * 0.5))
    font = None
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default(size=font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), text, fill=text_color, font=font)
    return img


def ensure_bullets():
    for name, fill, text_color, text in BULLETS:
        for size_label, px in SIZES:
            path = os.path.join(ASSETS_DIR, f"{name}_bullet_{size_label}.bmp")
            if not os.path.exists(path):
                img = _draw_bullet(name, fill, text_color, text, px)
                img.save(path, "BMP")
                print(f"Generated {path}")


if __name__ == "__main__":
    ensure_bullets()
