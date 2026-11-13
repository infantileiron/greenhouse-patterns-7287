from src.config.database import save, get, all_records
from src.models.dataset import Dataset
from src.utils.csv_data import parse_samples, checksum
from fastapi import HTTPException

def summary(record):
    return {k:v for k,v in record.items() if k!='rows'} | {'sample_count':len(record['rows']), 'item_count':len(set(x for row in record['rows'] for x in row['symptoms']))}
def list_datasets(): return [summary(r) for r in all_records('datasets')]
def require_dataset(record_id):
    record=get('datasets',record_id)
    if not record: raise HTTPException(404,'调查批次不存在')
    return record
def create_dataset(payload):
    try: rows=parse_samples(payload.csv_text)
    except ValueError as exc: raise HTTPException(422,str(exc))
    record=Dataset(payload.name,payload.filename,rows).to_record()
    record['checksum']=checksum(rows)
    return summary(save('datasets',record))
def samples(dataset_id, offset=0, limit=40):
    record=require_dataset(dataset_id)
    return {'dataset':summary(record),'total':len(record['rows']),'rows':record['rows'][offset:offset+limit]}
