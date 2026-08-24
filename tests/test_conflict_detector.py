from datetime import datetime

from backend.services.conflict_detector import (
    check_all_conflicts
)


def test_student_conflict():

    scheduled_interviews = [
        {
            "student_id": 1,
            "room_id": 1,
            "panel_id": 1,
            "start_time": datetime(2026, 8, 24, 10, 0),
            "end_time": datetime(2026, 8, 24, 11, 0)
        }
    ]

    result = check_all_conflicts(
        student_id=1,
        room_id=2,
        panel_id=2,
        start_time=datetime(2026, 8, 24, 10, 30),
        end_time=datetime(2026, 8, 24, 11, 30),
        scheduled_interviews=scheduled_interviews
    )

    assert result["student_conflict"] is True
    assert result["room_conflict"] is False
    assert result["panel_conflict"] is False
    assert result["has_conflict"] is True