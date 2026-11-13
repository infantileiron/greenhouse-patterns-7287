from pydantic import BaseModel, Field
class DatasetCreate(BaseModel):
    name: str = Field(min_length=2,max_length=100)
    filename: str = Field(min_length=4,max_length=120)
    csv_text: str = Field(min_length=10,max_length=1500000)
