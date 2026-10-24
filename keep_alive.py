from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot AI Server Architect is Alive!")
    def log_message(self, *args): pass

def _run():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

def keep_alive():
    t = threading.Thread(target=_run)
    t.daemon = True
    t.start()
