import os
from pathlib import Path
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./greenhouse.sqlite')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
QUEUE_MODE = os.getenv('QUEUE_MODE', 'redis')
JWT_SECRET = os.getenv('JWT_SECRET', 'local-demo-change-before-publishing-2105')
ARTIFACT_DIR = Path(os.getenv('ARTIFACT_DIR', './artifacts'))
SEED_DEMO = os.getenv('SEED_DEMO', 'false').lower() == 'true'
