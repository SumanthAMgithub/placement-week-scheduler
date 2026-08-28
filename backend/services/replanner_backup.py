from backend.database.models import (
    Interview,
    TimeSlot,
    Room,
    Panel
)

from backend.services.conflict_detector import check_all_conflicts


def build_scheduled_interviews(db, exclude_interview_id=None):
    """
    Build a list of currently scheduled interviews.

    This is used by the conflict detector when searching
    for replacement slots.
    """

    query = db.query(Interview).filter(
        Interview.status == "scheduled"
    )

    if exclude_interview_id is not None:
        query = query.filter(
            Interview.id != exclude_interview_id
        )

    interviews = query.all()

    scheduled = []

    for interview in interviews:

        slot = db.query(TimeSlot).filter(
            TimeSlot.id == interview.time_slot_id
        ).first()

        if not slot:
            continue

        scheduled.append(
            {
                "interview_id": interview.id,
                "student_id": interview.student_id,
                "room_id": interview.room_id,
                "panel_id": interview.panel_id,
                "start_time": slot.start_datetime,
                "end_time": slot.end_datetime
            }
        )

    return scheduled


def replan_company_delay(
    db,
    company_id,
    delay_hours
):
    """
    Replan a company's interviews when the company
    arrives late.

    The existing schedule is disturbed as little as possible.

    Only interviews that occur before the new company
    arrival time are considered for movement.
    """

    # --------------------------------------------------
    # 1. Get all scheduled interviews for this company
    # --------------------------------------------------

    company_interviews = db.query(Interview).filter(
        Interview.company_id == company_id,
        Interview.status == "scheduled"
    ).order_by(
        Interview.time_slot_id
    ).all()

    if not company_interviews:

        return {
            "message": "No scheduled interviews found for this company",
            "affected_interviews": 0,
            "moved_interviews": 0,
            "unchanged_interviews": 0,
            "cancelled_interviews": 0,
            "changes": []
        }

    # --------------------------------------------------
    # 2. Find the company's original first interview
    # --------------------------------------------------

    first_interview = company_interviews[0]

    first_slot = db.query(TimeSlot).filter(
        TimeSlot.id == first_interview.time_slot_id
    ).first()

    if not first_slot:

        return {
            "message": "Unable to determine company's original schedule",
            "affected_interviews": 0,
            "moved_interviews": 0,
            "unchanged_interviews": 0,
            "cancelled_interviews": 0,
            "changes": []
        }

    # Company arrival time after delay
    company_arrival_time = (
        first_slot.start_datetime
        + __import__("datetime").timedelta(
            hours=delay_hours
        )
    )

    # --------------------------------------------------
    # 3. Get available rooms, panels and time slots
    # --------------------------------------------------

    rooms = db.query(Room).filter(
        Room.status == "available"
    ).all()

    panels = db.query(Panel).filter(
        Panel.company_id == company_id,
        Panel.status == "available"
    ).all()

    time_slots = db.query(TimeSlot).order_by(
        TimeSlot.id
    ).all()

    # --------------------------------------------------
    # 4. Build current schedule
    # --------------------------------------------------

    scheduled_interviews = build_scheduled_interviews(db)

    changes = []

    moved_count = 0
    unchanged_count = 0
    cancelled_count = 0

    # --------------------------------------------------
    # 5. Process company interviews
    # --------------------------------------------------

    for interview in company_interviews:

        old_slot = db.query(TimeSlot).filter(
            TimeSlot.id == interview.time_slot_id
        ).first()

        if not old_slot:
            continue

        old_start = old_slot.start_datetime
        old_end = old_slot.end_datetime

        # --------------------------------------------------
        # Interview is already after company arrival.
        # Keep it unchanged.
        # --------------------------------------------------

        if old_start >= company_arrival_time:

            unchanged_count += 1

            changes.append(
                {
                    "interview_id": interview.id,
                    "student_id": interview.student_id,
                    "change": "unchanged",
                    "old_time_slot_id": old_slot.id,
                    "new_time_slot_id": old_slot.id,
                    "reason": "Interview already starts after company arrival"
                }
            )

            continue

        # --------------------------------------------------
        # Interview is affected by the delay.
        # Search for a replacement.
        # --------------------------------------------------

        new_slot = None
        new_room = None
        new_panel = None

        for slot in time_slots:

            # New interview must start after company arrival
            if slot.start_datetime < company_arrival_time:
                continue

            for room in rooms:

                for panel in panels:

                    conflicts = check_all_conflicts(
                        student_id=interview.student_id,
                        room_id=room.id,
                        panel_id=panel.id,
                        start_time=slot.start_datetime,
                        end_time=slot.end_datetime,
                        scheduled_interviews=scheduled_interviews
                    )

                    if conflicts["has_conflict"]:
                        continue

                    new_slot = slot
                    new_room = room
                    new_panel = panel

                    break

                if new_slot:
                    break

            if new_slot:
                break

        # --------------------------------------------------
        # No replacement found
        # --------------------------------------------------

        if not new_slot:

            interview.status = "cancelled"

            interview.reason = (
                f"Company delayed by {delay_hours} hours; "
                "no replacement slot available"
            )

            cancelled_count += 1

            changes.append(
                {
                    "interview_id": interview.id,
                    "student_id": interview.student_id,
                    "change": "cancelled",
                    "old_time_slot_id": old_slot.id,
                    "new_time_slot_id": None,
                    "reason": interview.reason
                }
            )

            continue

        # --------------------------------------------------
        # Save old values
        # --------------------------------------------------

        old_slot_id = interview.time_slot_id
        old_room_id = interview.room_id
        old_panel_id = interview.panel_id

        # --------------------------------------------------
        # Move interview
        # --------------------------------------------------

        interview.time_slot_id = new_slot.id
        interview.room_id = new_room.id
        interview.panel_id = new_panel.id
        interview.status = "scheduled"

        interview.reason = (
            f"Moved because company was delayed "
            f"by {delay_hours} hours"
        )

        moved_count += 1

        changes.append(
            {
                "interview_id": interview.id,
                "student_id": interview.student_id,

                "change": "moved",

                "old_time_slot_id": old_slot_id,
                "new_time_slot_id": new_slot.id,

                "old_room_id": old_room_id,
                "new_room_id": new_room.id,

                "old_panel_id": old_panel_id,
                "new_panel_id": new_panel.id,

                "reason": (
                    f"Company delayed by "
                    f"{delay_hours} hours"
                )
            }
        )

        # --------------------------------------------------
        # Add new position to conflict list
        # --------------------------------------------------

        scheduled_interviews.append(
            {
                "interview_id": interview.id,
                "student_id": interview.student_id,
                "room_id": new_room.id,
                "panel_id": new_panel.id,
                "start_time": new_slot.start_datetime,
                "end_time": new_slot.end_datetime
            }
        )

    # --------------------------------------------------
    # 6. Save all changes
    # --------------------------------------------------

    db.commit()

    # --------------------------------------------------
    # 7. Return replan summary
    # --------------------------------------------------

    return {
        "message": "Company delay replan completed",

        "company_id": company_id,

        "delay_hours": delay_hours,

        "company_arrival_time": company_arrival_time.strftime(
            "%Y-%m-%d %H:%M"
        ),

        "affected_interviews": (
            moved_count + cancelled_count
        ),

        "moved_interviews": moved_count,

        "unchanged_interviews": unchanged_count,

        "cancelled_interviews": cancelled_count,

        "changes": changes
    }