from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import Company
from backend.schemas.company import (
    CompanyCreate,
    CompanyResponse
)


router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)


@router.post("/", response_model=CompanyResponse)
def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db)
):
    new_company = Company(
        name=company.name,
        priority_tier=company.priority_tier,
        cgpa_cutoff=company.cgpa_cutoff,
        interview_duration=company.interview_duration,
        panel_count=company.panel_count
    )

    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return new_company


@router.get("/", response_model=list[CompanyResponse])
def get_companies(
    db: Session = Depends(get_db)
):
    return db.query(Company).all()