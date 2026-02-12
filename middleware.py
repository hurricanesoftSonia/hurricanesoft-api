"""LIDS OAuth2 authentication middleware and CORS support."""
import json
import urllib.request
import urllib.error

from hurricanesoft_cli.config import load_config


def get_lids_config():
    """Get LIDS config from unified config."""
    config = load_config()
    return config.get('lids', {})


def validate_token(token):
    """Validate a Bearer token against LIDS userinfo endpoint.

    Returns user dict {'username': ..., 'email': ..., ...} or None.
    """
    lids = get_lids_config()
    if not lids.get('use_lids'):
        return None
    server = lids.get('server', '').rstrip('/')
    if not server:
        return None
    url = f"{server}/connect/userinfo"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        return None


def authenticate(headers):
    """Extract and validate auth from request headers.

    Returns (user_dict, error_message).
    If LIDS is disabled, returns a default user.
    """
    lids = get_lids_config()
    if not lids.get('use_lids'):
        # No auth required — return default user from config
        config = load_config()
        username = config.get('user', {}).get('username', 'default')
        return {'username': username, 'sub': username}, None

    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, 'Missing or invalid Authorization header'

    token = auth_header[7:]
    user = validate_token(token)
    if not user:
        return None, 'Invalid or expired token'

    # Normalize: ensure 'username' key exists
    if 'username' not in user:
        user['username'] = user.get('preferred_username', user.get('sub', 'unknown'))
    return user, None


def cors_headers(origin=None):
    """Return CORS headers dict."""
    return {
        'Access-Control-Allow-Origin': origin or '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400',
    }


def handle_cors_preflight(origin=None):
    """Return (status, headers, body) for CORS preflight."""
    return 204, cors_headers(origin), b''
