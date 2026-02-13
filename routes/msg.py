"""MsgTool REST API routes.

Endpoints:
    GET    /api/msg/inbox          — inbox (?unread=1&page=&per_page=)
    GET    /api/msg/sent           — sent messages (?page=&per_page=)
    GET    /api/msg/<id>           — get message
    POST   /api/msg/send           — send {to, msg, reply_to?}
    POST   /api/msg/broadcast      — broadcast {msg}
    POST   /api/msg/<id>/read      — mark read
    GET    /api/msg/<id>/thread    — get thread
    GET    /api/msg/mentions       — mentions (?limit=)
    GET    /api/msg/unread         — unread count
    GET    /api/msg/users          — list users
"""
import math
import traceback
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    try:
        from msgtool import db as sqlite_db
        try:
            from msgtool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        # Use init_db to ensure tables exist
        conn, _ = get_connection('msgtool', sqlite_init_fn=sqlite_db.init_db, pg_init_fn=pg_init)
        return conn
    except Exception as e:
        raise ConnectionError(f"Database connection failed: {e}")


def _row(r):
    if r is None:
        return None
    return dict(r) if hasattr(r, 'keys') else r


def _paginate(items, page=1, per_page=20):
    """Apply pagination to a list and return paginated response."""
    total = len(items)
    pages = math.ceil(total / per_page) if per_page > 0 else 1
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages
    }


def handle(method, path, body, user):
    try:
        from msgtool import db
        conn = _get_conn()
        username = user.get('username', '')
        parts = path.strip('/').split('/')
        sub = parts[2] if len(parts) > 2 else 'inbox'

        if method == 'GET' and sub == 'inbox':
            p = body or {}
            
            # Pagination
            try:
                page = int(p.get('page', 1))
                per_page = int(p.get('per_page', 20))
                if page < 1:
                    page = 1
                if per_page < 1 or per_page > 100:
                    per_page = 20
            except (ValueError, TypeError):
                return 400, {'error': 'Invalid pagination parameters'}
            
            rows = db.get_inbox(conn, username,
                                unread_only=p.get('unread') == '1',
                                limit=None)
            items = [_row(r) for r in rows]
            return 200, _paginate(items, page, per_page)

        if method == 'GET' and sub == 'sent':
            p = body or {}
            
            # Pagination
            try:
                page = int(p.get('page', 1))
                per_page = int(p.get('per_page', 20))
                if page < 1:
                    page = 1
                if per_page < 1 or per_page > 100:
                    per_page = 20
            except (ValueError, TypeError):
                return 400, {'error': 'Invalid pagination parameters'}
            
            rows = db.get_sent(conn, username, limit=None)
            items = [_row(r) for r in rows]
            return 200, _paginate(items, page, per_page)

        if method == 'GET' and sub == 'users':
            rows = db.list_users(conn)
            return 200, [_row(r) for r in rows]

        if method == 'GET' and sub == 'unread':
            count = db.count_unread(conn, username)
            return 200, {'count': count}

        if method == 'GET' and sub == 'mentions':
            p = body or {}
            try:
                limit = int(p.get('limit', 20))
            except (ValueError, TypeError):
                return 400, {'error': 'Invalid limit parameter'}
            
            rows = db.get_mentions(conn, username, limit=limit)
            return 200, [_row(r) for r in rows]

        if method == 'POST' and sub == 'send':
            # Input validation
            if not body:
                return 400, {'error': 'Request body is required'}
            if 'to' not in body or not body['to']:
                return 400, {'error': 'to is required'}
            if 'msg' not in body or not body['msg']:
                return 400, {'error': 'msg is required'}
            
            msg_id = db.send_message(conn, username, body['to'], body['msg'],
                                     reply_to=body.get('reply_to'))
            return 201, {'id': msg_id, 'message': 'sent'}

        if method == 'POST' and sub == 'broadcast':
            if not body:
                return 400, {'error': 'Request body is required'}
            if 'msg' not in body or not body['msg']:
                return 400, {'error': 'msg is required'}
            
            count = db.broadcast(conn, username, body['msg'])
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
                return 404, {'error': 'Message not found'}
            return 200, _row(row)

        if method == 'POST' and action == 'read':
            db.mark_read(conn, item_id)
            return 200, {'message': 'marked read'}

        if method == 'GET' and action == 'thread':
            rows = db.get_thread(conn, item_id)
            return 200, [_row(r) for r in rows]

        return 404, {'error': 'not found'}
    
    except ConnectionError as e:
        return 503, {'error': str(e)}
    except ValueError as e:
        return 400, {'error': f'Invalid input: {str(e)}'}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in msg route: {e}\n{tb}")
        return 500, {'error': f'Internal server error: {str(e)}'}
