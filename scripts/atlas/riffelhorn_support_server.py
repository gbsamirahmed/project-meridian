"""Loopback-only evaluation delivery; transparent missing support, never AWS fill."""
import argparse
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import riffelhorn_support as support
import riffelhorn_terrain as terrain


def serve(data, port):
    manifest = support.verify(data)
    root = data / support.PRODUCT

    class Handler(BaseHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('X-Meridian-Product', manifest['identity'])
            super().end_headers()

        def do_GET(self):
            match = re.fullmatch(r'/tiles/(\d+)/(\d+)/(\d+)\.png', self.path)
            if not match:
                self.send_error(404)
                return
            z, x, y = map(int, match.groups())
            path = root / f'tiles/{z}/{x}/{y}.png'
            if not path.exists():
                self.send_error(404, 'Outside fully supported regional tile inventory')
                return
            body = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'public,max-age=3600')
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    print('SERVING', port, flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4181)
    args = parser.parse_args()
    serve(terrain.resolve_storage_roots(require_data=True).data, args.port)
