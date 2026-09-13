"""Static file server for local preview that disables all caching.

Plain `python -m http.server` lets browsers cache JS/CSS aggressively
(no Cache-Control header at all triggers heuristic freshness), which made
edits invisible in the preview browser without a manual hard-reload. This
adds `Cache-Control: no-store` to every response so each preview always
reflects the files on disk.
"""

import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    HTTPServer(("", port), NoCacheHandler).serve_forever()
