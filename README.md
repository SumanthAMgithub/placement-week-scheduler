# Placement Week Scheduler

A backend system for automatically scheduling campus placement interviews while respecting student, company, room, panel, time-slot, eligibility, and conflict constraints.

## Project Overview

The Placement Week Scheduler is designed to help placement coordinators generate an interview schedule for multiple companies and students.

The system considers:

- Company priority
- Student eligibility
- Student-company shortlisting
- Interview time slots
- Room availability
- Panel availability
- Student conflicts
- Room conflicts
- Panel conflicts
- Interview rescheduling

When an interview cannot be scheduled, the system provides a reason instead of silently failing.

---

## Key Features

### 1. Student Management

Students contain:

- Name
- CGPA
- Branch
- Status

Example:

```json
{
  "name": "Sumanth",
  "cgpa": 8.2,
  "branch": "MCA",
  "status": "active"
}