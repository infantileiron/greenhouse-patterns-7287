import csv
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException
from src.config.database import all_records,save,get
from src.config.settings import ARTIFACT_DIR
from src.models.report import Report
from src.services.run import require_run

def list_reports():
    return [{k:v for k,v in x.items() if k!='path'} for x in all_records('reports')]
def create_report(review):
    existing=next((r for r in all_records('reports') if r['review_id']==review['id']),None)
    if existing: return existing
    run=require_run(review['run_id']); selected=set(review['rule_ids'])
    rows=[r for r in run['result']['rules'] if r['rule_id'] in selected]
    ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
    file_id=str(uuid4()); path=ARTIFACT_DIR/f'{file_id}.csv'
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['rule_id','antecedent','consequent','support_count','sample_count','support','confidence','lift','p_value','q_value','checksum','note'])
        for rule in rows:
            # Neutralize spreadsheet formula injection in user-provided symptom labels and notes.
            def safe(value):
                text=str(value)
                return "'"+text if text.lstrip().startswith(('=','+','-','@')) else text
            writer.writerow([safe(rule['rule_id']),safe(' + '.join(rule['antecedent'])),safe(rule['consequent']),rule['count'],run['result']['sample_count'],rule['support'],rule['confidence'],rule['lift'],rule['p_value'],rule['q_value'],run['result']['checksum'],safe(review['note'])])
    return save('reports',Report(review['id'],'南岭温室复查清单',str(path.resolve())).to_record())
def download_report(report_id):
    record=get('reports',report_id)
    if not record: raise HTTPException(404,'报告不存在')
    review=get('reviews',record['review_id'])
    if not review or review['status']!='approved': raise HTTPException(403,'报告尚未批准')
    if not Path(record['path']).is_file(): raise HTTPException(410,'产物丢失，请重新生成报告')
    return record
