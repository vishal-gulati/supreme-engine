"""Main Application Server for The Daily Broadsheet.
Combines high-performance static asset delivery with RESTful API endpoints.
Zero external framework dependencies - runs on standard Python 3.
"""

import http.server
import json
import mimetypes
import os
import re
import sys
import traceback
import urllib.parse
from http import HTTPStatus

from storage import (
    init_db,
    get_config,
    update_config,
    get_sources,
    add_source,
    update_source,
    delete_source,
    get_editions,
    get_edition_by_id,
    get_latest_edition,
    delete_edition,
    save_edition,
)
from fetcher import fetch_all_feeds, fetch_single_feed, PRESET_SOURCES
from curator import format_newspaper_edition, get_market_ticker
from seed_data import seed_database

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class NewspaperRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler supporting REST API and static files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _send_json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message, status=HTTPStatus.BAD_REQUEST):
        self._send_json({"error": message, "success": False}, status=status)

    def _read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                return {}
            raw_body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_body)
        except Exception as e:
            print(f"Error reading JSON body: {e}")
            return {}

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            raw_path = parsed.path
            path = raw_path.rstrip("/")
            if not path:
                path = "/"

            # API Routes
            if path == "/api/config":
                self._send_json({"success": True, "config": get_config()})
                return

            if path == "/api/sources":
                self._send_json({"success": True, "sources": get_sources()})
                return

            if path == "/api/sources/presets":
                self._send_json({"success": True, "presets": PRESET_SOURCES})
                return

            if path == "/api/markets":
                self._send_json({"success": True, "markets": get_market_ticker()})
                return

            if path == "/api/weather":
                query = urllib.parse.parse_qs(parsed.query)
                city = query.get("city", ["Bengaluru"])[0]
                from weather import get_live_weather
                weather_data = get_live_weather(city)
                self._send_json({"success": True, "weather": weather_data})
                return

            if path == "/api/editions":
                editions = get_editions()
                self._send_json({"success": True, "editions": editions})
                return

            if path == "/api/editions/latest":
                latest = get_latest_edition()
                if latest:
                    self._send_json({"success": True, "edition": latest})
                else:
                    self._send_error("No editions found", HTTPStatus.NOT_FOUND)
                return

            edition_match = re.match(r"^/api/editions/(\d+)$", path)
            if edition_match:
                ed_id = int(edition_match.group(1))
                edition = get_edition_by_id(ed_id)
                if edition:
                    self._send_json({"success": True, "edition": edition})
                else:
                    self._send_error("Edition not found", HTTPStatus.NOT_FOUND)
                return

            # Serve SPA index for root
            if path == "/":
                self.path = "/index.html"
                return super().do_GET()

            # Serve static file
            self.path = raw_path
            return super().do_GET()
        except Exception as e:
            traceback.print_exc()
            self._send_error(f"Internal error: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")
            body = self._read_json_body()

            if path == "/api/config":
                update_config(body)
                self._send_json({"success": True, "config": get_config()})
                return

            if path == "/api/sources":
                name = body.get("name", "").strip()
                url = body.get("url", "").strip()
                section = body.get("section", "Front Page").strip()
                enabled = 1 if body.get("enabled", True) else 0
                max_items = int(body.get("max_items", 5))

                if not name or not url:
                    self._send_error("Source name and URL are required.")
                    return

                source_id = add_source(name, url, section, enabled, max_items)
                self._send_json({"success": True, "source_id": source_id, "sources": get_sources()})
                return

            if path == "/api/sources/test":
                url = body.get("url", "").strip()
                if not url:
                    self._send_error("URL is required.")
                    return
                test_source = {"name": "Test Source", "url": url, "section": "Preview", "max_items": 3}
                articles = fetch_single_feed(test_source, timeout=6)
                if articles:
                    self._send_json({"success": True, "count": len(articles), "sample": articles})
                else:
                    self._send_error("Could not fetch or parse articles from this feed URL.")
                return

            if path == "/api/generate":
                # 1. Fetch enabled sources
                sources = get_sources()
                enabled_sources = [s for s in sources if s.get("enabled", 1)]
                config = get_config()

                # Merge overrides from body if sent
                if body.get("paper_name"):
                    config["paper_name"] = body["paper_name"]
                if body.get("motto"):
                    config["motto"] = body["motto"]
                if body.get("city"):
                    config["city"] = body["city"]

                print(f"Fetching from {len(enabled_sources)} enabled sources...")
                raw_articles = []
                try:
                    raw_articles = fetch_all_feeds(enabled_sources)
                except Exception as ex:
                    print(f"Error during fetch_all_feeds: {ex}")

                if not raw_articles:
                    # If network was unavailable or feeds returned empty, fallback to rich sample articles
                    from seed_data import SAMPLE_ARTICLES
                    raw_articles = SAMPLE_ARTICLES

                edition_data = format_newspaper_edition(raw_articles, config)
                edition_id = save_edition(edition_data)

                self._send_json({
                    "success": True,
                    "edition_id": edition_id,
                    "edition": get_edition_by_id(edition_id),
                })
                return

            self._send_error("Route not found", HTTPStatus.NOT_FOUND)
        except Exception as e:
            traceback.print_exc()
            self._send_error(f"Server error: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        source_match = re.match(r"^/api/sources/(\d+)$", path)
        if source_match:
            source_id = int(source_match.group(1))
            success = update_source(source_id, **body)
            self._send_json({"success": success, "sources": get_sources()})
            return

        self._send_error("Route not found", HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        source_match = re.match(r"^/api/sources/(\d+)$", path)
        if source_match:
            source_id = int(source_match.group(1))
            success = delete_source(source_id)
            self._send_json({"success": success, "sources": get_sources()})
            return

        edition_match = re.match(r"^/api/editions/(\d+)$", path)
        if edition_match:
            ed_id = int(edition_match.group(1))
            success = delete_edition(ed_id)
            self._send_json({"success": success, "editions": get_editions()})
            return

        self._send_error("Route not found", HTTPStatus.NOT_FOUND)


def run_server(port=8080):
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

    seed_database()

    server_address = ("0.0.0.0", port)

    class ReusableServer(http.server.ThreadingHTTPServer):
        allow_reuse_address = True
        allow_reuse_port = True

    httpd = ReusableServer(server_address, NewspaperRequestHandler)
    print(f"\n=======================================================")
    print(f"  THE DAILY BROADSHEET - NEWSPAPER GENERATOR")
    print(f"  Live Server listening at: http://localhost:{port}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
