"""HealthTool REST API routes.

Endpoints:
    GET    /api/health/status      — latest status (?machine=)
    POST   /api/health/run         — run health checks
    GET    /api/health/history     — check history (?machine=&check=&limit=&days=)
    GET    /api/health/machines    — list machines
"""
from hurricanesoft_cli.db_factory import get_connection
import socket


def _get_conn():
    from healthtool import db as sqlite_db
    conn, _ = get_connection('healthtool', sqlite_init_fn=sqlite_db.get_conn)
    return conn


def _row(r):
    if r is None:
        return None
    return dict(r) if hasattr(r, 'keys') else r


def handle(method, path, body, user):
    from healthtool import db, checks
    conn = _get_conn()
    parts = path.strip('/').split('/')
    sub = parts[2] if len(parts) > 2 else 'status'

    if method == 'GET' and sub == 'status':
        p = body or {}
        machine = p.get('machine', socket.gethostname())
        rows = db.get_latest(conn, machine)
        return 200, [_row(r) for r in rows] if rows else []

    if method == 'POST' and sub == 'run':
        machine = socket.gethostname()
        results = []
        results.append(checks.check_cpu())
        results.append(checks.check_memory())
        results.append(checks.check_disk('/'))
        results.append(checks.check_network())
        for r in results:
            db.save_check(conn, machine, r['name'], r['status'], r.get('detail', ''), r)
        return 200, results

    if method == 'GET' and sub == 'history':
        p = body or {}
        rows = db.get_history(conn,
                              machine=p.get('machine'),
                              check_name=p.get('check'),
                              limit=int(p.get('limit', 100)),
                              days=int(p.get('days', 30)))
        return 200, [_row(r) for r in rows]

    if method == 'GET' and sub == 'machines':
        rows = db.list_machines(conn)
        return 200, [_row(r) for r in rows]

    return 404, {'error': 'not found'}
