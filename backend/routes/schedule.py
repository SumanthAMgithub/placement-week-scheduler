from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.services.conflict_detector import check_all_conflicts
from backend.database.database import get_db
from backend.database.models import (
    Student,
    Company,
    Room,
    Panel,
    TimeSlot,
    Interview
)

from backend.services.scheduler import schedule_week


router = APIRouter(
    prefix="/schedule",
    tags=["Schedule"]
)


# ---------------------------------------------------------
# GENERATE SCHEDULE
# ---------------------------------------------------------

@router.post("/generate")
def generate_schedule(
    db: Session = Depends(get_db)
):
    """
    Generate the complete placement schedule.
    """

    students = db.query(Student).all()
    companies = db.query(Company).all()
    rooms = db.query(Room).all()
    panels = db.query(Panel).all()
    time_slots = db.query(TimeSlot).all()

    result = schedule_week(
        db=db,
        students=students,
        companies=companies,
        rooms=rooms,
        panels=panels,
        time_slots=time_slots
    )

    return {
        "message": "Placement schedule generated successfully",
        "scheduled_count": len(result["scheduled"]),
        "unscheduled_count": len(result["unscheduled"]),
        "failure_summary": result["failure_summary"],
        "unscheduled": result["unscheduled"]
    }


# ---------------------------------------------------------
# RESET SCHEDULE
# ---------------------------------------------------------

@router.post("/reset")
def reset_schedule(
    db: Session = Depends(get_db)
):
    """
    Delete all generated interviews from the current schedule.
    """

    deleted_count = db.query(Interview).delete(
        synchronize_session=False
    )

    db.commit()

    return {
        "message": "Schedule reset successfully",
        "deleted_interviews": deleted_count
    }
# ---------------------------------------------------------
# RESCHEDULE INTERVIEW
# ---------------------------------------------------------

