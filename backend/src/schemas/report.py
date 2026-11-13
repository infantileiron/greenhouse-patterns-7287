from pydantic import BaseModel
class ReportRecord(BaseModel):
    id: str
    review_id: str
    name: str
    created_at: str
