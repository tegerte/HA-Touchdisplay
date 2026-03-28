# HA-Touchdisplay

ESPHome-Konfiguration für ein **Makerfabs MaTouch ESP32-S3 7-Zoll-Display** mit Home Assistant Integration.

## Hardware

- **MCU:** ESP32-S3, 16 MB Flash, Octal PSRAM, 240 MHz
- **Display:** 1024×600 RGB Parallel Interface
- **Touch:** GT911 kapazitiv (I2C)
- **Backlight:** LEDC PWM (GPIO10)

## UI-Seiten

| Seite       | Inhalt                                                                |
| ----------- | --------------------------------------------------------------------- |
| `main_page` | Thermometer, Vertikalbars, Solar-Infotabelle, Temperaturverlauf-Graph |
| `Licht`     | Licht ein/aus schalten                                                |
| `Charge`    | E-Auto Ladesteuerung (PV-Laden, Zeitplan) + EV-Infotabelle            |

Navigation über eine Buttonmatrix am unteren Bildschirmrand (zurück / Home / weiter).

## Home Assistant Integration

- Außentemperatur-Sensor
- E-Auto Batterie-SoC & Lademodus (evcc)
- Ladeplan-Status (`evcc_ladeplan_aktiv`)
- Lichtsteuerung via HA-Action
- Solar-Sensoren: PV heute, PV verbleibend, Autarkie, Sonnenuntergang
- EV-Sensoren: Reichweite, Ladeende, SOC-Soll, Abfahrtszeit, Kosten, Session-Daten

## Temperaturverlauf-Graph

Der Außentemperaturverlauf wird als Graph auf `main_page` angezeigt. Die Pipeline:

```
HA-Automation (browser_mod) → Python-Server (port 8765) → ESP32 (online_image)
```

1. **HA-Automation** navigiert alle 15 min zu einer Lovelace-View mit apexcharts-card,
   rendert das SVG via JavaScript und schickt es per POST an den Python-Server
2. **Python-Server** (`/opt/graph_server/server.py` auf dem Homeserver) konvertiert
   SVG → JPEG via cairosvg + Pillow und speichert es im RAM
3. **ESP32** holt das JPEG alle 2 min via `online_image` und zeigt es via LVGL `image`-Widget an

### Server einrichten (Linux Mint / Debian)

```bash
sudo apt install python3-cairosvg python3-pil
sudo mkdir -p /opt/graph_server
# server.py erstellen (siehe CLAUDE.md)
sudo nano /etc/systemd/system/graph-server.service
sudo systemctl enable --now graph-server
```

### Abhängigkeiten

- **browser_mod** (HACS) — für JavaScript-Ausführung im Browser
- **apexcharts-card** (HACS) — für den Temperaturverlauf-Graph

## Dateien

- `ha_7zoll_disp.yaml` — komplette ESPHome-Konfiguration
- `secrets.yaml` — WLAN-Zugangsdaten (nicht im Repo)
- `fonts/` — Material Design Icons TTF

## Kompilieren & Flashen

```bash
esphome compile ha_7zoll_disp.yaml        # nur kompilieren
esphome run ha_7zoll_disp.yaml            # kompilieren + OTA-Upload
esphome run ha_7zoll_disp.yaml --device /dev/cu.usbmodem114401  # via USB
esphome logs ha_7zoll_disp.yaml           # serielle Logs anzeigen
```

## Ressourcen

- [ESPHome LVGL Dokumentation](https://esphome.io/cookbook/lvgl/)
- [Makerfabs MaTouch ESP32-S3](https://www.makerfabs.com/matouch-esp32-s3.html)
- [Material Design Icons](https://materialdesignicons.com/)
