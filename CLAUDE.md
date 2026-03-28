# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ESPHome configuration for a **Makerfabs MaTouch ESP32-S3 7-inch display** integrated with Home Assistant. The display uses an RGB parallel interface (1024×600) with a GT911 capacitive touchscreen and LVGL for the UI.

## Key Commands

Common operations (`esphome` is available directly without activating the virtualenv):

```bash
# Compile only (no upload)
esphome compile ha_7zoll_disp.yaml

# Compile and upload via OTA (device must be on WiFi)
esphome run ha_7zoll_disp.yaml

# Upload via USB serial (device IP: 192.168.1.65)
esphome run ha_7zoll_disp.yaml --device /dev/cu.usbmodem114401

# View serial logs (use IP directly, mDNS port 5353 conflicts on macOS)
esphome logs ha_7zoll_disp.yaml --device 192.168.1.65

# Validate config syntax
esphome config ha_7zoll_disp.yaml
```

WiFi credentials are stored in `secrets.yaml` (not committed).

## Architecture

Everything lives in a single file: **`ha_7zoll_disp.yaml`**

**Hardware:**

- ESP32-S3, 16MB flash, octal PSRAM at 80MHz, 240MHz CPU
- Display: `rpi_dpi_rgb` platform, 1024×600, parallel RGB
- Touch: GT911 over I2C (SDA=GPIO17, SCL=GPIO18)
- Backlight: LEDC PWM on GPIO10 (inverted, min_power 7%)

**UI Structure (LVGL):**

- Global theme defined once in `lvgl.theme` — applies to all buttons, switches, sliders, buttonmatrix
- `header_footer` style definition used for page headers and the bottom navigation bar (bg: 0x252D38→0x1C2128 gradient, dark theme)
- Bottom navigation: `buttonmatrix` in `top_layer` with three buttons (prev page / home / next page)
- Pages: `main_page` (outdoor temperature meter + solar table + graph), `Licht` (light toggle), `Charge` (EV charging controls + EV table)

**Info-Tabellen (rechte Seite, x=570, y=35, width=424):**

- Solar-Tabelle auf `main_page` (height=224, 4 Zeilen): PV heute, PV verbl., Autarkie, Sonnenuntg.
- EV-Tabelle auf `Charge` (height=480, 9 Zeilen): Solar %, Reichweite, Ladeende, SOC Soll, Abfahrtszeit, Fahrenergiekosten, Nachgel. Reichweite, Sess. Kosten, Nachgeladen
- Layout: Icon (icons_20, farbig) + Label (montserrat_16, 0xAAAAAA) + Wert (montserrat_28, 0xDDDDDD, RIGHT-aligned)
- Wert-Labels stehen bei x=188, width=216; Icon bei x=0, width=24; Label bei x=28, width=156

**Thermometer-Geometrie:**

- align: TOP_MID + x:-100 → Mittelpunkt bei 412px, Breite 216px → linke Kante 304px, rechte Kante 520px
- Bars: x=30..254 (rechte Kante bar3 = 254), Lücke 50px → Tabelle bei x=570 (gleicher Abstand wie Bars←→Thermo)

**Vertikalbars (linke Seite):**

- Bar 1 (blau, Mercedes Reichweite): x=30, skaliert auf 400km max
- Bar 2 (orange, PV-Leistung): x=114, skaliert auf 10kW max
- Bar 3 (grün, Hausbatterie SoC): x=198, skaliert auf 100%
- Jede Bar: Container height=450, fill-from-bottom via Lambda in `on_value`

**Temperaturverlauf-Graph (`main_page`):**

- `online_image` Komponente holt JPEG von Homeserver (192.168.1.145:8765) alle 2 min
- LVGL `image` Widget: x=265, y=270, width=729, height=275
- `on_download_finished` → `lvgl.image.update` zum Aktualisieren des Widgets
- Benötigt `http_request` Komponente (bereits konfiguriert, verify_ssl: false)
- Homeserver IP konfigurierbar via `substitutions.graph_server_ip`

**Python-Bildserver (`/opt/graph_server/server.py` auf Homeserver 192.168.1.145):**

```python
# Läuft als systemd-Dienst: graph-server.service (User=tegerte)
# POST /save   → empfängt SVG, konvertiert zu JPEG 729x275 via cairosvg+Pillow
# GET /temp_graph.jpg → liefert letztes JPEG mit Content-Length Header
# CORS-Headers für alle Requests (browser_mod sendet von HA-Frontend)
```

Abhängigkeiten: `python3-cairosvg`, `python3-pil` (via apt)

**HA-Automation (Temp-Graph Screenshot):**

- Trigger: alle 15 min
- browser_id: `browser_mod_5d88ed49_a3e9779f` (Chromium auf Homeserver)
- Navigiert zu `/tablett-pv/0`, wartet 8s, führt JS aus
- JS: `deepQuery()` traversiert Shadow DOMs, serialisiert SVG, POST an Server
- SVG wird server-seitig auf 729×275px gerendert

**Home Assistant Integration:**

- Sensoren via `platform: homeassistant`
- Binary sensor: `evcc_ladeplan_aktiv` (charging plan active state)
- Text sensor: `ts_remote_light` (light on/off/unavailable state)
- Actions called via `homeassistant.action` on button press

**Fonts:**

- `montserrat_14/16/18/20/28`: aus gfonts
- `icons_20`: MDI, size 20, für Tabellen-Icons
- `icons_30`: MDI, size 30, für Bar-Labels
- `icons_100`: MDI, size 100, für große Icons
- Beim Hinzufügen neuer MDI-Icons: Codepoint zur `glyphs`-Liste hinzufügen

**Globals:**

- `brightness_global` (float, persisted): display brightness %
- `youliang` (int, persisted): brightness value (default 60)

## Important Notes

- The needle value for the temperature meter uses `x * 10` scaling (scale range -100 to 400 maps to -10°C to 40°C)
- The `charge_60perc_7` button toggles between two HA scripts depending on `evcc_ladeplan_aktiv` state
- Backlight control code exists but is commented out
- Build artifacts are in `.esphome/` (not committed per `.gitignore`)
- mDNS port 5353 conflicts on macOS — always use `--device 192.168.1.65` for logs
- `esphome run` always in foreground, never as background process
- text_sensor `on_value` lambdas format values with units (kWh, %, km, €)
- Solar %  und Session-Kosten werden auf 1 Nachkommastelle formatiert (snprintf + atof)
- Mercedes-Bar zeigt Reichweite in km (max 400km), nicht SoC%
