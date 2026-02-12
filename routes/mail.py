"""MailTool REST API routes.

Endpoints:
    GET    /api/mail/list          — list messages (?folder=&limit=&unread=&read=)
    GET    /api/mail/<id>          — read message
    POST   /api/mail/<id>/read     — mark as read
    POST   /api/mail/send          — send email {to, subject, body, cc?, bcc?}
    GET    /api/mail/search        — search (?q=&limit=)
    POST   /api/mail/fetch         — fetch new mail from server
    GET    /api/mail/<id>/attachments — list attachments
    POST   /api/mail/<id>/label    — add label {label}
    DELETE /api/mail/<id>/label    — remove label {label}
"""
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    from mailtool import db as sqlite_db
    conn, _ = get_connection('mailtool', sqlite_init_fn=sqlite_db.get_conn)
    return conn


def _row(r):
    if r is None:
        return None
    return dict(r) if hasattr(r, 'keys') else r


def _get_mail_config():
    """Load mail config from unified config."""
    from hurricanesoft_cli.config import load_config
    config = load_config()
    mail = config.get('mail', {})
    return {
        'email': mail.get('email', ''),
        'password': mail.get('password', ''),
        'pop3': {'host': mail.get('pop3_host', ''), 'port': mail.get('pop3_port', 995)},
        'smtp': {'host': mail.get('smtp_host', ''), 'port': mail.get('smtp_port', 465)},
        'signature': mail.get('signature', ''),
    }


def handle(method, path, body, user):
    from mailtool import db
    conn = _get_conn()
    parts = path.strip('/').split('/')
    sub = parts[2] if len(parts) > 2 else 'list'

    if method == 'GET' and sub == 'list':
        p = body or {}
        is_read = None
        if p.get('unread') == '1':
            is_read = 0
        elif p.get('read') == '1':
            is_read = 1
        rows = db.list_messages(conn,
                                folder=p.get('folder', 'inbox'),
                                limit=int(p.get('limit', 20)),
                                is_read=is_read)
        return 200, [_row(r) for r in rows]

    if method == 'GET' and sub == 'search':
        p = body or {}
        q = p.get('q', '')
        if not q:
            return 400, {'error': 'q is required'}
        rows = db.search(conn, q, limit=int(p.get('limit', 20)))
        return 200, [_row(r) for r in rows]

    if method == 'POST' and sub == 'send':
        if not body or 'to' not in body or 'subject' not in body or 'body' not in body:
            return 400, {'error': 'to, subject, and body required'}
        try:
            from mailtool import sender
            config = _get_mail_config()
            sender.send_mail(config, body['to'], body['subject'], body['body'],
                             cc=body.get('cc'), bcc=body.get('bcc'))
            return 200, {'message': 'sent'}
        except Exception as e:
            return 500, {'error': str(e)}

    if method == 'POST' and sub == 'fetch':
        try:
            from mailtool import receiver
            config = _get_mail_config()
            msgs = receiver.fetch_mail(config, keep=True)
            return 200, {'fetched': len(msgs) if msgs else 0}
        except Exception as e:
            return 500, {'error': str(e)}

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

    if method == 'GET' and action == 'attachments':
        rows = db.get_attachments(conn, item_id)
        return 200, [_row(r) for r in rows]

    if method == 'POST' and action == 'label':
        if not body or 'label' not in body:
            return 400, {'error': 'label required'}
        db.add_label(conn, item_id, body['label'])
        return 200, {'message': 'label added'}

    if method == 'DELETE' and action == 'label':
        if not body or 'label' not in body:
            return 400, {'error': 'label required'}
        db.remove_label(conn, item_id, body['label'])
        return 200, {'message': 'label removed'}

    return 404, {'error': 'not found'}
