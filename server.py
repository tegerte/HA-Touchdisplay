from http.server import BaseHTTPRequestHandler, HTTPServer
import cairosvg
from PIL import Image
import io
import re

latest_jpeg = b""


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
            global latest_jpeg

            # SVG viewBox nach rechts erweitern (rechte Achse wird sonst abgeschnitten)
            svg_str = data.decode('utf-8')
            match = re.search(r'viewBox="([^"]*)"', svg_str)
            if match:
                parts = match.group(1).split()
                if len(parts) == 4:
                    w = float(parts[2])
                    parts[2] = str(w * 1.10)  # 10% mehr Platz rechts
                    svg_str = svg_str.replace(match.group(0), f'viewBox="{" ".join(parts)}"')
            data = svg_str.encode('utf-8')

            # 2x rendern, dann runterskalieren fuer scharfes Ergebnis
            png = cairosvg.svg2png(bytestring=data, output_width=1458, output_height=550)
            buf = io.BytesIO()
            img = Image.open(io.BytesIO(png))
            img = img.resize((729, 275), Image.LANCZOS)  # auf Zielgröße strecken
            img.convert("RGB").save(buf, format="JPEG", quality=85)
            latest_jpeg = buf.getvalue()
            self.send_response(200)
            self.send_cors()
            self.end_headers()

    def do_GET(self):
        if self.path == "/temp_graph.jpg":
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(latest_jpeg)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(latest_jpeg)

    def log_message(self, *args):
        pass


HTTPServer(("0.0.0.0", 8765), Handler).serve_forever()