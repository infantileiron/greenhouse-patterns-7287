from pydantic import BaseModel, Field
from typing import Literal
class ReviewCreate(BaseModel):
    run_id: str
    rule_ids: list[str] = Field(min_length=1,max_length=100)
    note: str = Field(min_length=4,max_length=2000)
class ReviewDecision(BaseModel):
    status: Literal['approved','rejected']
