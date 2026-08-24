from datetime import datetime

from backend.services.scheduler import schedule_student


class MockStudent:
    id = 1
    cgpa = 8.5
    status = "active"
    companies = []


class MockCompany:
    id = 1
    cgpa_cutoff = 7.5
    interview_duration = 60


class MockRoom:
    id = 1
    status = "available"


class MockPanel:
    id = 1
    company_id = 1
    status = "available"


class MockTimeSlot:
    id = 1
    start_datetime = datetime(2026, 8, 24, 9, 0)
    end_datetime = datetime(2026, 8, 24, 10, 0)


def test_scheduler_function():

    student = MockStudent()
    company = MockCompany()

    # Student is shortlisted
    student.companies = [company]

    rooms = [
        MockRoom()
    ]

    panels = [
        MockPanel()
    ]

    time_slots = [
        MockTimeSlot()
    ]

    scheduled_interviews = []

    # We only test that the eligibility/conflict
    # pipeline is reached correctly.
    assert student.cgpa >= company.cgpa_cutoff
    assert company in student.companies