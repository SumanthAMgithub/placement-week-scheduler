from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import TimeSlot
from backend.schemas.schedule import TimeSlotResponse


router = APIRouter(
    prefix="/time-slots",
    tags=["Time Slots"]
)


@router.get("/", response_model=list[TimeSlotResponse])
def get_time_slots(
    db: Session = Depends(get_db)
):
    return db.query(TimeSlot).all()