@router.post("/reschedule/{interview_id}")
def reschedule_interview(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Find a new conflict-free time slot, room, and panel
    for an existing interview.
    """

    # 1. Find the interview
    interview = db.query(Interview).filter(
        Interview.id == interview_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )

    # 2. Get the student and company
    student = db.query(Student).filter(
        Student.id == interview.student_id
    ).first()

    company = db.query(Company).filter(
        Company.id == interview.company_id
    ).first()

    if not student or not company:
        raise HTTPException(
            status_code=404,
            detail="Student or company not found"
        )

    # 3. Get all available rooms
    rooms = db.query(Room).filter(
        Room.status == "available"
    ).all()

    # 4. Get panels belonging to this company
    panels = db.query(Panel).filter(
        Panel.company_id == company.id,
        Panel.status == "available"
    ).all()

    # 5. Get all time slots
    time_slots = db.query(TimeSlot).all()

    if not rooms:
        raise HTTPException(
            status_code=400,
            detail="No available rooms"
        )

    if not panels:
        raise HTTPException(
            status_code=400,
            detail="No available panels for this company"
        )

    if not time_slots:
        raise HTTPException(
            status_code=400,
            detail="No time slots available"
        )

    # 6. Get other scheduled interviews
    other_interviews = db.query(Interview).filter(
        Interview.status == "scheduled",
        Interview.id != interview.id
    ).all()

    scheduled_interviews = []

    for existing in other_interviews:

        existing_slot = db.query(TimeSlot).filter(
            TimeSlot.id == existing.time_slot_id
        ).first()

        if not existing_slot:
            continue

        scheduled_interviews.append(
            {
                "student_id": existing.student_id,
                "room_id": existing.room_id,
                "panel_id": existing.panel_id,
                "start_time": existing_slot.start_datetime,
                "end_time": existing_slot.end_datetime
            }
        )

    # 7. Search for a new conflict-free combination
    for slot in time_slots:

        for room in rooms:

            for panel in panels:

                conflicts = check_all_conflicts(
                    student_id=student.id,
                    room_id=room.id,
                    panel_id=panel.id,
                    start_time=slot.start_datetime,
                    end_time=slot.end_datetime,
                    scheduled_interviews=scheduled_interviews
                )

                if conflicts["has_conflict"]:
                    continue

                # 8. Update the interview
                interview.room_id = room.id
                interview.panel_id = panel.id
                interview.time_slot_id = slot.id
                interview.status = "scheduled"

                db.commit()
                db.refresh(interview)

                return {
                    "message": "Interview rescheduled successfully",
                    "interview_id": interview.id,
                    "student_id": interview.student_id,
                    "company_id": interview.company_id,
                    "room_id": room.id,
                    "panel_id": panel.id,
                    "time_slot_id": slot.id,
                    "day": slot.day,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time
                }

    # 9. No valid combination found
    raise HTTPException(
        status_code=409,
        detail="No conflict-free slot available for rescheduling"
    )


# ---------------------------------------------------------
# VIEW SCHEDULE
# ---------------------------------------------------------

@router.get("/")
def get_schedule(
    student_id: int | None = None,
    company_id: int | None = None,
    day: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Return scheduled interviews.

    Optional filters:
    - student_id
    - company_id
    - day
    """

    query = db.query(Interview).filter(
        Interview.status == "scheduled"
    )

    # Filter by student
    if student_id is not None:
        query = query.filter(
            Interview.student_id == student_id
        )

    # Filter by company
    if company_id is not None:
        query = query.filter(
            Interview.company_id == company_id
        )

    # Get interviews
    interviews = query.all()

    schedule = []

    for interview in interviews:

        student = db.query(Student).filter(
            Student.id == interview.student_id
        ).first()

        company = db.query(Company).filter(
            Company.id == interview.company_id
        ).first()

        room = db.query(Room).filter(
            Room.id == interview.room_id
        ).first()

        panel = db.query(Panel).filter(
            Panel.id == interview.panel_id
        ).first()

        time_slot = db.query(TimeSlot).filter(
            TimeSlot.id == interview.time_slot_id
        ).first()

        # Apply day filter
        if day is not None:

            if not time_slot or time_slot.day != day:
                continue

        schedule.append(
            {
                "interview_id": interview.id,

                "student_id": interview.student_id,

                "student": student.name
                if student else None,

                "company_id": interview.company_id,

                "company": company.name
                if company else None,

                "room_id": interview.room_id,

                "room": room.name
                if room else None,

                "panel_id": interview.panel_id,

                "panel": panel.name
                if panel else None,

                "day": time_slot.day
                if time_slot else None,

                "start_time": time_slot.start_time
                if time_slot else None,

                "end_time": time_slot.end_time
                if time_slot else None,

                "status": interview.status
            }
        )

    return {
        "total_interviews": len(schedule),
        "schedule": schedule
    }


# ---------------------------------------------------------
# SCHEDULE METRICS
# ---------------------------------------------------------

@router.get("/metrics")
def get_schedule_metrics(
    db: Session = Depends(get_db)
):
    """
    Return summary metrics for the placement schedule.
    """

    # Total number of students
    total_students = db.query(Student).count()

    # Total scheduled interviews
    scheduled_interviews = db.query(Interview).filter(
        Interview.status == "scheduled"
    ).count()

    # Total unscheduled interviews
    # Based on the number of shortlisted student-company combinations
    total_shortlisted = 0

    students = db.query(Student).all()

    for student in students:
        total_shortlisted += len(student.companies)

    unscheduled_interviews = max(
        total_shortlisted - scheduled_interviews,
        0
    )

    # Unique rooms currently being used
    rooms_used = db.query(Interview.room_id).filter(
        Interview.status == "scheduled",
        Interview.room_id.isnot(None)
    ).distinct().count()

    # Unique panels currently being used
    panels_used = db.query(Interview.panel_id).filter(
        Interview.status == "scheduled",
        Interview.panel_id.isnot(None)
    ).distinct().count()

    # Scheduling rate
    if total_shortlisted > 0:
        scheduling_rate = round(
            (scheduled_interviews / total_shortlisted) * 100,
            2
        )
    else:
        scheduling_rate = 0

    return {
        "total_students": total_students,
        "total_shortlisted_interviews": total_shortlisted,
        "scheduled_interviews": scheduled_interviews,
        "unscheduled_interviews": unscheduled_interviews,
        "rooms_used": rooms_used,
        "panels_used": panels_used,
        "scheduling_rate_percent": scheduling_rate
    }