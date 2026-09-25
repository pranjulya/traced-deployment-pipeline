"""Local notification sink (Phase 04).

A tiny webhook receiver that records Alertmanager notifications so delivery can
be tested end to end without any external destination. Receipts can be kept in
memory and, when P09_SINK_FILE is set, appended as JSON lines for drill
evidence.

    python deploy/sink/notify_sink.py [port]

GET /alerts returns the recorded receipts as JSON.
"""

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Sink:
    def __init__(self, file_path=None):
        self._received = []
        self._lock = threading.Lock()
        self._file_path = file_path

    def record(self, payload):
        with self._lock:
            self._received.append(payload)
            if self._file_path:
                with open(self._file_path, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload) + "\n")

    def received(self):
        with self._lock:
            return list(self._received)

    def clear(self):
        with self._lock:
            self._received.clear()


def make_handler(sink, body_max_bytes=1_000_000):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path != "/alerts":
                self.send_response(404)
                self.end_headers()
                return
            self._json(200, sink.received())

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
    sink = Sink(file_path=os.environ.get("P09_SINK_FILE"))
    server = create_server(sink, port=port)
    print(f"local sink listening on http://127.0.0.1:{port}/alerts")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main(sys.argv)
