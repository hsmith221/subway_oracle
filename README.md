# Subway Oracle

Two Raspberry Pi eInk displays showing the fastest MTA route — one at home (→ work), one at the office (→ home).

## Hardware

| Device | Display |
|--------|---------|
| Office Pi | Adafruit 2.13" 250×122 Quad-Color eInk (IL0373) |
| Home Pi   | Pimoroni Inky Impression 7.3" Spectra 800×480 |

Both require SPI enabled.

---

## Setup (both Pis)

### 1. Flash Pi OS Lite

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash **Raspberry Pi OS Lite (64-bit)** onto a microSD card. In the imager's advanced settings, set hostname, SSH, and WiFi before flashing.

### 2. Enable SPI

```bash
sudo raspi-config
# Interface Options → SPI → Enable
sudo reboot
```

### 3. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/subway_oracle.git
cd subway_oracle
```

### 4. Install dependencies

**Office Pi** (Adafruit IL0373):
```bash
pip3 install -r requirements.txt
```

**Home Pi** (Pimoroni Inky):
```bash
curl https://get.pimoroni.com/inky | bash
pip3 install -r requirements.txt
```

The Pimoroni installer handles all native dependencies. Run it before `pip install`.

---

## Running manually

```bash
# Office Pi
python3 run_office.py

# Home Pi
python3 run_home.py
```

On first boot, `lookup_stops.py` runs automatically to resolve any missing MTA stop IDs from the static GTFS feed.

### Manual stop lookup

If auto-resolution fails, search manually:

```bash
python3 lookup_stops.py search "72 St"
python3 lookup_stops.py search "34 St" R
python3 lookup_stops.py search "23 St"
```

Copy the resulting stop IDs into `config.py`.

---

## Autostart with systemd

**Office Pi:**
```bash
sudo cp subway_oracle_office.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable subway_oracle_office
sudo systemctl start subway_oracle_office
```

**Home Pi:**
```bash
sudo cp subway_oracle_home.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable subway_oracle_home
sudo systemctl start subway_oracle_home
```

Check logs:
```bash
journalctl -u subway_oracle_office -f
journalctl -u subway_oracle_home -f
```

---

## Notes

- The Inky Impression 7.3" takes ~30 seconds to fully refresh — this is normal.
- Both displays need SPI enabled via `raspi-config`.
- Route data refreshes every 60 seconds; MTA feed is cached for 30 seconds.
- Stop IDs resolved by `lookup_stops.py` are cached in `/tmp/mta_gtfs_stops.txt`. Delete this file to force a fresh download.
- Train bullet assets are generated automatically on first run in `assets/`.
