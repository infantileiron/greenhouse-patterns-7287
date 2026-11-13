import logging
import os
import signal
import time
from pathlib import Path
from src.config.database import initialize,all_records
from src.config.settings import QUEUE_MODE
from src.utils.redis_queue import pop
from src.services.run import execute_run
stop=False
def halt(*_):
    global stop
    stop=True
signal.signal(signal.SIGTERM,halt)
signal.signal(signal.SIGINT,halt)
def main():
    initialize()
    heartbeat=Path(os.getenv('WORKER_HEARTBEAT','/tmp/greenhouse-worker-heartbeat'))
    while not stop:
        heartbeat.write_text(str(time.time()))
        try:
            if QUEUE_MODE=='redis': record_id=pop()
            else:
                queued=sorted([r for r in all_records('runs') if r['status']=='queued'],key=lambda r:r['created_at'])
                record_id=queued[0]['id'] if queued else None
                if not record_id: time.sleep(.5)
            if record_id: execute_run(record_id)
        except Exception:
            logging.exception('Worker retry'); time.sleep(2)
if __name__=='__main__': main()
