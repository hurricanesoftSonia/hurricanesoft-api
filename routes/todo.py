"""TodoTool REST API routes.

Endpoints:
    GET    /api/todo/list          — list todos (?status=&tag=&priority=&limit=&page=&per_page=)
    GET    /api/todo/<id>          — get single todo
    POST   /api/todo/add           — add todo {title, priority?, due_date?, note?, tags?}
    PUT    /api/todo/<id>          — edit todo {title?, priority?, due_date?, note?, tags?}
    POST   /api/todo/<id>/done     — mark done
    GET    /api/todo/<id>/history  — change history
    GET    /api/todo/tags          — list all tags
    GET    /api/todo/due           — due within N days (?days=7)
    DELETE /api/todo/<id>          — (not supported yet)
"""
import math
import traceback
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    try:
        from todotool import db as sqlite_db
        try:
            from todotool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        conn, _ = get_connection('todotool', sqlite_init_fn=sqlite_db.get_conn, pg_init_fn=pg_init)
        return conn
    except Exception as e:
        raise ConnectionError(f"Database connection failed: {e}")


def _row_to_dict(row):
    if row is None:
        return None
    if hasattr(row, 'keys'):
        return dict(row)
    return row


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
    """Handle /api/todo/* requests."""
    try:
        from todotool import db
        conn = _get_conn()
        username = user.get('username', '')
        parts = path.strip('/').split('/')  # e.g. ['api', 'todo', 'list']
        sub = parts[2] if len(parts) > 2 else 'list'

        # GET /api/todo/list
        if method == 'GET' and sub == 'list':
            params = body or {}
            
            # Pagination params
            try:
                page = int(params.get('page', 1))
                per_page = int(params.get('per_page', 20))
                if page < 1:
                    page = 1
                if per_page < 1 or per_page > 100:
                    per_page = 20
            except (ValueError, TypeError):
                return 400, {'error': 'Invalid pagination parameters'}
            
            rows = db.list_todos(conn,
                                 status=params.get('status'),
                                 tag=params.get('tag'),
                                 priority=params.get('priority'),
                                 limit=None)  # Get all, then paginate
            items = [_row_to_dict(r) for r in rows]
            return 200, _paginate(items, page, per_page)

        # GET /api/todo/tags
        if method == 'GET' and sub == 'tags':
            tags = db.list_all_tags(conn)
            return 200, [_row_to_dict(t) for t in tags]

        # GET /api/todo/due
        if method == 'GET' and sub == 'due':
            params = body or {}
            try:
                days = int(params.get('days', 7))
            except (ValueError, TypeError):
                return 400, {'error': 'Invalid days parameter'}
            
            rows = db.list_due_within(conn, days)
            return 200, [_row_to_dict(r) for r in rows]

        # POST /api/todo/add
        if method == 'POST' and sub == 'add':
            # Input validation
            if not body:
                return 400, {'error': 'Request body is required'}
            if 'title' not in body or not body['title']:
                return 400, {'error': 'title is required'}
            
            todo_id = db.add_todo(conn, body['title'],
                                  priority=body.get('priority', 'medium'),
                                  due_date=body.get('due_date'),
                                  note=body.get('note', ''),
                                  created_by=username,
                                  tags=body.get('tags'))
            return 201, {'id': todo_id, 'message': 'created'}

        # Numeric ID routes
        try:
            item_id = int(sub)
        except (ValueError, TypeError):
            return 404, {'error': 'not found'}

        action = parts[3] if len(parts) > 3 else None

        # POST /api/todo/<id>/done
        if method == 'POST' and action == 'done':
            db.mark_done(conn, item_id, changed_by=username)
            return 200, {'message': 'marked done'}

        # GET /api/todo/<id>/history
        if method == 'GET' and action == 'history':
            rows = db.get_history(conn, item_id)
            return 200, [_row_to_dict(r) for r in rows]

        # GET /api/todo/<id>
        if method == 'GET' and action is None:
            row = db.get_todo(conn, item_id)
            if not row:
                return 404, {'error': 'Todo not found'}
            return 200, _row_to_dict(row)

        # PUT /api/todo/<id>
        if method == 'PUT' and action is None:
            if not body:
                return 400, {'error': 'Request body is required'}
            
            db.edit_todo(conn, item_id,
                         title=body.get('title'),
                         priority=body.get('priority'),
                         due_date=body.get('due_date'),
                         note=body.get('note'),
                         tags=body.get('tags'),
                         changed_by=username)
            return 200, {'message': 'updated'}

        return 404, {'error': 'not found'}
    
    except ConnectionError as e:
        return 503, {'error': str(e)}
    except ValueError as e:
        return 400, {'error': f'Invalid input: {str(e)}'}
    except Exception as e:
        # Log unexpected errors
        tb = traceback.format_exc()
        print(f"Error in todo route: {e}\n{tb}")
        return 500, {'error': f'Internal server error: {str(e)}'}
