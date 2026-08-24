from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import Room
from backend.schemas.room import (
    RoomCreate,
    RoomResponse
)


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


@router.post("/", response_model=RoomResponse)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):
    new_room = Room(
        name=room.name,
        capacity=room.capacity,
        status=room.status
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room


@router.get("/", response_model=list[RoomResponse])
def get_rooms(
    db: Session = Depends(get_db)
):
    return db.query(Room).all()