"""AccounTool REST API routes.

Endpoints:
    GET    /api/account/list         — list transactions (?start=&end=&type=&category_id=&keyword=&page=&per_page=)
    POST   /api/account/add          — add transaction {date, type, amount, category_id, note?}
    DELETE /api/account/<id>         — delete transaction
    GET    /api/account/balance      — current balance
    GET    /api/account/report       — monthly report (?year=&month=)
    GET    /api/account/stats        — category stats (?start=&end=)
    GET    /api/account/categories   — list categories (?type=)
    POST   /api/account/categories   — add category {name, type, description?}
    GET    /api/account/reminders    — list reminders
    POST   /api/account/reminders    — add reminder {name, amount, category_id, day_of_month, note?}
"""
import math
import traceback
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    try:
        from accountool import db as sqlite_db
        try:
            from accountool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        conn, _ = get_connection('accountool', sqlite_init_fn=sqlite_db.get_conn, pg_init_fn=pg_init)
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
        from accountool import db
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
            
            rows = db.list_transactions(conn,
                                        start_date=p.get('start'),
                                        end_date=p.get('end'),
                                        type_=p.get('type'),
                                        category_id=p.get('category_id'),
                                        keyword=p.get('keyword'),
                                        limit=None)
            items = [_row(r) for r in rows]
            return 200, _paginate(items, page, per_page)

        if method == 'POST' and sub == 'add':
            # Input validation
            if not body:
                return 400, {'error': 'Request body is required'}
            
            missing = []
            for k in ('date', 'type', 'amount', 'category_id'):
                if k not in body:
                    missing.append(k)
            if missing:
                return 400, {'error': f'Missing required fields: {", ".join(missing)}'}
            
            # Validate type
            if body['type'] not in ('income', 'expense'):
                return 400, {'error': 'type must be either "income" or "expense"'}
            
            # Validate amount is numeric
            try:
                amount = float(body['amount'])
                if amount <= 0:
                    return 400, {'error': 'amount must be greater than 0'}
            except (ValueError, TypeError):
                return 400, {'error': 'amount must be a valid number'}
            
            try:
                category_id = int(body['category_id'])
            except (ValueError, TypeError):
                return 400, {'error': 'category_id must be a valid integer'}
            
            txn_id = db.add_transaction(conn, body['date'], body['type'],
                                        amount, category_id,
                                        note=body.get('note', ''),
                                        created_by=username)
            return 201, {'id': txn_id, 'message': 'created'}

        if method == 'GET' and sub == 'balance':
            result = db.get_balance(conn)
            return 200, _row(result)

        if method == 'GET' and sub == 'report':
            p = body or {}
            if 'year' not in p or 'month' not in p:
                return 400, {'error': 'year and month are required'}
            
            try:
                year = int(p['year'])
                month = int(p['month'])
                if month < 1 or month > 12:
                    return 400, {'error': 'month must be between 1 and 12'}
            except (ValueError, TypeError):
                return 400, {'error': 'year and month must be valid integers'}
            
            rows = db.monthly_report(conn, year, month)
            return 200, [_row(r) for r in rows]

        if method == 'GET' and sub == 'stats':
            p = body or {}
            rows = db.category_stats(conn, start_date=p.get('start'), end_date=p.get('end'))
            return 200, [_row(r) for r in rows]

        if method == 'GET' and sub == 'categories':
            p = body or {}
            rows = db.list_categories(conn, type_=p.get('type'))
            return 200, [_row(r) for r in rows]

        if method == 'POST' and sub == 'categories':
            if not body:
                return 400, {'error': 'Request body is required'}
            if 'name' not in body or not body['name']:
                return 400, {'error': 'name is required'}
            if 'type' not in body or body['type'] not in ('income', 'expense'):
                return 400, {'error': 'type is required and must be "income" or "expense"'}
            
            cat_id = db.add_category(conn, body['name'], body['type'],
                                     description=body.get('description', ''))
            return 201, {'id': cat_id, 'message': 'created'}

        if method == 'GET' and sub == 'reminders':
            rows = db.list_reminders(conn)
            return 200, [_row(r) for r in rows]

        if method == 'POST' and sub == 'reminders':
            if not body:
                return 400, {'error': 'Request body is required'}
            
            missing = []
            for k in ('name', 'amount', 'category_id', 'day_of_month'):
                if k not in body:
                    missing.append(k)
            if missing:
                return 400, {'error': f'Missing required fields: {", ".join(missing)}'}
            
            try:
                amount = float(body['amount'])
                category_id = int(body['category_id'])
                day = int(body['day_of_month'])
                if day < 1 or day > 31:
                    return 400, {'error': 'day_of_month must be between 1 and 31'}
            except (ValueError, TypeError):
                return 400, {'error': 'Invalid numeric field values'}
            
            r_id = db.add_reminder(conn, body['name'], amount,
                                   category_id, day,
                                   note=body.get('note', ''))
            return 201, {'id': r_id, 'message': 'created'}

        # DELETE /api/account/<id>
        try:
            item_id = int(sub)
        except (ValueError, TypeError):
            return 404, {'error': 'not found'}

        if method == 'DELETE':
            db.delete_transaction(conn, item_id)
            return 200, {'message': 'deleted'}

        return 404, {'error': 'not found'}
    
    except ConnectionError as e:
        return 503, {'error': str(e)}
    except ValueError as e:
        return 400, {'error': f'Invalid input: {str(e)}'}
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in account route: {e}\n{tb}")
        return 500, {'error': f'Internal server error: {str(e)}'}
