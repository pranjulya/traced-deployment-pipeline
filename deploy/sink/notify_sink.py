"""Local notification sink (Phase 04).

A tiny webhook receiver that records Alertmanager notifications so delivery can
be tested end to end without any external destination. Run with:

    python deploy/sink/notify_sink.py [port]
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Sink:
    def __init__(self):
        self._received = []
        self._lock = threading.Lock()

    def record(self, payload):
        with self._lock:
            self._received.append(payload)

    def received(self):
        with self._lock:
            return list(self._received)

    def clear(self):
        with self._lock:
            self._received.clear()


def make_handler(sink, body_max_bytes=1_000_000):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/alerts":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", 0))
            if length > body_max_bytes:
                self.send_response(413)
                self.end_headers()
                return
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                return
            sink.record(payload)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            return None

    return Handler


def create_server(sink, host="127.0.0.1", port=9099):
    return ThreadingHTTPServer((host, port), make_handler(sink))


def main(argv):
    port = int(argv[1]) if len(argv) > 1 else 9099
    sink = Sink()
    server = create_server(sink, port=port)
    print(f"local sink listening on http://127.0.0.1:{port}/alerts")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main(sys.argv)
