import logging
import os
import signal
import time
from pathlib import Path
from src.config.database import initialize,all_records
from src.config.settings import QUEUE_MODE
from src.utils.redis_queue import pop,enqueue
from src.services.run import execute_run,recover_stale_runs
stop=False
def halt(*_):
    global stop
    stop=True
signal.signal(signal.SIGTERM,halt)
signal.signal(signal.SIGINT,halt)
def next_queued():
    pending=sorted([r for r in all_records('runs') if r['status'] in ('queued','recovering')],key=lambda r:r['created_at'])
    return pending[0]['id'] if pending else None
def main():
    initialize()
    heartbeat=Path(os.getenv('WORKER_HEARTBEAT','/tmp/greenhouse-worker-heartbeat'))
    while not stop:
        heartbeat.write_text(str(time.time()))
        try:
            recover_stale_runs(deliver=enqueue if QUEUE_MODE=='redis' else None)
            if QUEUE_MODE=='redis': record_id=pop()
            else:
                record_id=next_queued()
                if not record_id: time.sleep(.5)
            if record_id: execute_run(record_id)
        except Exception:
            logging.exception('Worker retry'); time.sleep(2)
if __name__=='__main__': main()
