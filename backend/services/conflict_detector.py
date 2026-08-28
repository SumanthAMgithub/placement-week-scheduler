from datetime import datetime


# ============================================================
# 1. TIME OVERLAP
# ============================================================

def times_overlap(
    start_time: datetime,
    end_time: datetime,
    existing_start: datetime,
    existing_end: datetime
) -> bool:
    """
    Return True when two time intervals overlap.

    Example:

        10:00 - 10:30
        10:15 - 10:45

    These overlap.

    But:

        10:00 - 10:30
        10:30 - 11:00

    do NOT overlap.
    """

    return (
        start_time < existing_end
        and end_time > existing_start
    )


# ============================================================
# 2. STUDENT CONFLICT
# ============================================================

def check_student_conflict(
    student_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> bool:
    """
    Check whether the student already has another
    interview during the requested time.
    """

    for interview in scheduled_interviews:

        if interview["student_id"] != student_id:
            continue

        if times_overlap(
            start_time,
            end_time,
            interview["start_time"],
            interview["end_time"]
        ):
            return True

    return False


# ============================================================
# 3. ROOM CONFLICT
# ============================================================

def check_room_conflict(
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> bool:
    """
    Check whether the room is already occupied
    during the requested time.
    """

    for interview in scheduled_interviews:

        if interview["room_id"] != room_id:
            continue

        if times_overlap(
            start_time,
            end_time,
            interview["start_time"],
            interview["end_time"]
        ):
            return True

    return False


# ============================================================
# 4. PANEL CONFLICT
# ============================================================

def check_panel_conflict(
    panel_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> bool:
    """
    Check whether the panel is already occupied
    during the requested time.
    """

    for interview in scheduled_interviews:

        if interview["panel_id"] != panel_id:
            continue

        if times_overlap(
            start_time,
            end_time,
            interview["start_time"],
            interview["end_time"]
        ):
            return True

    return False


# ============================================================
# 5. ALL CONFLICTS
# ============================================================

def check_all_conflicts(
    student_id: int,
    room_id: int,
    panel_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> dict:
    """
    Check student, room and panel conflicts.
    """

    student_conflict = check_student_conflict(
        student_id=student_id,
        start_time=start_time,
        end_time=end_time,
        scheduled_interviews=scheduled_interviews
    )

    room_conflict = check_room_conflict(
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        scheduled_interviews=scheduled_interviews
    )

    panel_conflict = check_panel_conflict(
        panel_id=panel_id,
        start_time=start_time,
        end_time=end_time,
        scheduled_interviews=scheduled_interviews
    )

    return {
        "student_conflict": student_conflict,
        "room_conflict": room_conflict,
        "panel_conflict": panel_conflict,
        "has_conflict": (
            student_conflict
            or room_conflict
            or panel_conflict
        )
    }