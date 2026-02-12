"""AccounTool REST API routes.

Endpoints:
    GET    /api/account/list         — list transactions (?start=&end=&type=&category_id=&keyword=&limit=)
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
from hurricanesoft_cli.db_factory import get_connection


def _get_conn():
    from accountool import db as sqlite_db
    try:
        from accountool import db_pg
        pg_init = db_pg.get_conn
    except (ImportError, RuntimeError):
        pg_init = None
    conn, _ = get_connection('accountool', sqlite_init_fn=sqlite_db.get_conn, pg_init_fn=pg_init)
    return conn


def _row(r):
    if r is None:
        return None
    return dict(r) if hasattr(r, 'keys') else r


def handle(method, path, body, user):
    from accountool import db
    conn = _get_conn()
    username = user.get('username', '')
    parts = path.strip('/').split('/')
    sub = parts[2] if len(parts) > 2 else 'list'

    if method == 'GET' and sub == 'list':
        p = body or {}
        rows = db.list_transactions(conn,
                                    start_date=p.get('start'),
                                    end_date=p.get('end'),
                                    type_=p.get('type'),
                                    category_id=p.get('category_id'),
                                    keyword=p.get('keyword'),
                                    limit=int(p.get('limit', 50)))
        return 200, [_row(r) for r in rows]

    if method == 'POST' and sub == 'add':
        if not body:
            return 400, {'error': 'body required'}
        for k in ('date', 'type', 'amount', 'category_id'):
            if k not in body:
                return 400, {'error': f'{k} is required'}
        txn_id = db.add_transaction(conn, body['date'], body['type'],
                                    float(body['amount']), int(body['category_id']),
                                    note=body.get('note', ''),
                                    created_by=username)
        return 201, {'id': txn_id, 'message': 'created'}

    if method == 'GET' and sub == 'balance':
        result = db.get_balance(conn)
        return 200, _row(result)

    if method == 'GET' and sub == 'report':
        p = body or {}
        if 'year' not in p or 'month' not in p:
            return 400, {'error': 'year and month required'}
        rows = db.monthly_report(conn, int(p['year']), int(p['month']))
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
        if not body or 'name' not in body or 'type' not in body:
            return 400, {'error': 'name and type required'}
        cat_id = db.add_category(conn, body['name'], body['type'],
                                 description=body.get('description', ''))
        return 201, {'id': cat_id, 'message': 'created'}

    if method == 'GET' and sub == 'reminders':
        rows = db.list_reminders(conn)
        return 200, [_row(r) for r in rows]

    if method == 'POST' and sub == 'reminders':
        if not body:
            return 400, {'error': 'body required'}
        for k in ('name', 'amount', 'category_id', 'day_of_month'):
            if k not in body:
                return 400, {'error': f'{k} is required'}
        r_id = db.add_reminder(conn, body['name'], float(body['amount']),
                               int(body['category_id']), int(body['day_of_month']),
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
