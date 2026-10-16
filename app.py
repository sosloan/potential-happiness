import json
import os
import shutil
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
MAX_REQUEST_BYTES = 1_000_000
MAX_QUERY_LENGTH = 10_000
JQ_TIMEOUT_SECONDS = 5


def run_query(query, document):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Enter a jq query.")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query must be {MAX_QUERY_LENGTH} characters or fewer.")
    if not isinstance(document, str):
        raise ValueError("JSON input must be text.")

    try:
        result = subprocess.run(
            ["jq", "--", query],
            input=document,
            capture_output=True,
            text=True,
            timeout=JQ_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return {"ok": False, "output": "Query timed out after 5 seconds."}

    if result.returncode:
        return {"ok": False, "output": result.stderr.strip() or "jq could not run this query."}
    return {"ok": True, "output": result.stdout.rstrip("\n")}


class JqHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        if urlparse(self.path).path == "/":
            self.path = "/index.html"
        elif urlparse(self.path).path != self.path:
            self.send_error(404)
            return
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/run":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length."})
            return

        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request must be 1 MB or smaller."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise ValueError
            result = run_query(payload.get("query"), payload.get("input"))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            self._send_json(400, {"error": "Provide a JSON object with query and input fields."})
            return

        self._send_json(200, result)

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    if not shutil.which("jq"):
        raise SystemExit("jq was not found. Install jq and try again.")

    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), JqHandler)
    print(f"jq playground running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping jq playground.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
