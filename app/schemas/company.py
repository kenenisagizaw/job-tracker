from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)

class CompanyUpdate(CompanyCreate):
    pass


class CompanyRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
