from fastapi import APIRouter,Depends,Query
from src.controllers.dataset import list_datasets,create_dataset,samples
from src.schemas.dataset import DatasetCreate
from src.utils.security import current_user,writer
router=APIRouter(prefix='/datasets',tags=['datasets'])
@router.get('')
def index(user=Depends(current_user)): return list_datasets()
@router.post('',status_code=201)
def create(payload:DatasetCreate,user=Depends(writer)): return create_dataset(payload)
@router.get('/{record_id}/samples')
def detail(record_id:str,offset:int=Query(0,ge=0),limit:int=Query(40,ge=1,le=100),user=Depends(current_user)):
    return samples(record_id,offset,limit)
