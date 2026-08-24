import random

from sqlalchemy.orm import Session

from backend.database.models import (
    Company,
    Student,
    Room,
    Panel,
    TimeSlot
)


COMPANY_NAMES = [
    "TechNova",
    "Infosys",
    "TCS",
    "Wipro",
    "Accenture",
    "IBM",
    "Deloitte",
    "Cognizant",
    "Capgemini",
    "Oracle",
    "Microsoft",
    "Amazon",
    "Google",
    "Cisco",
    "Intel",
    "Adobe",
    "SAP",
    "Dell",
    "HP",
    "Bosch",
    "Siemens",
    "EY",
    "KPMG",
    "PwC",
    "Genpact",
    "Mindtree",
    "Mphasis",
    "Persistent",
    "Zoho",
    "Freshworks",
    "Razorpay",
    "Flipkart",
    "Paytm",
    "Swiggy",
    "PhonePe"
]


BRANCHES = [
    "CSE",
    "ISE",
    "ECE",
    "EEE",
    "MCA"
]


FIRST_NAMES = [
    "Rahul",
    "Priya",
    "Arjun",
    "Sneha",
    "Kiran",
    "Ananya",
    "Vikram",
    "Neha",
    "Rohan",
    "Pooja",
    "Sumanth",
    "Amit",
    "Divya",
    "Akash",
    "Meera"
]


LAST_NAMES = [
    "Sharma",
    "Patel",
    "Kumar",
    "Reddy",
    "Nair",
    "Singh",
    "Rao",
    "Shetty",
    "Das",
    "Verma"
]


def generate_companies(db: Session):
    companies = []

    for index, name in enumerate(COMPANY_NAMES, start=1):

        priority_tier = random.choice([1, 2, 3])

        cgpa_cutoff = round(
            random.uniform(6.5, 9.0),
            1
        )

        interview_duration = random.choice(
            [30, 45, 60]
        )

        panel_count = random.randint(1, 4)

        company = Company(
            name=name,
            priority_tier=priority_tier,
            cgpa_cutoff=cgpa_cutoff,
            interview_duration=interview_duration,
            panel_count=panel_count
        )

        db.add(company)
        companies.append(company)

    db.commit()

    return companies


def generate_students(db: Session, count=800):

    students = []

    for i in range(1, count + 1):

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        student = Student(
            name=f"{first_name} {last_name} {i}",
            cgpa=round(
                random.uniform(6.0, 10.0),
                2
            ),
            branch=random.choice(BRANCHES),
            status="active"
        )

        db.add(student)
        students.append(student)

    db.commit()

    return students
def generate_shortlists(db: Session, students, companies):

    shortlist_count = 0

    for student in students:

        eligible_companies = [
            company
            for company in companies
            if student.cgpa >= company.cgpa_cutoff
        ]

        if eligible_companies:

            number_of_companies = min(
                random.randint(3, 8),
                len(eligible_companies)
            )

            shortlisted_companies = random.sample(
                eligible_companies,
                number_of_companies
            )

            student.companies.extend(
                shortlisted_companies
            )

            shortlist_count += number_of_companies

    db.commit()

    return shortlist_count


def generate_rooms(db: Session, count=20):

    rooms = []

    for i in range(1, count + 1):

        room = Room(
            name=f"Room {i}",
            capacity=random.choice([2, 4, 6]),
            status="available"
        )

        db.add(room)
        rooms.append(room)

    db.commit()

    return rooms


def generate_panels(db: Session, companies):

    panels = []

    for company in companies:

        for number in range(1, company.panel_count + 1):

            panel = Panel(
                name=f"{company.name} Panel {number}",
                company_id=company.id,
                status="available"
            )

            db.add(panel)
            panels.append(panel)

    db.commit()

    return panels


def generate_time_slots(db: Session):

    slots = []

    for day in range(1, 6):

        for hour in range(9, 17):

            slot = TimeSlot(
                day=day,
                start_time=f"{hour:02d}:00",
                end_time=f"{hour + 1:02d}:00"
            )

            db.add(slot)
            slots.append(slot)

    db.commit()

    return slots


def generate_all_data(db: Session):

    companies = generate_companies(db)

    students = generate_students(db)

    shortlist_count = generate_shortlists(
        db,
        students,
        companies
    )

    rooms = generate_rooms(db)

    panels = generate_panels(
        db,
        companies
    )

    time_slots = generate_time_slots(db)

    return {
        "companies": len(companies),
        "students": len(students),
        "shortlists": shortlist_count,
        "rooms": len(rooms),
        "panels": len(panels),
        "time_slots": len(time_slots)
    }