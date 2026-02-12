"""MsgTool REST API routes.

Endpoints:
    GET    /api/msg/inbox          — inbox (?unread=1&limit=)
    GET    /api/msg/sent           — sent messages (?limit=)
    GET    /api/msg/<id>           — get message
    POST   /api/msg/send           — send {to, body, reply_to?}
    POST   /api/msg/broadcast      — broadcast {body}
    POST   /api/msg/<id>/read      — mark read
    GET    /api/msg/<id>/thread    — get thread
    GET    /api/msg/mentions       — mentions (?limit=)
    GET    /api/msg/unread         — unread count
    GET    /api/msg/users          — list users
"""
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    from msgtool import db as sqlite_db
    try:
        from msgtool import db_pg
        pg_init = db_pg.get_conn
    except (ImportError, RuntimeError):
        pg_init = None
    conn, _ = get_connection('msgtool', sqlite_init_fn=sqlite_db.get_conn, pg_init_fn=pg_init)
    return conn


def _row(r):
    if r is None:
        return None
    return dict(r) if hasattr(r, 'keys') else r


def handle(method, path, body, user):
    from msgtool import db
    conn = _get_conn()
    username = user.get('username', '')
    parts = path.strip('/').split('/')
    sub = parts[2] if len(parts) > 2 else 'inbox'

    if method == 'GET' and sub == 'inbox':
        p = body or {}
        rows = db.get_inbox(conn, username,
                            unread_only=p.get('unread') == '1',
                            limit=int(p.get('limit', 50)))
        return 200, [_row(r) for r in rows]

    if method == 'GET' and sub == 'sent':
        p = body or {}
        rows = db.get_sent(conn, username, limit=int(p.get('limit', 50)))
        return 200, [_row(r) for r in rows]

    if method == 'GET' and sub == 'users':
        rows = db.list_users(conn)
        return 200, [_row(r) for r in rows]

    if method == 'GET' and sub == 'unread':
        count = db.count_unread(conn, username)
        return 200, {'count': count}

    if method == 'GET' and sub == 'mentions':
        p = body or {}
        rows = db.get_mentions(conn, username, limit=int(p.get('limit', 20)))
        return 200, [_row(r) for r in rows]

    if method == 'POST' and sub == 'send':
        if not body or 'to' not in body or 'body' not in body:
            return 400, {'error': 'to and body required'}
        msg_id = db.send_message(conn, username, body['to'], body['body'],
                                 reply_to=body.get('reply_to'))
        return 201, {'id': msg_id, 'message': 'sent'}

    if method == 'POST' and sub == 'broadcast':
        if not body or 'body' not in body:
            return 400, {'error': 'body required'}
        count = db.broadcast(conn, username, body['body'])
        return 200, {'count': count, 'message': 'broadcast sent'}

    # Numeric ID routes
    try:
        item_id = int(sub)
    except (ValueError, TypeError):
        return 404, {'error': 'not found'}

    action = parts[3] if len(parts) > 3 else None

    if method == 'GET' and action is None:
        row = db.get_message(conn, item_id)
        if not row:
            return 404, {'error': 'not found'}
        return 200, _row(row)

    if method == 'POST' and action == 'read':
        db.mark_read(conn, item_id)
        return 200, {'message': 'marked read'}

    if method == 'GET' and action == 'thread':
        rows = db.get_thread(conn, item_id)
        return 200, [_row(r) for r in rows]

    return 404, {'error': 'not found'}
