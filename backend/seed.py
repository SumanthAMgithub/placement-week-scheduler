from backend.database.database import SessionLocal
from backend.database.models import (
    Company,
    Student,
    StudentCompany,
    Room,
    Panel,
    TimeSlot,
    Interview
)

from backend.services.data_generator import generate_all_data


def clear_database(db):

    db.query(Interview).delete()
    db.query(StudentCompany).delete()
    db.query(Panel).delete()
    db.query(TimeSlot).delete()
    db.query(Room).delete()
    db.query(Student).delete()
    db.query(Company).delete()

    db.commit()


def main():

    db = SessionLocal()

    try:

        print("Clearing existing data...")

        clear_database(db)

        print("Generating placement data...")

        result = generate_all_data(db)

        print("\nData generation completed!")
        print("--------------------------------")

        for key, value in result.items():
            print(f"{key}: {value}")

        print("--------------------------------")

    finally:
        db.close()


if __name__ == "__main__":
    main()