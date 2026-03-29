from http.server import BaseHTTPRequestHandler, HTTPServer
import cairosvg
from PIL import Image
import io

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
            png = cairosvg.svg2png(bytestring=data, output_width=729)
            buf = io.BytesIO()
            img = Image.open(io.BytesIO(png))
            img = img.resize((729, 275), Image.LANCZOS)  # auf Zielgröße strecken
            img.convert("RGB").save(buf, format="JPEG", quality=85)
            latest_jpeg = buf.getvalue()
            #Image.open(io.BytesIO(png)).convert("RGB").save(buf, format="JPEG", quality=85)
            #latest_jpeg = buf.getvalue()
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