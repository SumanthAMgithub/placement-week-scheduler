from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import Panel
from backend.schemas.panel import PanelResponse


router = APIRouter(
    prefix="/panels",
    tags=["Panels"]
)


@router.get("/", response_model=list[PanelResponse])
def get_panels(
    db: Session = Depends(get_db)
):
    return db.query(Panel).all()