"""
Renders to_work routes on Pimoroni Inky Impression 7.3" Spectra (800x480, 7 colors).
"""

import os
from PIL import Image, ImageDraw, ImageFont
from assets.generate_bullets import ensure_bullets, ASSETS_DIR

WIDTH, HEIGHT = 800, 480

MTA_GREEN  = (0,   147, 60)
MTA_YELLOW = (252, 204, 10)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
DARK_GRAY  = (40,  40,  40)


def _load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
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


def _draw_route_card(draw, img, x, y, w, h, route, bullet_names):
    """Draw a single route card at position (x,y) with dimensions (w,h)."""
    draw.rectangle([x, y, x + w, y + h], fill=WHITE, outline=DARK_GRAY, width=2)

    bullet_size = 60
    bx = x + 16
    by = y + 16
    for i, bname in enumerate(bullet_names):
        bmp = Image.open(os.path.join(ASSETS_DIR, f"{bname}_bullet_large.bmp")).resize((bullet_size, bullet_size))
        img.paste(bmp, (bx + i * (bullet_size + 8), by))
        if i < len(bullet_names) - 1:
            draw.text((bx + i * (bullet_size + 8) + bullet_size + 1, by + 18), "→",
                      fill=BLACK, font=_load_font(28, bold=True))

    text_y = by + bullet_size + 16
    font_body = _load_font(26)
    font_total = _load_font(24, bold=True)

    if route["valid"]:
        draw.text((x + 16, text_y),      f"departs {_fmt_time(route['departs_dt'])}", fill=BLACK, font=font_body)
        draw.text((x + 16, text_y + 36), f"arrive ~{_fmt_time(route['arrives_dt'])}", fill=BLACK, font=font_body)
        draw.text((x + 16, text_y + 72), f"total: {route['total_minutes']} min", fill=DARK_GRAY, font=font_total)
    else:
        draw.text((x + 16, text_y + 36), "no trains found", fill=DARK_GRAY, font=font_body)


def render(routes, updated_at):
    """
    routes: output of calculate_routes("to_work")
    updated_at: datetime of last refresh
    Returns PIL Image (800x480, RGB)
    """
    ensure_bullets()
    img = Image.new("RGB", (WIDTH, HEIGHT), (230, 230, 230))
    draw = ImageDraw.Draw(img)

    card_w = (WIDTH - 48) // 2
    card_h = 260
    card_y = 16

    # Route A card (Q → R/W)
    _draw_route_card(draw, img, 16, card_y, card_w, card_h, routes["route_a"], ["Q", "RW"])

    # Route B card (6)
    _draw_route_card(draw, img, 16 + card_w + 16, card_y, card_w, card_h, routes["route_b"], ["6"])

    # Winner banner
    banner_y = card_y + card_h + 16
    banner_h = HEIGHT - banner_y - 48
    winner = routes["winner"]
    savings = routes["savings_minutes"]

    if winner is not None:
        banner_color = MTA_YELLOW if winner == "B" else MTA_GREEN
        draw.rectangle([16, banner_y, WIDTH - 16, banner_y + banner_h], fill=banner_color)

        winner_name = "6" if winner == "B" else "R/W → Q"
        font_banner = _load_font(52, bold=True)
        banner_text = f"✓  TAKE THE {winner_name}"
        if savings and savings > 0:
            banner_text += f"   saves you {savings} min"

        text_color = WHITE if winner == "B" else BLACK
        bbox = draw.textbbox((0, 0), banner_text, font=font_banner)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (WIDTH - tw) / 2
        ty = banner_y + (banner_h - th) / 2
        draw.text((tx, ty), banner_text, fill=text_color, font=font_banner)
    else:
        draw.rectangle([16, banner_y, WIDTH - 16, banner_y + banner_h], fill=DARK_GRAY)
        draw.text((WIDTH // 2 - 100, banner_y + 20), "no service data", fill=WHITE, font=_load_font(36, bold=True))

    # Footer
    font_footer = _load_font(20)
    draw.text((16, HEIGHT - 36), f"updated {_fmt_time(updated_at)}", fill=DARK_GRAY, font=font_footer)

    return img


_inky = None


def _init_inky():
    global _inky
    import gpiod
    import spidev as _spidev
    from gpiod.line import Direction, Edge, Value
    from datetime import timedelta
    import gpiodevice

    CS_PIN    = 8
    DC_PIN    = 22
    RESET_PIN = 27
    BUSY_PIN  = 17

    chip = gpiodevice.find_chip_by_platform()
    lines = chip.request_lines(consumer="inky", config={
        DC_PIN:    gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
        RESET_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
        BUSY_PIN:  gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.RISING,
                                      debounce_period=timedelta(milliseconds=10)),
    })

    class _GPIO:
        def set_value(self, pin, value):
            if pin != CS_PIN:
                lines.set_value(pin, value)
        def get_value(self, pin):
            return lines.get_value(pin)
        def wait_edge_events(self, timeout=None):
            return lines.wait_edge_events(timeout)
        def read_edge_events(self, max_events=1):
            return lines.read_edge_events(max_events)

    class _SpiDev(_spidev.SpiDev):
        @property
        def no_cs(self): return False
        @no_cs.setter
        def no_cs(self, _): pass

    from inky.inky_ac073tc1a import Inky
    import types
    _inky = Inky(gpio=_GPIO(), spi_bus=_SpiDev())

    # inky's _spi_write sends one byte at a time via xfer(), causing hardware CS
    # to toggle between every byte. xfer2() holds CS low for the entire transfer,
    # which is what the display expects per command.
    def _spi_write(self, dc, values):
        self._gpio.set_value(self.dc_pin, Value.ACTIVE if dc else Value.INACTIVE)
        if isinstance(values, str):
            values = [ord(c) for c in values]
        values = list(values)
        chunk = 4096
        for i in range(0, len(values), chunk):
            self._spi_bus.xfer2(values[i:i + chunk])

    _inky._spi_write = types.MethodType(_spi_write, _inky)


def show(routes, updated_at):
    """Render and push to physical Inky Impression display."""
    global _inky
    if _inky is None:
        _init_inky()
    img = render(routes, updated_at)
    _inky.set_image(img)
    _inky.show()
