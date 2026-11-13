import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4
from .settings import DATABASE_URL
_LOCK = threading.RLock()
TABLES = {'datasets', 'studies', 'runs', 'reviews', 'reports', 'users', 'audit'}
def now():
    return datetime.now(timezone.utc).isoformat()
@contextmanager
def connect():
    if DATABASE_URL.startswith('sqlite:///'):
        db = sqlite3.connect(DATABASE_URL[10:], timeout=30, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
    else:
        import psycopg
        from psycopg.rows import dict_row
        db = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def execute(db, sql, values=()):
    return db.execute(sql if DATABASE_URL.startswith('sqlite:') else sql.replace('?', '%s'), values)
def _columns(db, table):
    if DATABASE_URL.startswith('sqlite:'):
        return {row[1] for row in db.execute(f'PRAGMA table_info({table})')}
    return {r['column_name'] for r in execute(db, 'SELECT column_name FROM information_schema.columns WHERE table_name=?', (table,))}
# runs 的认领/租约列：status、claim_token、claimed_at 与 payload 同步，供原子条件更新
RUN_SYNC_COLUMNS = ('status', 'claim_token', 'claimed_at')
def initialize():
    from pathlib import Path
    sql = (Path(__file__).parents[2] / 'migrations' / '001_initial.sql').read_text()
    with _LOCK, connect() as db:
        for statement in sql.split(';'):
            if statement.strip(): db.execute(statement)
        existing = _columns(db, 'runs')
        for column in RUN_SYNC_COLUMNS:
            if column not in existing:
                execute(db, f'ALTER TABLE runs ADD COLUMN {column} TEXT')
        execute(db, 'CREATE INDEX IF NOT EXISTS runs_status ON runs(status)')
        for row in execute(db, 'SELECT id, payload FROM runs WHERE status IS NULL').fetchall():
            data = json.loads(row['payload'])
            execute(db, 'UPDATE runs SET status=?, claim_token=?, claimed_at=? WHERE id=?',
                    (data.get('status'), data.get('claim_token'), data.get('claimed_at'), row['id']))
def decode(row):
    if row is None: return None
    return json.loads(row['payload'])
def all_records(table):
    assert table in TABLES
    with connect() as db:
        return [decode(x) for x in execute(db, f'SELECT payload FROM {table} ORDER BY created_at DESC').fetchall()]
def get(table, record_id):
    assert table in TABLES
    with connect() as db:
        return decode(execute(db, f'SELECT payload FROM {table} WHERE id=?', (record_id,)).fetchone())
def save(table, data, insert_only=False):
    assert table in TABLES
    data = dict(data)
    data.setdefault('id', str(uuid4()))
    data.setdefault('created_at', now())
    columns = ['id', 'created_at', 'payload']
    values = [data['id'], data['created_at'], json.dumps(data, ensure_ascii=False)]
    refs = {'studies':['dataset_id'], 'runs':['study_id'] + list(RUN_SYNC_COLUMNS), 'reviews':['run_id'], 'reports':['review_id']}.get(table, [])
    for key in refs:
        columns.append(key); values.append(data.get(key))
    suffix = 'DO NOTHING' if insert_only else 'DO UPDATE SET ' + ','.join(f'{c}=excluded.{c}' for c in columns[1:])
    with _LOCK, connect() as db:
        execute(db, f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)}) ON CONFLICT(id) {suffix}', values)
    return get(table, data['id'])
def transition_run(record_id, updates, expect_statuses=None, expect_token=None, expect_claimed_at=None):
    """原子条件更新运行：前置条件不满足时返回None，调用方不得再写入。用于认领、心跳、完成与恢复。"""
    with _LOCK, connect() as db:
        row = execute(db, 'SELECT payload FROM runs WHERE id=?', (record_id,)).fetchone()
        if not row: return None
        data = json.loads(row['payload'])
        data.update(updates)
        sql = 'UPDATE runs SET status=?, claim_token=?, claimed_at=?, payload=? WHERE id=?'
        values = [data.get('status'), data.get('claim_token'), data.get('claimed_at'), json.dumps(data, ensure_ascii=False), record_id]
        if expect_statuses is not None:
            sql += f' AND status IN ({",".join("?" for _ in expect_statuses)})'
            values += list(expect_statuses)
        if expect_token is not None:
            sql += ' AND claim_token=?'
            values.append(expect_token)
        if expect_claimed_at is not None:
            sql += ' AND claimed_at=?'
            values.append(expect_claimed_at)
        cursor = execute(db, sql, values)
        return data if cursor.rowcount else None
