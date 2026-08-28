from datetime import datetime, timedelta

from backend.database.models import (
    Interview,
    TimeSlot,
    Room,
    Panel
)

from backend.services.conflict_detector import (
    check_all_conflicts
)


# ============================================================
# HELPER
# ============================================================

def datetime_min():
    """
    Return minimum datetime.

    Used when a TimeSlot cannot be found.
    """
    return datetime.min


# ============================================================
# GET SLOT
# ============================================================

def get_time_slot(db, slot_id):
    """
    Get a TimeSlot by ID.
    """

    if slot_id is None:
        return None

    return db.query(TimeSlot).filter(
        TimeSlot.id == slot_id
    ).first()


# ============================================================
# BUILD CURRENT SCHEDULE
# ============================================================

def build_scheduled_interviews(
    db,
    exclude_interview_id=None
):
    """
    Build a conflict-detection list from currently
    scheduled interviews.

    Cancelled interviews are ignored.

    One interview can optionally be excluded.
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

        slot = get_time_slot(
            db,
            interview.time_slot_id
        )

        if not slot:
            continue

        # Ignore incomplete assignments
        if (
            interview.room_id is None
            or interview.panel_id is None
        ):
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


# ============================================================
# REMOVE INTERVIEWS FROM CONFLICT LIST
# ============================================================

def remove_interviews_from_schedule(
    scheduled_interviews,
    interview_ids
):
    """
    Remove interviews that are currently being replanned.

    This is important because their OLD positions should not
    block their NEW positions.
    """

    interview_ids = set(interview_ids)

    return [
        interview
        for interview in scheduled_interviews
        if interview.get("interview_id") not in interview_ids
    ]


# ============================================================
# ADD INTERVIEW TO CONFLICT LIST
# ============================================================

def add_interview_to_schedule(
    scheduled_interviews,
    interview
):
    """
    Add a newly assigned interview to the temporary
    conflict-detection schedule.
    """

    slot = interview.time_slot

    if not slot:
        return

    scheduled_interviews.append(
        {
            "interview_id": interview.id,

            "student_id": interview.student_id,

            "room_id": interview.room_id,

            "panel_id": interview.panel_id,

            "start_time": slot.start_datetime,

            "end_time": slot.end_datetime
        }
    )


# ============================================================
# ORDER ROOMS
# ============================================================

def get_ordered_rooms(
    db,
    rooms,
    original_room_id
):
    """
    Prefer the interview's original room.

    Then try other available rooms.
    """

    ordered_rooms = []

    original_room = None

    if original_room_id is not None:

        original_room = db.query(Room).filter(
            Room.id == original_room_id
        ).first()

    if (
        original_room
        and original_room.status == "available"
    ):

        ordered_rooms.append(original_room)

    for room in rooms:

        if room.id == original_room_id:
            continue

        if room.status != "available":
            continue

        ordered_rooms.append(room)

    return ordered_rooms


# ============================================================
# ORDER PANELS
# ============================================================

def get_ordered_panels(
    db,
    panels,
    original_panel_id
):
    """
    Prefer the interview's original panel.

    Then try other available panels.
    """

    ordered_panels = []

    original_panel = None

    if original_panel_id is not None:

        original_panel = db.query(Panel).filter(
            Panel.id == original_panel_id
        ).first()

    if (
        original_panel
        and original_panel.status == "available"
    ):

        ordered_panels.append(original_panel)

    for panel in panels:

        if panel.id == original_panel_id:
            continue

        if panel.status != "available":
            continue

        ordered_panels.append(panel)

    return ordered_panels


# ============================================================
# FIND REPLACEMENT
# ============================================================

def find_replacement(
    db,
    interview,
    company_arrival_time,
    rooms,
    panels,
    time_slots,
    scheduled_interviews
):
    """
    Find the earliest conflict-free replacement.

    Priority:

        1. Slot after company arrival
        2. Earliest slot
        3. Original room first
        4. Original panel first
        5. No student conflict
        6. No room conflict
        7. No panel conflict
    """

    ordered_rooms = get_ordered_rooms(
        db=db,
        rooms=rooms,
        original_room_id=interview.room_id
    )

    ordered_panels = get_ordered_panels(
        db=db,
        panels=panels,
        original_panel_id=interview.panel_id
    )

    sorted_slots = sorted(
        time_slots,
        key=lambda slot: slot.start_datetime
    )

    for slot in sorted_slots:

        # ----------------------------------------------------
        # Interview must start at or after company arrival
        # ----------------------------------------------------

        if slot.start_datetime < company_arrival_time:
            continue

        # ----------------------------------------------------
        # Try rooms
        # ----------------------------------------------------

        for room in ordered_rooms:

            # ------------------------------------------------
            # Try panels
            # ------------------------------------------------

            for panel in ordered_panels:

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

                return {
                    "slot": slot,
                    "room": room,
                    "panel": panel
                }

    return None


# ============================================================
# COMPANY DELAY REPLAN
# ============================================================

def replan_company_delay(
    db,
    company_id,
    delay_hours
):
    """
    Replan a company's interviews after a company delay.

    Behavior:

        - Reject negative delay.
        - Find company's scheduled interviews.
        - Calculate new company arrival time.
        - Interviews already after arrival remain unchanged.
        - Affected interviews are temporarily removed from
          conflict detection.
        - Affected interviews are reassigned sequentially.
        - Every successful replacement is immediately added
          back to conflict detection.
        - Student, room and panel conflicts are checked.
        - If no valid replacement exists, interview is cancelled.
    """

    # ========================================================
    # 1. VALIDATE DELAY
    # ========================================================

    if delay_hours < 0:

        return {
            "message": "Delay hours cannot be negative",

            "company_id": company_id,

            "delay_hours": delay_hours,

            "affected_interviews": 0,

            "moved_interviews": 0,

            "unchanged_interviews": 0,

            "cancelled_interviews": 0,

            "replan_churn_percent": 0,

            "changes": []
        }

    # ========================================================
    # 2. GET COMPANY INTERVIEWS
    # ========================================================

    company_interviews = db.query(
        Interview
    ).filter(
        Interview.company_id == company_id,
        Interview.status == "scheduled"
    ).all()

    # ========================================================
    # NO INTERVIEWS
    # ========================================================

    if not company_interviews:

        return {
            "message": (
                "No scheduled interviews found "
                "for this company"
            ),

            "company_id": company_id,

            "delay_hours": delay_hours,

            "affected_interviews": 0,

            "moved_interviews": 0,

            "unchanged_interviews": 0,

            "cancelled_interviews": 0,

            "replan_churn_percent": 0,

            "changes": []
        }

    # ========================================================
    # 3. SORT COMPANY INTERVIEWS
    # ========================================================

    def interview_start(interview):

        slot = get_time_slot(
            db,
            interview.time_slot_id
        )

        if not slot:
            return datetime_min()

        return slot.start_datetime

    company_interviews.sort(
        key=interview_start
    )

    # ========================================================
    # 4. FIND ORIGINAL COMPANY START
    # ========================================================

    first_interview = company_interviews[0]

    first_slot = get_time_slot(
        db,
        first_interview.time_slot_id
    )

    if not first_slot:

        return {
            "message": (
                "Unable to determine company's "
                "original schedule"
            ),

            "company_id": company_id,

            "delay_hours": delay_hours,

            "affected_interviews": 0,

            "moved_interviews": 0,

            "unchanged_interviews": 0,

            "cancelled_interviews": 0,

            "replan_churn_percent": 0,

            "changes": []
        }

    # ========================================================
    # 5. NEW COMPANY ARRIVAL
    # ========================================================

    company_arrival_time = (
        first_slot.start_datetime
        + timedelta(hours=delay_hours)
    )

    # ========================================================
    # 6. GET RESOURCES
    # ========================================================

    rooms = db.query(Room).filter(
        Room.status == "available"
    ).all()

    panels = db.query(Panel).filter(
        Panel.company_id == company_id,
        Panel.status == "available"
    ).all()

    time_slots = db.query(TimeSlot).all()

    time_slots.sort(
        key=lambda slot: slot.start_datetime
    )

    # ========================================================
    # 7. BUILD CURRENT SCHEDULE
    # ========================================================

    scheduled_interviews = build_scheduled_interviews(
        db
    )

    # ========================================================
    # 8. IDENTIFY AFFECTED INTERVIEWS
    # ========================================================

    affected = []

    unaffected = []

    for interview in company_interviews:

        slot = get_time_slot(
            db,
            interview.time_slot_id
        )

        if not slot:
            continue

        if slot.start_datetime < company_arrival_time:

            affected.append(interview)

        else:

            unaffected.append(interview)

    # ========================================================
    # IMPORTANT FIX
    #
    # Remove ALL affected interviews from their old
    # positions before searching for replacements.
    # ========================================================

    affected_ids = [
        interview.id
        for interview in affected
    ]

    scheduled_interviews = (
        remove_interviews_from_schedule(
            scheduled_interviews,
            affected_ids
        )
    )

    # ========================================================
    # 9. COUNTERS
    # ========================================================

    changes = []

    moved_count = 0

    unchanged_count = len(unaffected)

    cancelled_count = 0

    # ========================================================
    # 10. RECORD UNCHANGED INTERVIEWS
    # ========================================================

    for interview in unaffected:

        old_slot = get_time_slot(
            db,
            interview.time_slot_id
        )

        if not old_slot:
            continue

        changes.append(
            {
                "interview_id": interview.id,

                "student_id": interview.student_id,

                "change": "unchanged",

                "old_time_slot_id": interview.time_slot_id,

                "new_time_slot_id": interview.time_slot_id,

                "old_room_id": interview.room_id,

                "new_room_id": interview.room_id,

                "old_panel_id": interview.panel_id,

                "new_panel_id": interview.panel_id,

                "reason": (
                    "Interview already starts after "
                    "company arrival"
                )
            }
        )

    # ========================================================
    # 11. PROCESS AFFECTED INTERVIEWS
    # ========================================================

    for interview in affected:

        old_slot = get_time_slot(
            db,
            interview.time_slot_id
        )

        if not old_slot:
            continue

        old_slot_id = interview.time_slot_id

        old_room_id = interview.room_id

        old_panel_id = interview.panel_id

        # ====================================================
        # FIND REPLACEMENT
        # ====================================================

        replacement = find_replacement(
            db=db,

            interview=interview,

            company_arrival_time=company_arrival_time,

            rooms=rooms,

            panels=panels,

            time_slots=time_slots,

            scheduled_interviews=scheduled_interviews
        )

        # ====================================================
        # NO REPLACEMENT
        # ====================================================

        if replacement is None:

            interview.status = "cancelled"

            interview.room_id = None

            interview.panel_id = None

            interview.time_slot_id = None

            interview.reason = (
                f"Company delayed by {delay_hours} hours; "
                "no conflict-free replacement slot available"
            )

            cancelled_count += 1

            changes.append(
                {
                    "interview_id": interview.id,

                    "student_id": interview.student_id,

                    "change": "cancelled",

                    "old_time_slot_id": old_slot_id,

                    "new_time_slot_id": None,

                    "old_room_id": old_room_id,

                    "new_room_id": None,

                    "old_panel_id": old_panel_id,

                    "new_panel_id": None,

                    "reason": interview.reason
                }
            )

            continue

        # ====================================================
        # REPLACEMENT FOUND
        # ====================================================

        new_slot = replacement["slot"]

        new_room = replacement["room"]

        new_panel = replacement["panel"]

        # ====================================================
        # UPDATE DATABASE OBJECT
        # ====================================================

        interview.time_slot_id = new_slot.id

        interview.room_id = new_room.id

        interview.panel_id = new_panel.id

        interview.status = "scheduled"

        interview.reason = (
            f"Moved because company was delayed "
            f"by {delay_hours} hours"
        )

        # ====================================================
        # DETERMINE CHANGE TYPE
        # ====================================================

        if (
            old_slot_id == new_slot.id
            and old_room_id == new_room.id
            and old_panel_id == new_panel.id
        ):

            change_type = "unchanged"

            unchanged_count += 1

        else:

            change_type = "moved"

            moved_count += 1

        # ====================================================
        # RECORD CHANGE
        # ====================================================

        changes.append(
            {
                "interview_id": interview.id,

                "student_id": interview.student_id,

                "change": change_type,

                "old_time_slot_id": old_slot_id,

                "new_time_slot_id": new_slot.id,

                "old_room_id": old_room_id,

                "new_room_id": new_room.id,

                "old_panel_id": old_panel_id,

                "new_panel_id": new_panel.id,

                "old_day": old_slot.day,

                "new_day": new_slot.day,

                "old_start_time": old_slot.start_time,

                "new_start_time": new_slot.start_time,

                "old_end_time": old_slot.end_time,

                "new_end_time": new_slot.end_time,

                "reason": (
                    f"Company delayed by "
                    f"{delay_hours} hours"
                )
            }
        )

        # ====================================================
        # IMPORTANT:
        #
        # Add the NEW position to conflict detection.
        # ====================================================

        add_interview_to_schedule(
            scheduled_interviews,
            interview
        )

        db.flush()

    # ========================================================
    # 12. COMMIT
    # ========================================================

    db.commit()

    # ========================================================
    # 13. CHURN
    # ========================================================

    total_interviews = len(company_interviews)

    affected_interviews = (
        moved_count + cancelled_count
    )

    if total_interviews > 0:

        replan_churn_percent = round(
            (
                affected_interviews
                / total_interviews
            ) * 100,
            2
        )

    else:

        replan_churn_percent = 0

    # ========================================================
    # 14. RETURN
    # ========================================================

    return {
        "message": "Company delay replan completed",

        "company_id": company_id,

        "delay_hours": delay_hours,

        "company_arrival_time": (
            company_arrival_time.strftime(
                "%Y-%m-%d %H:%M"
            )
        ),

        "affected_interviews": affected_interviews,

        "moved_interviews": moved_count,

        "unchanged_interviews": unchanged_count,

        "cancelled_interviews": cancelled_count,

        "replan_churn_percent": replan_churn_percent,

        "changes": changes
    }


# ============================================================
# PANEL DROP REPLAN
# ============================================================

def replan_panel_drop(
    db,
    panel_id
):
    """
    Replan interviews when a panel becomes unavailable.

    Strategy:

        1. Find panel.
        2. Find affected interviews.
        3. Mark panel unavailable.
        4. Find other available panels of same company.
        5. Try same slot + same room first.
        6. Otherwise find another slot + room + panel.
        7. Cancel only if no valid replacement exists.
    """

    # ========================================================
    # 1. FIND PANEL
    # ========================================================

    dropped_panel = db.query(Panel).filter(
        Panel.id == panel_id
    ).first()

    if not dropped_panel:

        return {
            "message": "Panel not found",

            "panel_id": panel_id,

            "affected_interviews": 0,

            "moved_interviews": 0,

            "unchanged_interviews": 0,

            "cancelled_interviews": 0,

            "replan_churn_percent": 0,

            "changes": []
        }

    company_id = dropped_panel.company_id

    # ========================================================
    # 2. FIND AFFECTED INTERVIEWS
    # ========================================================

    affected_interviews = db.query(
        Interview
    ).filter(
        Interview.panel_id == panel_id,
        Interview.status == "scheduled"
    ).all()

    affected_interviews.sort(
        key=lambda interview: (
            get_time_slot(
                db,
                interview.time_slot_id
            ).start_datetime
            if get_time_slot(
                db,
                interview.time_slot_id
            )
            else datetime_min()
        )
    )

    # ========================================================
    # 3. NO AFFECTED INTERVIEWS
    # ========================================================

    if not affected_interviews:

        dropped_panel.status = "unavailable"

        db.commit()

        return {
            "message": (
                "Panel marked unavailable; "
                "no scheduled interviews affected"
            ),

            "panel_id": panel_id,

            "company_id": company_id,

            "affected_interviews": 0,

            "moved_interviews": 0,

            "unchanged_interviews": 0,

            "cancelled_interviews": 0,

            "replan_churn_percent": 0,

            "changes": []
        }

    # ========================================================
    # 4. MARK PANEL UNAVAILABLE
    # ========================================================

    dropped_panel.status = "unavailable"

    # ========================================================
    # 5. OTHER PANELS
    # ========================================================

    available_panels = db.query(
        Panel
    ).filter(
        Panel.company_id == company_id,
        Panel.status == "available",
        Panel.id != panel_id
    ).all()

    # ========================================================
    # 6. ROOMS
    # ========================================================

    rooms = db.query(Room).filter(
        Room.status == "available"
    ).all()

    # ========================================================
    # 7. TIME SLOTS
    # ========================================================

    time_slots = db.query(TimeSlot).all()

    time_slots.sort(
        key=lambda slot: slot.start_datetime
    )

    # ========================================================
    # 8. BUILD CURRENT SCHEDULE
    # ========================================================

    scheduled_interviews = build_scheduled_interviews(
        db
    )

    # ========================================================
    # REMOVE ALL AFFECTED INTERVIEWS
    # ========================================================

    affected_ids = [
        interview.id
        for interview in affected_interviews
    ]

    scheduled_interviews = (
        remove_interviews_from_schedule(
            scheduled_interviews,
            affected_ids
        )
    )

    # ========================================================
    # 9. COUNTERS
    # ========================================================

    changes = []

    moved_count = 0

    unchanged_count = 0

    cancelled_count = 0

    # ========================================================
    # 10. PROCESS
    # ========================================================

    for interview in affected_interviews:

        old_slot = get_time_slot(
            db,
            interview.time_slot_id
        )

        if not old_slot:
            continue

        old_slot_id = interview.time_slot_id

        old_room_id = interview.room_id

        old_panel_id = interview.panel_id

        new_slot = None

        new_room = None

        new_panel = None

        # ====================================================
        # FIRST:
        # SAME SLOT + SAME ROOM + OTHER PANEL
        # ====================================================

        original_room = None

        if old_room_id is not None:

            original_room = db.query(Room).filter(
                Room.id == old_room_id
            ).first()

        if original_room:

            for panel in available_panels:

                conflicts = check_all_conflicts(
                    student_id=interview.student_id,

                    room_id=original_room.id,

                    panel_id=panel.id,

                    start_time=old_slot.start_datetime,

                    end_time=old_slot.end_datetime,

                    scheduled_interviews=scheduled_interviews
                )

                if conflicts["has_conflict"]:
                    continue

                new_slot = old_slot

                new_room = original_room

                new_panel = panel

                break

        # ====================================================
        # SECOND:
        # ANY VALID SLOT + ROOM + PANEL
        # ====================================================

        if new_slot is None:

            for slot in time_slots:

                for room in rooms:

                    for panel in available_panels:

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

        # ====================================================
        # NO REPLACEMENT
        # ====================================================

        if new_slot is None:

            interview.status = "cancelled"

            interview.room_id = None

            interview.panel_id = None

            interview.time_slot_id = None

            interview.reason = (
                "Panel dropped out; "
                "no conflict-free replacement "
                "panel/slot available"
            )

            cancelled_count += 1

            changes.append(
                {
                    "interview_id": interview.id,

                    "student_id": interview.student_id,

                    "change": "cancelled",

                    "old_time_slot_id": old_slot_id,

                    "new_time_slot_id": None,

                    "old_room_id": old_room_id,

                    "new_room_id": None,

                    "old_panel_id": old_panel_id,

                    "new_panel_id": None,

                    "reason": interview.reason
                }
            )

            continue

        # ====================================================
        # UPDATE
        # ====================================================

        interview.time_slot_id = new_slot.id

        interview.room_id = new_room.id

        interview.panel_id = new_panel.id

        interview.status = "scheduled"

        interview.reason = (
            f"Panel {panel_id} dropped out"
        )

        # ====================================================
        # CHANGE TYPE
        # ====================================================

        if (
            old_slot_id == new_slot.id
            and old_room_id == new_room.id
        ):

            change_type = "panel_changed"

        else:

            change_type = "moved"

        moved_count += 1

        # ====================================================
        # RECORD
        # ====================================================

        changes.append(
            {
                "interview_id": interview.id,

                "student_id": interview.student_id,

                "change": change_type,

                "old_time_slot_id": old_slot_id,

                "new_time_slot_id": new_slot.id,

                "old_room_id": old_room_id,

                "new_room_id": new_room.id,

                "old_panel_id": old_panel_id,

                "new_panel_id": new_panel.id,

                "reason": (
                    f"Panel {panel_id} dropped out"
                )
            }
        )

        # ====================================================
        # ADD NEW POSITION
        # ====================================================

        add_interview_to_schedule(
            scheduled_interviews,
            interview
        )

        db.flush()

    # ========================================================
    # 11. COMMIT
    # ========================================================

    db.commit()

    # ========================================================
    # 12. CHURN
    # ========================================================

    total_affected = len(affected_interviews)

    if total_affected > 0:

        replan_churn_percent = round(
            (
                (moved_count + cancelled_count)
                / total_affected
            ) * 100,
            2
        )

    else:

        replan_churn_percent = 0

    # ========================================================
    # 13. RETURN
    # ========================================================

    return {
        "message": "Panel drop replan completed",

        "company_id": company_id,

        "panel_id": panel_id,

        "affected_interviews": total_affected,

        "moved_interviews": moved_count,

        "unchanged_interviews": unchanged_count,

        "cancelled_interviews": cancelled_count,

        "replan_churn_percent": replan_churn_percent,

        "changes": changes
    }