#!/usr/bin/env python3
"""HurricaneSoft Unified API Server.

A lightweight HTTP server using Python stdlib http.server.
No Flask/FastAPI dependency.

Usage:
    python -m hurricanesoft_api.server [--port 8080] [--host 0.0.0.0] [--static ./static]
"""
import http.server
import json
import os
import sys
import datetime
from urllib.parse import urlparse, parse_qs

from hurricanesoft_api import __version__
from hurricanesoft_api.middleware import authenticate, cors_headers, handle_cors_preflight

# Route registry: prefix → module
ROUTE_MAP = {
    '/api/todo':     'hurricanesoft_api.routes.todo',
    '/api/memo':     'hurricanesoft_api.routes.memo',
    '/api/account':  'hurricanesoft_api.routes.account',
    '/api/announce': 'hurricanesoft_api.routes.announce',
    '/api/msg':      'hurricanesoft_api.routes.msg',
    '/api/health':   'hurricanesoft_api.routes.health',
    '/api/mail':     'hurricanesoft_api.routes.mail',
}

# Cached route modules
_route_modules = {}

STATIC_DIR = None


def _get_route_module(prefix):
    """Lazily import and cache route module."""
    if prefix not in _route_modules:
        mod_name = ROUTE_MAP[prefix]
        _route_modules[prefix] = __import__(mod_name, fromlist=['handle'])
    return _route_modules[prefix]


def _json_serial(obj):
    """JSON serializer for non-standard types."""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f"Type {type(obj)} not serializable")


class APIHandler(http.server.BaseHTTPRequestHandler):
    """Request handler for the unified API."""

    def log_message(self, format, *args):
        sys.stderr.write("[%s] %s\n" % (
            self.log_date_time_string(), format % args))

    def _send_json(self, status, data, extra_headers=None):
        body = json.dumps(data, default=_json_serial, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        # CORS
        for k, v in cors_headers().items():
            self.send_header(k, v)
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return None
        raw = self.rfile.read(length)
        content_type = self.headers.get('Content-Type', '')
        if 'json' in content_type:
            return json.loads(raw)
        return raw.decode('utf-8', errors='replace')

    def _get_query_params(self):
        parsed = urlparse(self.path)
        params = {}
        for k, v in parse_qs(parsed.query).items():
            params[k] = v[0] if len(v) == 1 else v
        return params

    def _route(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        # CORS preflight
        if method == 'OPTIONS':
            status, headers, body = handle_cors_preflight()
            self.send_response(status)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            if body:
                self.wfile.write(body)
            return

        # API version / health
        if path == '/api' or path == '/api/version':
            self._send_json(200, {
                'name': 'hurricanesoft-api',
                'version': __version__,
                'endpoints': list(ROUTE_MAP.keys()),
            })
            return

        # Find matching route
        matched_prefix = None
        for prefix in ROUTE_MAP:
            if path == prefix or path.startswith(prefix + '/'):
                matched_prefix = prefix
                break

        if matched_prefix:
            # Authenticate
            user, err = authenticate(self.headers)
            if err:
                self._send_json(401, {'error': err})
                return

            # Parse body/params
            if method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                body = self._read_body()
                if body is None:
                    body = {}
            else:
                body = self._get_query_params()

            # Dispatch to route handler
            try:
                mod = _get_route_module(matched_prefix)
                status, data = mod.handle(method, path, body, user)
                self._send_json(status, data)
            except Exception as e:
                sys.stderr.write(f"Error in {matched_prefix}: {e}\n")
                import traceback
                traceback.print_exc()
                self._send_json(500, {'error': str(e)})
            return

        # Static file serving for web dashboard
        if STATIC_DIR:
            self._serve_static(path)
            return

        self._send_json(404, {'error': 'not found'})

    def _serve_static(self, path):
        """Serve static files from STATIC_DIR."""
        if path == '' or path == '/':
            path = '/index.html'
        file_path = os.path.join(STATIC_DIR, path.lstrip('/'))
        file_path = os.path.realpath(file_path)

        # Security: prevent directory traversal
        if not file_path.startswith(os.path.realpath(STATIC_DIR)):
            self._send_json(403, {'error': 'forbidden'})
            return

        if not os.path.isfile(file_path):
            # SPA fallback: serve index.html for non-file paths
            index = os.path.join(STATIC_DIR, 'index.html')
            if os.path.isfile(index):
                file_path = index
            else:
                self._send_json(404, {'error': 'not found'})
                return

        # Guess content type
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
            '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
            '.gif': 'image/gif', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
            '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf',
        }
        ct = content_types.get(ext, 'application/octet-stream')

        with open(file_path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', str(len(data)))
        for k, v in cors_headers().items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._route('GET')

    def do_POST(self):
        self._route('POST')

    def do_PUT(self):
        self._route('PUT')

    def do_DELETE(self):
        self._route('DELETE')

    def do_PATCH(self):
        self._route('PATCH')

    def do_OPTIONS(self):
        self._route('OPTIONS')


def run(host='0.0.0.0', port=8080, static_dir=None):
    """Start the API server."""
    global STATIC_DIR
    if static_dir and os.path.isdir(static_dir):
        STATIC_DIR = os.path.realpath(static_dir)
        print(f"📁 Static files: {STATIC_DIR}")

    server = http.server.HTTPServer((host, port), APIHandler)
    print(f"🌀 HurricaneSoft API Server v{__version__}")
    print(f"🚀 Listening on {host}:{port}")
    print(f"📡 Endpoints: {', '.join(ROUTE_MAP.keys())}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        server.server_close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='HurricaneSoft Unified API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Bind host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Bind port (default: 8080)')
    parser.add_argument('--static', default=None, help='Static files directory for web dashboard')
    args = parser.parse_args()
    run(host=args.host, port=args.port, static_dir=args.static)


if __name__ == '__main__':
    main()
