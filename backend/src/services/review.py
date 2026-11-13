from fastapi import HTTPException
from src.config.database import save,get,all_records,now
from src.models.review import Review
from src.services.run import require_run
from src.services.report import create_report

def list_reviews(): return all_records('reviews')
def create_review(payload,user):
    run=require_run(payload.run_id)
    if run['status']!='succeeded': raise HTTPException(409,'请等待成功运行再提交复查')
    rule_ids={r['rule_id'] for r in run['result']['rules']}
    if not set(payload.rule_ids)<=rule_ids: raise HTTPException(422,'包含不存在的规则')
    row=Review(payload.run_id,sorted(set(payload.rule_ids)),payload.note,'pending').to_record()
    row['submitted_by']=user['email']
    return save('reviews',row)
def decide_review(record_id,payload,user):
    row=get('reviews',record_id)
    if not row: raise HTTPException(404,'复查不存在')
    if row['status']!='pending': raise HTTPException(409,'复查已处理')
    if payload.status=='approved':
        create_report(row)
    row.update(status=payload.status,reviewed_by=user['email'],reviewed_at=now())
    return save('reviews',row)
