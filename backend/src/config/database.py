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
def initialize():
    from pathlib import Path
    sql = (Path(__file__).parents[2] / 'migrations' / '001_initial.sql').read_text()
    with _LOCK, connect() as db:
        for statement in sql.split(';'):
            if statement.strip(): db.execute(statement)
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
    refs = {'studies':['dataset_id'], 'runs':['study_id'], 'reviews':['run_id'], 'reports':['review_id']}.get(table, [])
    for key in refs:
        columns.append(key); values.append(data[key])
    suffix = 'DO NOTHING' if insert_only else 'DO UPDATE SET ' + ','.join(f'{c}=excluded.{c}' for c in columns[1:])
    with _LOCK, connect() as db:
        execute(db, f'INSERT INTO {table} ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)}) ON CONFLICT(id) {suffix}', values)
    return get(table, data['id'])
