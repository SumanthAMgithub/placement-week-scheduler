from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey
)

from sqlalchemy.orm import relationship

from .database import Base
from datetime import datetime, timedelta


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    priority_tier = Column(Integer, nullable=False)
    cgpa_cutoff = Column(Float, nullable=False)
    interview_duration = Column(Integer, nullable=False)
    panel_count = Column(Integer, nullable=False)

    students = relationship(
        "Student",
        secondary="student_company",
        back_populates="companies"
    )

    panels = relationship(
        "Panel",
        back_populates="company"
    )


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    cgpa = Column(Float, nullable=False)
    branch = Column(String, nullable=False)
    status = Column(String, default="active")

    companies = relationship(
        "Company",
        secondary="student_company",
        back_populates="students"
    )


class StudentCompany(Base):
    __tablename__ = "student_company"

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        primary_key=True
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        primary_key=True
    )


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String, default="available")


class Panel(Base):
    __tablename__ = "panels"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False
    )

    status = Column(String, default="available")

    company = relationship(
        "Company",
        back_populates="panels"
    )


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)

    day = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)

    @property
    def start_datetime(self):
        return datetime.strptime(
            f"2026-08-{23 + self.day:02d} {self.start_time}",
            "%Y-%m-%d %H:%M"
        )

    @property
    def end_datetime(self):
        return datetime.strptime(
            f"2026-08-{23 + self.day:02d} {self.end_time}",
            "%Y-%m-%d %H:%M"
        )


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=True
    )

    panel_id = Column(
        Integer,
        ForeignKey("panels.id"),
        nullable=True
    )

    time_slot_id = Column(
        Integer,
        ForeignKey("time_slots.id"),
        nullable=True
    )

    status = Column(
        String,
        default="scheduled"
    )

    reason = Column(
        String,
        nullable=True
    )

    student = relationship(
        "Student"
    )

    company = relationship(
        "Company"
    )

    room = relationship(
        "Room"
    )

    panel = relationship(
        "Panel"
    )

    time_slot = relationship(
        "TimeSlot"
    )