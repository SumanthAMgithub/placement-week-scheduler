from backend.services.conflict_detector import check_all_conflicts
from backend.services.eligibility import can_student_be_scheduled
from backend.database.models import Interview


def schedule_student(
    db,
    student,
    company,
    rooms,
    panels,
    time_slots,
    scheduled_interviews
):
    """
    Try to schedule one student for one company.

    Returns a dictionary containing:
    - interview: Interview object if successful, otherwise None
    - reason: Failure reason if scheduling fails
    """

    # 1. Check eligibility
    if not can_student_be_scheduled(student, company):
        return {
            "interview": None,
            "reason": "Student is not eligible for this company"
        }

    # 2. Get panels belonging to this company
    company_panels = [
        panel
        for panel in panels
        if panel.company_id == company.id
        and panel.status == "available"
    ]

    if not company_panels:
        return {
            "interview": None,
            "reason": "No available panel for this company"
        }

    # Track why scheduling failed
    conflict_reasons = {
        "student_conflict": 0,
        "room_conflict": 0,
        "panel_conflict": 0
    }

    # 3. Try every time slot
    for slot in time_slots:

        # 4. Try every room
        for room in rooms:

            if room.status != "available":
                continue

            # 5. Try every company panel
            for panel in company_panels:

                conflicts = check_all_conflicts(
                    student_id=student.id,
                    room_id=room.id,
                    panel_id=panel.id,
                    start_time=slot.start_datetime,
                    end_time=slot.end_datetime,
                    scheduled_interviews=scheduled_interviews
                )

                # No conflict → schedule it
                if not conflicts["has_conflict"]:

                    interview = Interview(
                        student_id=student.id,
                        company_id=company.id,
                        room_id=room.id,
                        panel_id=panel.id,
                        time_slot_id=slot.id,
                        status="scheduled"
                    )

                    db.add(interview)
                    db.commit()
                    db.refresh(interview)

                    scheduled_interviews.append(
                        {
                            "student_id": student.id,
                            "room_id": room.id,
                            "panel_id": panel.id,
                            "start_time": slot.start_datetime,
                            "end_time": slot.end_datetime
                        }
                    )

                    return {
                        "interview": interview,
                        "reason": None
                    }

                # Record conflict reasons
                if conflicts["student_conflict"]:
                    conflict_reasons["student_conflict"] += 1

                if conflicts["room_conflict"]:
                    conflict_reasons["room_conflict"] += 1

                if conflicts["panel_conflict"]:
                    conflict_reasons["panel_conflict"] += 1

    # 6. Determine the main reason for failure
    if conflict_reasons["student_conflict"] > 0:
        reason = "Student has conflicts in available time slots"

    elif conflict_reasons["panel_conflict"] > 0:
        reason = "Company panels are unavailable in available time slots"

    elif conflict_reasons["room_conflict"] > 0:
        reason = "Rooms are unavailable in available time slots"

    else:
        reason = "No suitable time slot available"

    return {
        "interview": None,
        "reason": reason
    }


def schedule_week(
    db,
    students,
    companies,
    rooms,
    panels,
    time_slots
):
    """
    Generate a placement schedule for all students
    and their shortlisted companies.
    """

    scheduled_interviews = []
    unscheduled = []

    failure_summary = {
        "student_conflict": 0,
        "panel_conflict": 0,
        "room_conflict": 0,
        "no_available_panel": 0,
        "not_eligible": 0,
        "no_time_slot": 0
    }

    # 1. Schedule higher-priority companies first
    sorted_companies = sorted(
        companies,
        key=lambda company: company.priority_tier
    )

    # 2. Process companies according to priority
    for company in sorted_companies:

        # 3. Find students shortlisted for this company
        shortlisted_students = [
            student
            for student in students
            if company in student.companies
        ]
        # Prioritize students with more shortlisted companies.
        # Students with more interviews are harder to schedule.
        shortlisted_students.sort(
            key=lambda student: len(student.companies),
            reverse=True
        )

        # 4. Schedule each student
        for student in shortlisted_students:

            result = schedule_student(
                db=db,
                student=student,
                company=company,
                rooms=rooms,
                panels=panels,
                time_slots=time_slots,
                scheduled_interviews=scheduled_interviews
            )

            # 5. Handle failed scheduling
            if result["interview"] is None:

                reason = result["reason"]

                unscheduled.append(
                    {
                        "student_id": student.id,
                        "company_id": company.id,
                        "reason": reason
                    }
                )

                # 6. Count failure reasons
                if "Student has conflicts" in reason:
                    failure_summary["student_conflict"] += 1

                elif "Company panels" in reason:
                    failure_summary["panel_conflict"] += 1

                elif "Rooms" in reason:
                    failure_summary["room_conflict"] += 1

                elif "No available panel" in reason:
                    failure_summary["no_available_panel"] += 1

                elif "not eligible" in reason.lower():
                    failure_summary["not_eligible"] += 1

                else:
                    failure_summary["no_time_slot"] += 1

    # 7. Return complete scheduling result
    return {
        "scheduled": scheduled_interviews,
        "unscheduled": unscheduled,
        "failure_summary": failure_summary
    }