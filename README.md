# HA-Touchdisplay

ESPHome-Konfiguration für ein **Makerfabs MaTouch ESP32-S3 7-Zoll-Display** mit Home Assistant Integration.

## Hardware

- **MCU:** ESP32-S3, 16 MB Flash, Octal PSRAM, 240 MHz
- **Display:** 1024×600 RGB Parallel Interface
- **Touch:** GT911 kapazitiv (I2C)
- **Backlight:** LEDC PWM (GPIO10)

## UI-Seiten

| Seite       | Inhalt                                    |
| ----------- | ----------------------------------------- |
| `main_page` | Außentemperatur-Anzeige (Tachometer)      |
| `Licht`     | Licht ein/aus schalten                    |
| `Charge`    | E-Auto Ladesteuerung (PV-Laden, Zeitplan) |

Navigation über eine Buttonmatrix am unteren Bildschirmrand (zurück / Home / weiter).

## Home Assistant Integration

- Außentemperatur-Sensor
- E-Auto Batterie-SoC & Lademodus (evcc)
- Ladeplan-Status (`evcc_ladeplan_aktiv`)
- Lichtsteuerung via HA-Action

## Dateien

- `ha_7zoll_disp.yaml` — komplette ESPHome-Konfiguration
- `secrets.yaml` — WLAN-Zugangsdaten (nicht im Repo)
- `fonts/` — Material Design Icons TTF

## Kompilieren & Flashen

```bash
esphome compile ha_7zoll_disp.yaml   # nur kompilieren
esphome run ha_7zoll_disp.yaml       # kompilieren + OTA-Upload
esphome logs ha_7zoll_disp.yaml      # serielle Logs anzeigen
```

## Ressourcen

- [ESPHome LVGL Dokumentation](https://esphome.io/cookbook/lvgl/)
- [Makerfabs MaTouch ESP32-S3](https://www.makerfabs.com/matouch-esp32-s3.html)
- [Material Design Icons](https://materialdesignicons.com/)
