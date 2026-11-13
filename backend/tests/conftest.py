import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

_db = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False).name
os.environ['DATABASE_URL'] = f'sqlite:///{_db}'
os.environ['QUEUE_MODE'] = 'database'
os.environ['SEED_DEMO'] = 'false'

import pytest  # noqa: E402

from src.config.database import initialize, all_records, save  # noqa: E402

initialize()


@pytest.fixture(autouse=True)
def _terminal_cleanup():
    """每个用例结束后把未终结的运行置为失败，避免占用全局活跃名额影响其他用例。"""
    yield
    for row in all_records('runs'):
        if row['status'] in ('queued', 'running', 'recovering'):
            row.update(status='failed', error='用例清理', claim_token=None)
            save('runs', row)
