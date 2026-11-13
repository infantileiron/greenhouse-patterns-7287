from src.config.database import save, all_records, get
from src.models.study import Study
from src.services.dataset import require_dataset
from fastapi import HTTPException

def list_studies(): return all_records('studies')
def require_study(record_id):
    record=get('studies',record_id)
    if not record: raise HTTPException(404,'研究不存在')
    return record
def create_study(payload):
    require_dataset(payload.dataset_id)
    return save('studies',Study(**payload.model_dump()).to_record())
