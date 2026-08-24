from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    priority_tier: int
    cgpa_cutoff: float
    interview_duration: int
    panel_count: int


class CompanyResponse(CompanyCreate):
    id: int

    class Config:
        from_attributes = True