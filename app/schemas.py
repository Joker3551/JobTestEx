from pydantic import BaseModel,Field, field_validator
from datetime import date

class DepartmentSchema(BaseModel):
    name: str = Field(min_length=1,max_length=200)
    parent_id: int | None = None
    
    @field_validator("name")
    @classmethod
    def trim_name(cls, v: str):
        return v.strip()

class EmployeerSchema(BaseModel):
    full_name: str = Field(min_length=1,max_length=200)
    position: str = Field(min_length=1,max_length=200)
    hired_at: date | None = None

class DepartmentUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None