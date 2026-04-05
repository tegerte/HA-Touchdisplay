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
esphome run ha_7zoll_disp.yaml --device /dev/cu.usbmodem14401

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
- Bottom navigation: `buttonmatrix` in `top_layer` with three buttons — each navigates directly via `lvgl.page.show` (Automationen→Licht, Home→main_page, Laden→Charge)
- Pages: `main_page` (outdoor temperature meter + solar table + graph), `Licht` (light toggle), `Charge` (EV charging controls + EV table)

**Charge-Seite Layout (linke Seite):**

- 4 Modus-Buttons in Reihe (y=55, je 120×70): PV, Min+PV, Schnell, Aus
  - Rufen `script.evcc_lademodus` mit `data: modus:` Parameter auf
  - Aktiver Modus wird grün via `select.evcc_e_auto_laden_mode` Sensor (on_value + on_boot sync)
- Modus-Label (y=135, lbl_charge_mode) + SoC-Label (lbl_charge_soc)
- Ladeplan-Button (y=175, 516×80): `charge_60perc_7`, checkable, toggelt `script.evcc_ladeplan_morgen`/`loeschen`
- PV-Start-Button (y=270, 516×80): `charge_PV_Start`, checkable=false, ruft `script.evcc_minpv_aktivieren`
  - Wird grün wenn evcc_mode == "minpv" (via Sensor, nicht via Klick)
- Horizontale Fill-Bars als separate obj-Widgets nach den Buttons:
  - Oben: Ladeleistungs-Balken (dunkelgrün, 0x0D5C2A), max 11kW → 516px
  - Gelbe 1-Phasen-Markierung bei x=189 (3.6kW)
  - Unten: Reichweite-Balken (orange, 0xFF9500), max 400km → 516px

**Info-Tabellen (rechte Seite, x=570, y=35, width=424):**

- Solar-Tabelle auf `main_page` (height=224, 4 Zeilen): PV heute, PV verbl., Autarkie, Sonnenuntg.
- EV-Tabelle auf `Charge` (height=480, 9 Zeilen): Solar %, Reichweite, Ladeende, SOC Soll, Abfahrtszeit, Fahrenergiekosten, Nachgel. Reichweite, Sess. Kosten, Nachgeladen
- Layout: Icon (icons_20, farbig) + Label (montserrat_16, 0xAAAAAA) + Wert (montserrat_28, 0xDDDDDD, RIGHT-aligned)
- Wert-Labels stehen bei x=188, width=216; Icon bei x=0, width=24; Label bei x=28, width=156

**Thermometer-Geometrie:**

- align: TOP_MID + x:-100 → Mittelpunkt bei 412px, Breite 216px → linke Kante 304px, rechte Kante 520px
- Bars: x=30..254 (rechte Kante bar3 = 254), Lücke 50px → Tabelle bei x=570 (gleicher Abstand wie Bars←→Thermo)

**Vertikalbars (linke Seite):**

- Bar 1 (blau, Mercedes Reichweite): x=30, width=44, skaliert auf 400km max
- Bar 2 (orange, PV-Leistung): x=90, width=44, skaliert auf 10kW max
- Bar 3 (grün, Hausbatterie SoC): x=150, width=44, skaliert auf 100%
- Bar 4 (dunkelgrün, EV-Ladeleistung): x=210, width=44, skaliert auf 11kW, sensor.evcc_e_auto_laden_charge_power (in kW)
- Gelbe Markierungslinie bei 3,6 kW (1-phasig) als separates obj-Widget auf y=348
- Jede Bar: Container height=450, fill-from-bottom via Lambda in `on_value`

**Solarenergie-Graph (`main_page`):**

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
- Text sensor: `evcc_mode` — entity_id: `select.evcc_e_auto_laden_mode` (nicht sensor!)
- Time component: `ha_time` (platform: homeassistant) — für relative Zeitberechnung
- Actions called via `homeassistant.action` on button press
- `script.evcc_lademodus` mit `data: modus:` Parameter (pv/minpv/now/off/status)

**Fonts:**

- `montserrat_14/16/18/20/28`: LVGL built-in Fonts (kein €-Zeichen!)
- `montserrat_28_ext`: Eigene gfonts-Montserrat mit €-Glyph (U+20AC), für Kostenfelder
- `icons_20`: MDI, size 20, für Tabellen-Icons
- `icons_30`: MDI, size 30, für Bar-Labels und Charge-Seite Buttons
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
- Solar %, Session-Kosten und Nachgeladen werden auf 1 Nachkommastelle formatiert (snprintf + atof)
- Mercedes-Bar zeigt Reichweite in km (max 400km), nicht SoC%
- Ladeende (`sensor.cw_mt_891_e_end_of_charge`) wird als relative Stunden angezeigt ("in Xh")
- Abfahrtzeit: "unknown" wird als "-" angezeigt
- Kostenfelder nutzen `montserrat_28_ext` für €-Zeichen (LVGL built-in Fonts haben kein €)
- Charge-Seite Fill-Bars müssen NACH den Buttons im YAML stehen (LVGL Z-Order = Reihenfolge)
