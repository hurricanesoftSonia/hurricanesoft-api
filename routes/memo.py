"""MemoTool REST API routes.

Endpoints:
    GET    /api/memo/list           — list memos (?tag=&pinned=&archived=&page=&per_page=)
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
import math
import traceback
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    try:
        from memotool import db as sqlite_db
        try:
            from memotool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        # Use init_db to ensure tables exist
        conn, _ = get_connection('memotool', sqlite_init_fn=sqlite_db.init_db, pg_init_fn=pg_init)
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
        from memotool import db
        conn = _get_conn()
        username = user.get('username', '')
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
            
            rows = db.list_memos(conn,
                                 tag=p.get('tag'),
                                 pinned_only=p.get('pinned') == '1',
                                 archived=p.get('archived') == '1',
                                 limit=None)
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
            
            rows = db.search_memos(conn, q, limit=limit)
            return 200, [_row(r) for r in rows]

        if method == 'POST' and sub == 'add':
            # Input validation
            if not body:
                return 400, {'error': 'Request body is required'}
            if 'title' not in body or not body['title']:
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
                return 404, {'error': 'Memo not found'}
            return 200, _row(row)

        if method == 'PUT' and action is None:
            if not body:
                return 400, {'error': 'Request body is required'}
            
            kwargs = {}
            for k in ('title', 'body', 'tags'):
                if k in body:
                    kwargs[k] = body[k]
            
            if not kwargs:
                return 400, {'error': 'At least one field must be provided'}
            
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
    
    except ConnectionError as e:
        return 503, {'error': str(e)}
    except ValueError as e:
        return 400, {'error': f'Invalid input: {str(e)}'}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in memo route: {e}\n{tb}")
        return 500, {'error': f'Internal server error: {str(e)}'}
