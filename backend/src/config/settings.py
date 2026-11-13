import os
from pathlib import Path
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./greenhouse.sqlite')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
QUEUE_MODE = os.getenv('QUEUE_MODE', 'redis')
JWT_SECRET = os.getenv('JWT_SECRET', 'local-demo-change-before-publishing-2105')
ARTIFACT_DIR = Path(os.getenv('ARTIFACT_DIR', './artifacts'))
SEED_DEMO = os.getenv('SEED_DEMO', 'false').lower() == 'true'
# 运行认领与恢复：租约秒数、心跳间隔、最多自动恢复次数、重新入队宽限秒数
RUN_LEASE_SECONDS = int(os.getenv('RUN_LEASE_SECONDS', '30'))
RUN_HEARTBEAT_SECONDS = int(os.getenv('RUN_HEARTBEAT_SECONDS', '5'))
RUN_MAX_ATTEMPTS = int(os.getenv('RUN_MAX_ATTEMPTS', '5'))
RUN_REQUEUE_GRACE_SECONDS = int(os.getenv('RUN_REQUEUE_GRACE_SECONDS', '15'))
