from src.config.database import save, get, all_records, now
from src.config.settings import QUEUE_MODE
from src.constants.enums import RunStatus
from src.models.run import Run
from src.services.study import require_study
from src.services.dataset import require_dataset
from src.services.mining import analyze
from src.utils.redis_queue import enqueue
from fastapi import HTTPException

def list_runs(): return [{k:v for k,v in r.items() if k!='result'} for r in all_records('runs')]
def require_run(record_id):
    row=get('runs',record_id)
    if not row: raise HTTPException(404,'运行不存在')
    return row
def create_run(payload):
    require_study(payload.study_id)
    active=[r for r in all_records('runs') if r['status'] in ('queued','running')]
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
def execute_run(record_id):
    row=require_run(record_id)
    if row['status']!='queued': return row
    row.update(status=RunStatus.RUNNING.value,started_at=now()); save('runs',row)
    try:
        study=require_study(row['study_id']); dataset=require_dataset(study['dataset_id'])
        result=analyze(dataset['rows'], {k:study[k] for k in ('min_support','min_confidence','permutations','seed')})
        row.update(status=RunStatus.SUCCEEDED.value,result=result,error=None,finished_at=now())
    except Exception as exc: row.update(status=RunStatus.FAILED.value,error=str(exc),finished_at=now())
    return save('runs',row)
