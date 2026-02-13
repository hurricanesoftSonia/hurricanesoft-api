"""Dashboard REST API route.

Endpoint:
    GET /api/dashboard — aggregate system stats
"""
import traceback
import time
from hurricanesoft_cli.db_factory import get_connection
from hurricanesoft_api import __version__


# Server start time for uptime calculation
_start_time = time.time()


def _get_conn(tool_name, sqlite_init_fn, pg_init_fn=None):
    """Helper to get DB connection for a tool."""
    try:
        conn, _ = get_connection(tool_name, sqlite_init_fn=sqlite_init_fn, pg_init_fn=pg_init_fn)
        return conn
    except Exception:
        return None


def _get_todo_stats():
    """Get todo statistics."""
    try:
        from todotool import db as sqlite_db
        try:
            from todotool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        
        conn = _get_conn('todotool', sqlite_db.get_conn, pg_init)
        if not conn:
            return {'error': 'DB unavailable'}
        
        from todotool import db
        all_todos = db.list_todos(conn, limit=None)
        
        pending = sum(1 for t in all_todos if dict(t).get('status') != 'done')
        completed = sum(1 for t in all_todos if dict(t).get('status') == 'done')
        
        return {
            'pending': pending,
            'completed': completed,
            'total': len(all_todos)
        }
    except Exception as e:
        return {'error': str(e)}


def _get_memo_stats():
    """Get memo statistics."""
    try:
        from memotool import db as sqlite_db
        try:
            from memotool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        
        conn = _get_conn('memotool', sqlite_db.init_db, pg_init)
        if not conn:
            return {'error': 'DB unavailable'}
        
        from memotool import db
        all_memos = db.list_memos(conn, limit=None)
        
        return {
            'total': len(all_memos)
        }
    except Exception as e:
        return {'error': str(e)}


def _get_msg_stats(username):
    """Get message statistics."""
    try:
        from msgtool import db as sqlite_db
        try:
            from msgtool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        
        conn = _get_conn('msgtool', sqlite_db.init_db, pg_init)
        if not conn:
            return {'error': 'DB unavailable'}
        
        from msgtool import db
        unread = db.count_unread(conn, username)
        
        return {
            'unread': unread
        }
    except Exception as e:
        return {'error': str(e)}


def _get_mail_stats():
    """Get mail statistics."""
    try:
        from mailtool import db as sqlite_db
        conn = _get_conn('mailtool', sqlite_db.get_conn)
        if not conn:
            return {'error': 'DB unavailable'}
        
        from mailtool import db
        messages = db.list_messages(conn, folder='inbox', limit=None, is_read=0)
        
        return {
            'unread': len(messages)
        }
    except Exception as e:
        return {'error': str(e)}


def _get_announce_stats():
    """Get announcement statistics."""
    try:
        from announcetool import db as sqlite_db
        try:
            from announcetool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        
        conn = _get_conn('announcetool', sqlite_db.init_db, pg_init)
        if not conn:
            return {'error': 'DB unavailable'}
        
        from announcetool import db
        # Count announcements that need acknowledgement (not archived)
        announcements = db.list_announcements(conn, archived=False, limit=None)
        
        return {
            'pending': len(announcements)
        }
    except Exception as e:
        return {'error': str(e)}


def _get_health_status():
    """Get health check status."""
    try:
        from hurricanesoft_cli.db_factory import get_connection
        from healthtool import db as sqlite_db
        try:
            from healthtool import db_pg
            pg_init = db_pg.get_conn
        except (ImportError, RuntimeError):
            pg_init = None
        
        conn = _get_conn('healthtool', sqlite_db.get_conn, pg_init)
        if not conn:
            return {'status': 'unavailable'}
        
        from healthtool import db
        latest = db.latest_check(conn)
        
        if latest:
            return {
                'status': dict(latest).get('status', 'unknown'),
                'last_check': dict(latest).get('check_time')
            }
        
        return {'status': 'no_data'}
    except Exception:
        return {'status': 'error'}


def _get_system_info():
    """Get system information."""
    uptime_seconds = int(time.time() - _start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    
    return {
        'version': __version__,
        'uptime': f"{hours}h {minutes}m",
        'uptime_seconds': uptime_seconds
    }


def handle(method, path, body, user):
    """Handle /api/dashboard requests."""
    try:
        if method != 'GET':
            return 405, {'error': 'Method not allowed'}
        
        username = user.get('username', '')
        
        # Aggregate all stats
        dashboard = {
            'todo': _get_todo_stats(),
            'memo': _get_memo_stats(),
            'msg': _get_msg_stats(username),
            'mail': _get_mail_stats(),
            'announce': _get_announce_stats(),
            'health': _get_health_status(),
            'system': _get_system_info()
        }
        
        return 200, dashboard
    
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error in dashboard route: {e}\n{tb}")
        return 500, {'error': f'Internal server error: {str(e)}'}
