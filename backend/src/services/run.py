import logging
import threading
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from src.config.database import save, get, all_records, now, transition_run
from src.config.settings import QUEUE_MODE, RUN_LEASE_SECONDS, RUN_HEARTBEAT_SECONDS, RUN_MAX_ATTEMPTS, RUN_REQUEUE_GRACE_SECONDS
from src.constants.enums import RunStatus
from src.models.run import Run
from src.services.study import require_study
from src.services.dataset import require_dataset
from src.services.mining import analyze
from src.utils.redis_queue import enqueue
from fastapi import HTTPException

ACTIVE_STATUSES = (RunStatus.QUEUED.value, RunStatus.RUNNING.value, RunStatus.RECOVERING.value)
CLAIMABLE_STATUSES = (RunStatus.QUEUED.value, RunStatus.RECOVERING.value)
LEASE_SECONDS = RUN_LEASE_SECONDS
HEARTBEAT_SECONDS = RUN_HEARTBEAT_SECONDS
MAX_ATTEMPTS = RUN_MAX_ATTEMPTS
REQUEUE_GRACE_SECONDS = RUN_REQUEUE_GRACE_SECONDS

def _ago(seconds):
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()

def list_runs(): return [{k:v for k,v in r.items() if k!='result'} for r in all_records('runs')]
def require_run(record_id):
    row=get('runs',record_id)
    if not row: raise HTTPException(404,'运行不存在')
    return row
def create_run(payload):
    require_study(payload.study_id)
    active=[r for r in all_records('runs') if r['status'] in ACTIVE_STATUSES]
    if len(active)>=3: raise HTTPException(429,'最多允许3个活跃挖掘任务，请等待完成')
    row=save('runs',Run(payload.study_id,RunStatus.QUEUED.value).to_record())
    try:
        if QUEUE_MODE=='redis': enqueue(row['id'])
        elif QUEUE_MODE!='database': raise ValueError('队列模式无效')
    except Exception:
        row.update(status=RunStatus.FAILED.value,error='队列不可用，请恢复Redis后重新运行')
        save('runs',row)
        raise HTTPException(503,'队列不可用，请恢复Redis后重新运行')
    return row

def claim_run(record_id):
    """原子认领：仅当运行处于 queued/recovering 时生效，返回(记录,令牌)；被他人抢先或已终结时返回None。"""
    token = str(uuid4())
    row = get('runs', record_id)
    if not row: return None
    claimed = transition_run(record_id, {
        'status': RunStatus.RUNNING.value,
        'claim_token': token,
        'claimed_at': now(),
        'started_at': now(),
        'finished_at': None,
        'attempts': int(row.get('attempts') or 0) + 1,
    }, expect_statuses=CLAIMABLE_STATUSES)
    return (claimed, token) if claimed else None

def heartbeat_claim(record_id, token):
    """续租：令牌失效（已被接管）时返回False，执行者必须放弃结果。"""
    return transition_run(record_id, {'claimed_at': now()},
        expect_statuses=(RunStatus.RUNNING.value,), expect_token=token) is not None

def finish_run(record_id, token, updates):
    """栅栏写回：只有当前持有令牌的执行者能写入结果，晚到结果返回None并被丢弃。"""
    return transition_run(record_id, updates,
        expect_statuses=(RunStatus.RUNNING.value,), expect_token=token)

def recover_stale_runs(deliver=None):
    """恢复中断的运行：租约过期的 running 重新排队为 recovering；同时补足队列中缺失的待办投递。"""
    recovered = []
    for row in all_records('runs'):
        status = row['status']
        if status == RunStatus.RUNNING.value and (row.get('claimed_at') or '') < _ago(LEASE_SECONDS):
            attempts = int(row.get('attempts') or 0)
            if attempts >= MAX_ATTEMPTS:
                transition_run(row['id'], {
                    'status': RunStatus.FAILED.value,
                    'error': f'计算连续{attempts}次被中断，已停止自动恢复，请检查样本后重新运行',
                    'finished_at': now(),
                }, expect_statuses=(RunStatus.RUNNING.value,), expect_claimed_at=row.get('claimed_at'))
                continue
            note = f'第{max(attempts,1)}次执行中断（执行者失联），已自动重新排队'
            stale = transition_run(row['id'], {
                'status': RunStatus.RECOVERING.value,
                'claim_token': None,
                'recovered_at': now(),
                'error': note,
            }, expect_statuses=(RunStatus.RUNNING.value,), expect_claimed_at=row.get('claimed_at'))
            if stale:
                recovered.append(stale['id'])
                if deliver: deliver(stale['id'])
        elif deliver and status == RunStatus.QUEUED.value and (row.get('created_at') or '') < _ago(REQUEUE_GRACE_SECONDS):
            deliver(row['id'])  # 队列丢失时补投；重复投递由原子认领去重
        elif deliver and status == RunStatus.RECOVERING.value and (row.get('recovered_at') or '') < _ago(REQUEUE_GRACE_SECONDS):
            deliver(row['id'])
    return recovered

def execute_run(record_id):
    claimed = claim_run(record_id)
    if not claimed:
        return None  # 重复投递或他人已认领：本次送达无效
    row, token = claimed
    stop = threading.Event()
    def beat():
        while not stop.wait(HEARTBEAT_SECONDS):
            if not heartbeat_claim(record_id, token):
                logging.warning('运行 %s 租约丢失，停止心跳', record_id)
                return
    keeper = threading.Thread(target=beat, daemon=True)
    keeper.start()
    try:
        study = require_study(row['study_id'])
        dataset = require_dataset(study['dataset_id'])
        result = analyze(dataset['rows'], {k: study[k] for k in ('min_support','min_confidence','permutations','seed')})
        outcome = {'status': RunStatus.SUCCEEDED.value, 'result': result, 'error': None, 'finished_at': now()}
    except Exception as exc:
        outcome = {'status': RunStatus.FAILED.value, 'error': str(exc), 'finished_at': now()}
    finally:
        stop.set()
    saved = finish_run(record_id, token, outcome)
    if saved is None:
        logging.warning('运行 %s 的结果晚到，任务已被接管，结果丢弃', record_id)
    return saved
