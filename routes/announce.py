"""AnnounceTool REST API routes.

Endpoints:
    GET    /api/announce/list             — list announcements (?priority=&archived=&limit=)
    GET    /api/announce/<id>             — get announcement
    POST   /api/announce/add              — post announcement {title, body?, priority?}
    POST   /api/announce/<id>/archive     — archive
    POST   /api/announce/<id>/unarchive   — unarchive
    POST   /api/announce/<id>/recipients  — add recipients {contacts: [...]}
    GET    /api/announce/<id>/recipients  — get recipients
    POST   /api/announce/<id>/ack         — acknowledge {email}
    POST   /api/announce/<id>/remind      — increment remind {email}
    GET    /api/announce/contacts         — list contacts
    POST   /api/announce/contacts         — add contact {name, email}
    DELETE /api/announce/contacts/<name>  — remove contact
"""
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    from announcetool import db as sqlite_db
    try:
        from announcetool import db_pg
        pg_init = db_pg.get_conn
    except (ImportError, RuntimeError):
        pg_init = None
    conn, _ = get_connection('announcetool', sqlite_init_fn=sqlite_db.get_conn, pg_init_fn=pg_init)
    return conn


def _row(r):
    if r is None:
        return None
    return dict(r) if hasattr(r, 'keys') else r


def handle(method, path, body, user):
    from announcetool import db
    conn = _get_conn()
    username = user.get('username', '')
    parts = path.strip('/').split('/')
    sub = parts[2] if len(parts) > 2 else 'list'

    if method == 'GET' and sub == 'list':
        p = body or {}
        rows = db.list_announcements(conn,
                                     priority=p.get('priority'),
                                     archived=p.get('archived') == '1',
                                     limit=int(p.get('limit', 50)))
        return 200, [_row(r) for r in rows]

    if method == 'POST' and sub == 'add':
        if not body or 'title' not in body:
            return 400, {'error': 'title is required'}
        ann_id = db.post_announcement(conn, body['title'],
                                      body=body.get('body', ''),
                                      priority=body.get('priority', 'normal'),
                                      posted_by=username)
        return 201, {'id': ann_id, 'message': 'created'}

    if method == 'GET' and sub == 'contacts':
        rows = db.list_contacts(conn)
        return 200, [_row(r) for r in rows]

    if method == 'POST' and sub == 'contacts':
        if not body or 'name' not in body or 'email' not in body:
            return 400, {'error': 'name and email required'}
        result = db.add_contact(conn, body['name'], body['email'])
        return 201, {'success': bool(result), 'message': 'created'}

    # DELETE /api/announce/contacts/<name>
    if method == 'DELETE' and sub == 'contacts' and len(parts) > 3:
        name = parts[3]
        db.remove_contact(conn, name)
        return 200, {'message': 'deleted'}

    # Numeric ID routes
    try:
        item_id = int(sub)
    except (ValueError, TypeError):
        return 404, {'error': 'not found'}

    action = parts[3] if len(parts) > 3 else None

    if method == 'GET' and action is None:
        row = db.get_announcement(conn, item_id)
        if not row:
            return 404, {'error': 'not found'}
        return 200, _row(row)

    if method == 'POST' and action == 'archive':
        db.archive_announcement(conn, item_id)
        return 200, {'message': 'archived'}

    if method == 'POST' and action == 'unarchive':
        db.unarchive_announcement(conn, item_id)
        return 200, {'message': 'unarchived'}

    if method == 'GET' and action == 'recipients':
        rows = db.get_recipients(conn, item_id)
        return 200, [_row(r) for r in rows]

    if method == 'POST' and action == 'recipients':
        if not body or 'contacts' not in body:
            return 400, {'error': 'contacts list required'}
        db.add_recipients(conn, item_id, body['contacts'])
        return 200, {'message': 'recipients added'}

    if method == 'POST' and action == 'ack':
        if not body or 'email' not in body:
            return 400, {'error': 'email required'}
        db.mark_read(conn, item_id, body['email'])
        return 200, {'message': 'acknowledged'}

    if method == 'POST' and action == 'remind':
        if not body or 'email' not in body:
            return 400, {'error': 'email required'}
        db.increment_remind(conn, item_id, body['email'])
        return 200, {'message': 'reminded'}

    return 404, {'error': 'not found'}
