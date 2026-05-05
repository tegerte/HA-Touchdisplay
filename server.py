from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image
import io
import re
import subprocess


def render_svg(svg_bytes, width, height):
    """SVG-Bytes mit rsvg-convert zu PNG-Bytes rendern.
    librsvg respektiert das SVG-Spec-konforme Color/Fill-Modell korrekt —
    cairosvg hatte hier auf .apexcharts-text-Elementen Falschfarben gerendert.
    """
    proc = subprocess.run(
        ['rsvg-convert', '-w', str(width), '-h', str(height), '-f', 'png'],
        input=svg_bytes, capture_output=True, check=True)
    return proc.stdout

latest_jpeg = b""
latest_jpeg_small = b""
latest_png_small = b""
latest_svg = b""
latest_svg_processed = b""


class Handler(BaseHTTPRequestHandler):
    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Content-Length")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            global latest_jpeg, latest_jpeg_small, latest_png_small, latest_svg, latest_svg_processed
            latest_svg = data

            svg_str = data.decode('utf-8')

            # ApexCharts nutzt CSS-Custom-Properties (var(--primary-text-color))
            # fuer Achsen-Labels. CairoSVG kann die nicht aufloesen — also
            # textuell durch konkrete Farben ersetzen.
            svg_str = re.sub(r'var\(--[^)]+\)', '#ffffff', svg_str)

            # <foreignObject> mit eingebettetem HTML/CSS (Legend-Layout) raus —
            # CairoSVG verarbeitet die HTML-Style-Cascade auf eine Weise, die
            # auf .apexcharts-text-Elementen die Schriftfarbe verfaelscht
            # (rendert fill="#ffffff" als gruen). Ohne foreignObject werden die
            # Achsen-Labels direkt aus den fill-Attributen der <text>-Elemente
            # geseh.
            svg_str = re.sub(
                r'<foreignObject[\s\S]*?</foreignObject>', '', svg_str)

            # Achsen-Schriftgroesse anheben (Default 11/12 px ist nach Skalierung
            # auf 580 px Output unleserlich klein). Direkt im font-size-Attribut
            # patchen — kein <style>-Block, weil CairoSVG damit crasht.
            def _bump_font(m):
                pre, size_attr, mid = m.group(1), m.group(2), m.group(3)
                # size_attr ist z.B. font-size="11px" → wir verdreifachen die Zahl
                new_size = re.sub(
                    r'(\d+(?:\.\d+)?)',
                    lambda nm: str(int(float(nm.group(1)) * 3.0)),
                    size_attr, count=1)
                return f'{pre}{new_size}{mid}'
            svg_str = re.sub(
                r'(<text[^>]*?)(font-size="[^"]*")([^>]*?class="apexcharts-text[^"]*")',
                _bump_font, svg_str)

            latest_svg_processed = svg_str.encode('utf-8')

            # MAtouch-Variante: viewBox um 10% nach rechts erweitern, damit die
            # rechte Y-Achsen-Beschriftung nicht weggeclippt wird.
            svg_expanded = svg_str
            match = re.search(r'viewBox="([^"]*)"', svg_str)
            if match:
                parts = match.group(1).split()
                if len(parts) == 4:
                    parts[2] = str(float(parts[2]) * 1.10)
                    svg_expanded = svg_str.replace(
                        match.group(0), f'viewBox="{" ".join(parts)}"')

            # 2x Supersampling: SVG bei doppelter Zielaufloesung rastern,
            # dann via BOX-Filter 4-Pixel-Mittelwert auf Zielgroesse.
            # Kein LANCZOS-Ringing (BOX ist arithmetisches Mittel ohne Lobes),
            # subpixel-genaues Antialiasing entlang der Stroke-Kanten.

            # MAtouch (1024x600): 729x275 (rendered 1458x550) — mit viewBox-Hack
            png_large = render_svg(svg_expanded.encode('utf-8'), 1458, 550)
            buf = io.BytesIO()
            Image.open(io.BytesIO(png_large)).resize(
                (729, 275), Image.BOX).convert("RGB").save(
                buf, format="JPEG", quality=95, subsampling=0)
            latest_jpeg = buf.getvalue()

            # Waveshare (800x480): 580x185 (rendered 1160x370) — vorerst auch
            # mit viewBox-Hack, bis der ohne-Hack-Fall sauber funktioniert.
            png_small = render_svg(svg_expanded.encode('utf-8'), 1160, 370)
            small_rgb = Image.open(io.BytesIO(png_small)).resize(
                (580, 185), Image.BOX).convert("RGB")
            buf2 = io.BytesIO()
            small_rgb.save(buf2, format="JPEG", quality=95, subsampling=0)
            latest_jpeg_small = buf2.getvalue()

            # Lossless PNG-Variante zum Vergleichen — keine JPEG-Block-Artefakte.
            buf3 = io.BytesIO()
            small_rgb.save(buf3, format="PNG", optimize=True)
            latest_png_small = buf3.getvalue()
            self.send_response(200)
            self.send_cors()
            self.end_headers()

    def do_GET(self):
        if self.path == "/temp_graph.jpg":
            payload, ctype = latest_jpeg, "image/jpeg"
        elif self.path == "/temp_graph_580.jpg":
            payload, ctype = latest_jpeg_small, "image/jpeg"
        elif self.path == "/temp_graph_580.png":
            payload, ctype = latest_png_small, "image/png"
        elif self.path == "/raw.svg":
            payload, ctype = latest_svg, "image/svg+xml"
        elif self.path == "/processed.svg":
            payload, ctype = latest_svg_processed, "image/svg+xml"
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


HTTPServer(("0.0.0.0", 8765), Handler).serve_forever()