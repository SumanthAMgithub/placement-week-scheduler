from pydantic import BaseModel


class PanelCreate(BaseModel):
    name: str
    company_id: int
    status: str = "available"


class PanelResponse(PanelCreate):
    id: int

    class Config:
        from_attributes = True