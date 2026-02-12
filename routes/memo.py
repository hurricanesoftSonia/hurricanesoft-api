"""MemoTool REST API routes.

Endpoints:
    GET    /api/memo/list           — list memos (?tag=&pinned=&archived=&limit=)
    GET    /api/memo/<id>           — get memo
    POST   /api/memo/add            — add memo {title, body?, tags?}
    PUT    /api/memo/<id>           — update memo {title?, body?, tags?}
    DELETE /api/memo/<id>           — delete memo
    POST   /api/memo/<id>/pin      — pin
    POST   /api/memo/<id>/unpin    — unpin
    POST   /api/memo/<id>/archive  — archive
    POST   /api/memo/<id>/unarchive — unarchive
    GET    /api/memo/search         — search (?q=)
"""
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    from memotool import db as sqlite_db
    try:
        from memotool import db_pg
        pg_init = db_pg.get_conn
    except (ImportError, RuntimeError):
        pg_init = None
    conn, _ = get_connection('memotool', sqlite_init_fn=sqlite_db.get_conn, pg_init_fn=pg_init)
    return conn


def _row(r):
    if r is None:
        return None
    return dict(r) if hasattr(r, 'keys') else r


def handle(method, path, body, user):
    from memotool import db
    conn = _get_conn()
    username = user.get('username', '')
    parts = path.strip('/').split('/')
    sub = parts[2] if len(parts) > 2 else 'list'

    if method == 'GET' and sub == 'list':
        p = body or {}
        rows = db.list_memos(conn,
                             tag=p.get('tag'),
                             pinned_only=p.get('pinned') == '1',
                             archived=p.get('archived') == '1',
                             limit=int(p.get('limit', 50)))
        return 200, [_row(r) for r in rows]

    if method == 'GET' and sub == 'search':
        p = body or {}
        q = p.get('q', '')
        if not q:
            return 400, {'error': 'q is required'}
        rows = db.search_memos(conn, q, limit=int(p.get('limit', 20)))
        return 200, [_row(r) for r in rows]

    if method == 'POST' and sub == 'add':
        if not body or 'title' not in body:
            return 400, {'error': 'title is required'}
        memo_id = db.add_memo(conn, body['title'],
                              body=body.get('body', ''),
                              tags=body.get('tags', ''),
                              created_by=username)
        return 201, {'id': memo_id, 'message': 'created'}

    try:
        item_id = int(sub)
    except (ValueError, TypeError):
        return 404, {'error': 'not found'}

    action = parts[3] if len(parts) > 3 else None

    if method == 'GET' and action is None:
        row = db.get_memo(conn, item_id)
        if not row:
            return 404, {'error': 'not found'}
        return 200, _row(row)

    if method == 'PUT' and action is None:
        kwargs = {}
        for k in ('title', 'body', 'tags'):
            if body and k in body:
                kwargs[k] = body[k]
        db.update_memo(conn, item_id, **kwargs)
        return 200, {'message': 'updated'}

    if method == 'DELETE' and action is None:
        db.delete_memo(conn, item_id)
        return 200, {'message': 'deleted'}

    if method == 'POST' and action == 'pin':
        db.pin_memo(conn, item_id)
        return 200, {'message': 'pinned'}

    if method == 'POST' and action == 'unpin':
        db.unpin_memo(conn, item_id)
        return 200, {'message': 'unpinned'}

    if method == 'POST' and action == 'archive':
        db.archive_memo(conn, item_id)
        return 200, {'message': 'archived'}

    if method == 'POST' and action == 'unarchive':
        db.unarchive_memo(conn, item_id)
        return 200, {'message': 'unarchived'}

    return 404, {'error': 'not found'}
