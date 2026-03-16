# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ESPHome configuration for a **Makerfabs MaTouch ESP32-S3 7-inch display** integrated with Home Assistant. The display uses an RGB parallel interface (1024×600) with a GT911 capacitive touchscreen and LVGL for the UI.

## Key Commands

The ESPHome toolchain is installed in a local virtualenv at `esphome-2026-1-5/`. Activate it before running commands:

```bash
source esphome-2026-1-5/bin/activate
```

Common operations:
```bash
# Compile only (no upload)
esphome compile ha_7zoll_disp.yaml

# Compile and upload via OTA (device must be on WiFi)
esphome run ha_7zoll_disp.yaml

# Upload via USB serial
esphome upload ha_7zoll_disp.yaml --device /dev/ttyUSB0

# View serial logs
esphome logs ha_7zoll_disp.yaml

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
- `header_footer` style definition used for page headers and the bottom navigation bar
- Bottom navigation: `buttonmatrix` in `top_layer` with three buttons (prev page / home / next page)
- Pages: `main_page` (outdoor temperature meter), `Licht` (light toggle), `Charge` (EV charging controls)

**Home Assistant Integration:**
- Sensors pulled via `platform: homeassistant` — outdoor temp, EV battery SoC, charging mode
- Binary sensor: `evcc_ladeplan_aktiv` (charging plan active state)
- Text sensor: `ts_remote_light` (light on/off/unavailable state)
- Actions called via `homeassistant.action` on button press

**Globals:**
- `brightness_global` (float, persisted): display brightness %
- `youliang` (int, persisted): brightness value (default 60)

**Fonts:**
- `large_font`: Roboto from gfonts, size 32
- `icons_100`: Material Design Icons from `fonts/materialdesignicons-webfont.ttf`, size 100 — only specific MDI codepoints are included to save flash space

## Important Notes

- When adding new MDI icons to `icons_100`, the codepoint must be added to the `glyphs` list — icons not in the list will render as blank
- The needle value for the temperature meter uses `x * 10` scaling (scale range -100 to 400 maps to -10°C to 40°C)
- The `charge_60perc_7` button toggles between two HA scripts depending on `evcc_ladeplan_aktiv` state
- Backlight control code exists but is commented out — the `display_backlight` light entity and `on_idle`/`on_release` handlers are present as comments for future use
- Build artifacts are in `.esphome/` (not committed per `.gitignore`)
