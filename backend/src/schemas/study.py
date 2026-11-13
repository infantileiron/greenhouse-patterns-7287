from pydantic import BaseModel, Field
class StudyCreate(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    dataset_id: str
    min_support: float = Field(default=.12,ge=.02,le=.8)
    min_confidence: float = Field(default=.65,ge=.1,le=1)
    permutations: int = Field(default=999,ge=99,le=1999)
    seed: int = Field(default=261105,ge=0,le=2147483647)
