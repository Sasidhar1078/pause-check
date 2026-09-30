import argparse
import ipaddress
import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
MAX_BODY_SIZE = 4096
MAX_URL_LENGTH = 2048
SHORTENER_DOMAINS = {
    "bit.ly",
    "goo.gl",
    "is.gd",
    "ow.ly",
    "t.co",
    "tinyurl.com",
}
STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/manifest.webmanifest": "manifest.webmanifest",
    "/service-worker.js": "service-worker.js",
    "/icon.svg": "icon.svg",
    "/icon-192.png": "icon-192.png",
    "/icon-512.png": "icon-512.png",
    "/apple-touch-icon.png": "apple-touch-icon.png",
}


def inspect_url(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Enter a web address.")
    if len(value) > MAX_URL_LENGTH:
        raise ValueError("The web address is too long.")
    if any(character.isspace() for character in value):
        raise ValueError("The web address cannot contain spaces.")

    candidate = value if re.match(r"^[a-zA-Z][a-zA-Z\d+.-]*:", value) else f"https://{value}"
    try:
        address = urlsplit(candidate)
        hostname = address.hostname
        address.port
    except ValueError as error:
        raise ValueError("This does not look like a valid web address.") from error

    if address.scheme.lower() not in {"http", "https"} or not hostname:
        raise ValueError("Enter a valid website address beginning with http:// or https://.")

    try:
        host = hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise ValueError("This does not look like a valid web address.") from error
    reasons = []
    if address.scheme.lower() == "http":
        reasons.append("It does not use HTTPS, so the connection is not encrypted.")
    if address.username or address.password:
        reasons.append(
            "It contains sign-in details before the website name, which can be used to disguise where a link goes."
        )
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        reasons.append("It uses a numeric address instead of a recognisable website name.")
    if any(label.startswith("xn--") for label in host.split(".")):
        reasons.append(
            "The website name uses encoded characters that can make look-alike names harder to spot."
        )
    if len(host) > 50:
        reasons.append("The website name is unusually long.")
    if any(host == domain or host.endswith(f".{domain}") for domain in SHORTENER_DOMAINS):
        reasons.append("It uses a shortened-link service, so the destination is hidden.")
    if len(address.path) > 70 and re.search(r"%[0-9a-f]{2}", address.path, re.IGNORECASE):
        reasons.append("The link contains a long, encoded path that is difficult to inspect.")

    return {"warning_signs": reasons}


class AppHandler(BaseHTTPRequestHandler):
    server_version = "PauseCheck"
    sys_version = ""

    def log_message(self, _format, *_args):
        return

    def send_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'",
        )

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            self.send_json(200, {"status": "ok"})
            return

        filename = STATIC_FILES.get(path)
        if filename is None:
            self.send_json(404, {"error": "Page not found."})
            return

        content = (ROOT / filename).read_bytes()
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        if filename.endswith(".webmanifest"):
            content_type = "application/manifest+json"
        if filename.endswith((".html", ".js", ".webmanifest")):
            content_type += "; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.send_security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/link-check":
            self.send_json(404, {"error": "Endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid request size."})
            return
        if content_length < 1 or content_length > MAX_BODY_SIZE:
            self.send_json(413 if content_length > MAX_BODY_SIZE else 400, {"error": "Invalid request size."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {"error": "Send a valid JSON request."})
            return

        if not isinstance(payload, dict) or "url" not in payload:
            self.send_json(400, {"error": "Include a web address to check."})
            return

        try:
            assessment = inspect_url(payload["url"])
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
            return

        self.send_json(200, assessment)


def main():
    parser = argparse.ArgumentParser(description="Run the Pause & Check website and private link-check service.")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind to (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000).")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print(f"Pause & Check is available at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Pause & Check.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
