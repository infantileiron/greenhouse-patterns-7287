from fastapi import APIRouter,Depends
from fastapi.responses import FileResponse
from src.controllers.report import list_reports,download_report
from src.utils.security import current_user
from src.schemas.report import ReportRecord
router=APIRouter(prefix='/reports',tags=['reports'])
@router.get('',response_model=list[ReportRecord])
def index(user=Depends(current_user)): return list_reports()
@router.get('/{record_id}/download')
def download(record_id:str,user=Depends(current_user)):
    row=download_report(record_id)
    return FileResponse(row['path'],media_type='text/csv',filename=f'greenhouse-review-{record_id}.csv')
