"""
Renders to_home routes on Adafruit 2.13" 250x122 Quad-Color eInk (IL0373 driver).
Colors available: black, white, red, yellow (mapped from MTA colors).
"""

import os
from PIL import Image, ImageDraw, ImageFont
from assets.generate_bullets import ensure_bullets, ASSETS_DIR

WIDTH, HEIGHT = 250, 122
PALETTE = {
    "black":  (0,   0,   0),
    "white":  (255, 255, 255),
    "red":    (255, 0,   0),
    "yellow": (255, 200, 0),
}

# eInk color mapping: 6 → red (closest to green on this display), R/W → yellow
COLOR_6 = PALETTE["red"]
COLOR_RW = PALETTE["yellow"]
COLOR_Q = PALETTE["yellow"]


def _load_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _fmt_time(dt):
    if dt is None:
        return "--:--"
    return dt.strftime("%-I:%M%p").lower()


def render(routes, updated_at):
    """
    routes: output of calculate_routes("to_home")
    updated_at: datetime of last refresh
    Returns PIL Image (250x122, RGB)
    """
    ensure_bullets()
    img = Image.new("RGB", (WIDTH, HEIGHT), PALETTE["white"])
    draw = ImageDraw.Draw(img)

    font_sm = _load_font(10)
    font_md = _load_font(11)
    font_tiny = _load_font(9)

    bullet_size = 18
    bullet_rw = Image.open(os.path.join(ASSETS_DIR, "RW_bullet_small.bmp")).resize((bullet_size, bullet_size))
    bullet_6 = Image.open(os.path.join(ASSETS_DIR, "6_bullet_small.bmp")).resize((bullet_size, bullet_size))
    bullet_q = Image.open(os.path.join(ASSETS_DIR, "Q_bullet_small.bmp")).resize((bullet_size, bullet_size))

    route_a = routes["route_a"]
    route_b = routes["route_b"]
    winner = routes["winner"]

    row1_y = 8
    row2_y = 42
    footer_y = 108

    # --- Row 1: R/W → Q ---
    img.paste(bullet_rw, (4, row1_y))
    draw.text((24, row1_y + 3), "→", fill=PALETTE["black"], font=font_md)
    img.paste(bullet_q, (36, row1_y))
    if route_a["valid"]:
        draw.text((58, row1_y + 2), f"departs {_fmt_time(route_a['departs_dt'])}", fill=PALETTE["black"], font=font_sm)
        draw.text((58, row1_y + 14), f"arrive ~{_fmt_time(route_a['arrives_dt'])}", fill=PALETTE["black"], font=font_sm)
    else:
        draw.text((58, row1_y + 8), "no trains found", fill=PALETTE["black"], font=font_sm)
    if winner == "A":
        draw.text((230, row1_y + 8), "✓", fill=PALETTE["black"], font=font_md)

    # --- Row 2: 6 ---
    img.paste(bullet_6, (4, row2_y))
    if route_b["valid"]:
        draw.text((28, row2_y + 2), f"departs {_fmt_time(route_b['departs_dt'])}", fill=PALETTE["black"], font=font_sm)
        draw.text((28, row2_y + 14), f"arrive ~{_fmt_time(route_b['arrives_dt'])}", fill=PALETTE["black"], font=font_sm)
    else:
        draw.text((28, row2_y + 8), "no trains found", fill=PALETTE["black"], font=font_sm)
    if winner == "B":
        draw.text((230, row2_y + 8), "✓", fill=PALETTE["black"], font=font_md)

    # --- Divider ---
    draw.line([(0, 76), (WIDTH, 76)], fill=PALETTE["black"], width=1)

    # --- Savings line ---
    if routes["savings_minutes"] is not None and routes["savings_minutes"] > 0:
        winner_label = "R/W→Q" if winner == "A" else "6"
        draw.text((4, 82), f"Take the {winner_label} — saves {routes['savings_minutes']} min", fill=PALETTE["black"], font=font_sm)

    # --- Footer ---
    draw.text((4, footer_y), f"updated {_fmt_time(updated_at)}", fill=PALETTE["black"], font=font_tiny)

    return img


def show(routes, updated_at):
    """Render and push to physical eInk display."""
    img = render(routes, updated_at)

    import board
    import busio
    import digitalio
    import adafruit_il0373

    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    ecs = digitalio.DigitalInOut(board.CE0)
    dc = digitalio.DigitalInOut(board.D22)
    srcs = digitalio.DigitalInOut(board.CE1)  # SRAM chip select (PID 6366 has onboard SRAM)
    rst = digitalio.DigitalInOut(board.D27)
    busy = digitalio.DigitalInOut(board.D17)

    display = adafruit_il0373.IL0373(
        spi, ecs, dc, srcs, rst, busy,
        width=WIDTH, height=HEIGHT,
        highlight_color=0xFF0000,
        rotation=270,
    )

    bg = display.display_bus
    g = display.root_group if hasattr(display, "root_group") else None

    # Convert PIL image to displayio bitmap via raw bytes
    import displayio
    bitmap = displayio.Bitmap(WIDTH, HEIGHT, 4)
    palette = displayio.Palette(4)
    palette[0] = 0xFFFFFF  # white
    palette[1] = 0x000000  # black
    palette[2] = 0xFF0000  # red
    palette[3] = 0xFFD700  # yellow

    def nearest_palette(r, g_ch, b):
        colors = [
            (255, 255, 255, 0),
            (0, 0, 0, 1),
            (255, 0, 0, 2),
            (255, 215, 0, 3),
        ]
        best = min(colors, key=lambda c: (r - c[0])**2 + (g_ch - c[1])**2 + (b - c[2])**2)
        return best[3]

    px = img.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g_ch, b = px[x, y]
            bitmap[x, y] = nearest_palette(r, g_ch, b)

    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    group = displayio.Group()
    group.append(tile_grid)
    display.root_group = group
    display.refresh()
