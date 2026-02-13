"""MailTool REST API routes.

Endpoints:
    GET    /api/mail/list          — list messages (?folder=&page=&per_page=&unread=&read=)
    GET    /api/mail/<id>          — read message
    POST   /api/mail/<id>/read     — mark as read
    POST   /api/mail/send          — send email {to, subject, body, cc?, bcc?}
    GET    /api/mail/search        — search (?q=&limit=)
    POST   /api/mail/fetch         — fetch new mail from server
    GET    /api/mail/<id>/attachments — list attachments
    POST   /api/mail/<id>/label    — add label {label}
    DELETE /api/mail/<id>/label    — remove label {label}
"""
import math
import traceback
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    try:
        from mailtool import db as sqlite_db
        conn, _ = get_connection('mailtool', sqlite_init_fn=sqlite_db.get_conn)
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
    try:
        from mailtool import db
        conn = _get_conn()
        parts = path.strip('/').split('/')
        sub = parts[2] if len(parts) > 2 else 'list'

        if method == 'GET' and sub == 'list':
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
            
            is_read = None
            if p.get('unread') == '1':
                is_read = 0
            elif p.get('read') == '1':
                is_read = 1
            
            rows = db.list_messages(conn,
                                    folder=p.get('folder', 'inbox'),
                                    limit=None,
                                    is_read=is_read)
            items = [_row(r) for r in rows]
            return 200, _paginate(items, page, per_page)

        if method == 'GET' and sub == 'search':
            p = body or {}
            q = p.get('q', '')
            if not q:
                return 400, {'error': 'q is required'}
            
            try:
                limit = int(p.get('limit', 20))
            except (ValueError, TypeError):
                return 400, {'error': 'Invalid limit parameter'}
            
            rows = db.search(conn, q, limit=limit)
            return 200, [_row(r) for r in rows]

        if method == 'POST' and sub == 'send':
            # Input validation
            if not body:
                return 400, {'error': 'Request body is required'}
            
            missing = []
            for k in ('to', 'subject'):
                if k not in body or not body[k]:
                    missing.append(k)
            if missing:
                return 400, {'error': f'Missing required fields: {", ".join(missing)}'}
            
            try:
                from mailtool import sender
                config = _get_mail_config()
                sender.send_mail(config, body['to'], body['subject'], body.get('body', ''),
                                 cc=body.get('cc'), bcc=body.get('bcc'))
                return 200, {'message': 'sent'}
            except Exception as e:
                tb = traceback.format_exc()
                print(f"Error sending email: {e}\n{tb}")
                return 500, {'error': f'Failed to send email: {str(e)}'}

        if method == 'POST' and sub == 'fetch':
            try:
                from mailtool import receiver
                config = _get_mail_config()
                msgs = receiver.fetch_mail(config, keep=True)
                return 200, {'fetched': len(msgs) if msgs else 0}
            except Exception as e:
                tb = traceback.format_exc()
                print(f"Error fetching mail: {e}\n{tb}")
                return 500, {'error': f'Failed to fetch mail: {str(e)}'}

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

        if method == 'GET' and action == 'attachments':
            rows = db.get_attachments(conn, item_id)
            return 200, [_row(r) for r in rows]

        if method == 'POST' and action == 'label':
            if not body:
                return 400, {'error': 'Request body is required'}
            if 'label' not in body or not body['label']:
                return 400, {'error': 'label is required'}
            
            db.add_label(conn, item_id, body['label'])
            return 200, {'message': 'label added'}

        if method == 'DELETE' and action == 'label':
            if not body:
                return 400, {'error': 'Request body is required'}
            if 'label' not in body or not body['label']:
                return 400, {'error': 'label is required'}
            
            db.remove_label(conn, item_id, body['label'])
            return 200, {'message': 'label removed'}

        return 404, {'error': 'not found'}
    
    except ConnectionError as e:
        return 503, {'error': str(e)}
    except ValueError as e:
        return 400, {'error': f'Invalid input: {str(e)}'}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in mail route: {e}\n{tb}")
        return 500, {'error': f'Internal server error: {str(e)}'}
