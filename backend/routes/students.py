from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import Student
from backend.schemas.student import (
    StudentCreate,
    StudentResponse
)


router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


@router.post("/", response_model=StudentResponse)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    new_student = Student(
        name=student.name,
        cgpa=student.cgpa,
        branch=student.branch,
        status=student.status
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


@router.get("/", response_model=list[StudentResponse])
def get_students(
    db: Session = Depends(get_db)
):
    return db.query(Student).all()