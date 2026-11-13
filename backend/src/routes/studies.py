from fastapi import APIRouter,Depends
from src.controllers.study import list_studies,create_study
from src.schemas.study import StudyCreate
from src.utils.security import current_user,writer
router=APIRouter(prefix='/studies',tags=['studies'])
@router.get('')
def index(user=Depends(current_user)): return list_studies()
@router.post('',status_code=201)
def create(payload:StudyCreate,user=Depends(writer)): return create_study(payload)
