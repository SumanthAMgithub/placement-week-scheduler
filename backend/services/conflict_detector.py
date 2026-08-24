from datetime import datetime


def times_overlap(
    start_time: datetime,
    end_time: datetime,
    existing_start: datetime,
    existing_end: datetime
) -> bool:
    """
    Check whether two time intervals overlap.
    """

    return (
        start_time < existing_end
        and end_time > existing_start
    )


def check_student_conflict(
    student_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> bool:
    """
    Returns True if the student is already scheduled
    during the requested time.
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


def check_room_conflict(
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> bool:
    """
    Returns True if the room is already occupied
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


def check_panel_conflict(
    panel_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> bool:
    """
    Returns True if the panel is already occupied
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


def check_all_conflicts(
    student_id: int,
    room_id: int,
    panel_id: int,
    start_time: datetime,
    end_time: datetime,
    scheduled_interviews: list
) -> dict:
    """
    Check all major scheduling conflicts.
    """

    student_conflict = check_student_conflict(
        student_id,
        start_time,
        end_time,
        scheduled_interviews
    )

    room_conflict = check_room_conflict(
        room_id,
        start_time,
        end_time,
        scheduled_interviews
    )

    panel_conflict = check_panel_conflict(
        panel_id,
        start_time,
        end_time,
        scheduled_interviews
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