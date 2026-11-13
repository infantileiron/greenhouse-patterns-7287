from fastapi import APIRouter,Depends
from src.controllers.review import list_reviews,create_review,decide_review
from src.schemas.review import ReviewCreate,ReviewDecision
from src.utils.security import current_user,writer,admin
router=APIRouter(prefix='/reviews',tags=['reviews'])
@router.get('')
def index(user=Depends(current_user)): return list_reviews()
@router.post('',status_code=201)
def create(payload:ReviewCreate,user=Depends(writer)): return create_review(payload,user)
@router.patch('/{record_id}')
def decide(record_id:str,payload:ReviewDecision,user=Depends(admin)): return decide_review(record_id,payload,user)
