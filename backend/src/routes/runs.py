from fastapi import APIRouter,Depends
from src.controllers.run import list_runs,create_run,require_run
from src.schemas.run import RunCreate
from src.utils.security import current_user,writer
router=APIRouter(prefix='/runs',tags=['runs'])
@router.get('')
def index(user=Depends(current_user)): return list_runs()
@router.post('',status_code=202)
def create(payload:RunCreate,user=Depends(writer)): return create_run(payload)
@router.get('/{record_id}')
def detail(record_id:str,user=Depends(current_user)): return require_run(record_id)
