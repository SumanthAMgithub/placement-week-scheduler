from pydantic import BaseModel


class TimeSlotResponse(BaseModel):
    id: int
    day: int
    start_time: str
    end_time: str

    class Config:
        from_attributes = True