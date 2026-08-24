from pydantic import BaseModel


class StudentCreate(BaseModel):
    name: str
    cgpa: float
    branch: str
    status: str = "active"


class StudentResponse(StudentCreate):
    id: int

    class Config:
        from_attributes = True