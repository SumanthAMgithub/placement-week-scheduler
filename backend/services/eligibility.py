def is_student_eligible(student, company):
    """
    Check whether a student satisfies
    the company's basic CGPA requirement.
    """

    return student.cgpa >= company.cgpa_cutoff


def is_student_shortlisted(student, company):
    """
    Check whether the student is shortlisted
    for the company.
    """

    return company in student.companies


def can_student_be_scheduled(student, company):
    """
    Perform all basic eligibility checks.
    """

    if student.status != "active":
        return False

    if not is_student_eligible(student, company):
        return False

    if not is_student_shortlisted(student, company):
        return False

    return True