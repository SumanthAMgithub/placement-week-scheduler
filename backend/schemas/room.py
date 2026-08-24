from pydantic import BaseModel


class RoomCreate(BaseModel):
    name: str
    capacity: int
    status: str = "available"


class RoomResponse(RoomCreate):
    id: int

    class Config:
        from_attributes = True