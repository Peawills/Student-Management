# academics/utils.py

from django.db.models import Avg, Count, Q
from .models import TermResult, StudentScore, Assessment


def calculate_grade(score):
    """
    Calculate letter grade from numeric score

    Args:
        score: Numeric score (0-100)

    Returns:
        Letter grade (A-F)
    """
    if score >= 75:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 45:
        return "D"
    elif score >= 40:
        return "E"
    else:
        return "F"


def calculate_grade_point(grade):
    """
    Calculate grade point from letter grade

    Args:
        grade: Letter grade (A-F)

    Returns:
        Grade point (0-5)
    """
    grade_points = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}
    return grade_points.get(grade, 0)


def get_grade_remark(grade):
    """
    Get remark based on grade

    Args:
        grade: Letter grade (A-F)

    Returns:
        Remark string
    """
    remarks = {
        "A": "Excellent",
        "B": "Very Good",
        "C": "Good",
        "D": "Fair",
        "E": "Pass",
        "F": "Fail",
    }
    return remarks.get(grade, "N/A")


def calculate_class_position(student, term, classroom):
    """
    Calculate student's position in class for a term

    Args:
        student: Student object
        term: Term object
        classroom: ClassRoom object

    Returns:
        Dictionary with position and total students
    """
    # Get all students' total scores for this term and class
    results = (
        TermResult.objects.filter(term=term, classroom=classroom)
        .values("student")
        .annotate(total=Count("id"), avg_score=Avg("total_score"))
        .order_by("-avg_score")
    )

    # Find student's position
    position = 1
    total_students = results.count()

    for idx, result in enumerate(results, start=1):
        if result["student"] == student.id:
            position = idx
            break

    return {"position": position, "out_of": total_students}


def calculate_subject_statistics(subject, term, classroom):
    """
    Calculate statistics for a subject in a class

    Args:
        subject: Subject object
        term: Term object
        classroom: ClassRoom object

    Returns:
        Dictionary with statistics
    """
    results = TermResult.objects.filter(subject=subject, term=term, classroom=classroom)

    if not results.exists():
        return None

    stats = results.aggregate(
        average=Avg("total_score"),
        pass_count=Count("id", filter=Q(total_score__gte=40)),
        total_students=Count("id"),
    )

    stats["fail_count"] = stats["total_students"] - stats["pass_count"]
    stats["pass_rate"] = (
        (stats["pass_count"] / stats["total_students"] * 100)
        if stats["total_students"] > 0
        else 0
    )

    # Grade distribution
    stats["grade_distribution"] = {
        "A": results.filter(grade="A").count(),
        "B": results.filter(grade="B").count(),
        "C": results.filter(grade="C").count(),
        "D": results.filter(grade="D").count(),
        "E": results.filter(grade="E").count(),
        "F": results.filter(grade="F").count(),
    }

    return stats


def get_student_rank_suffix(position):
    """
    Get ordinal suffix for position (1st, 2nd, 3rd, etc.)

    Args:
        position: Integer position

    Returns:
        Position with suffix (e.g., "1st", "2nd")
    """
    if 10 <= position % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(position % 10, "th")

    return f"{position}{suffix}"


def calculate_weighted_score(scores, assessment_types):
    """
    Calculate weighted total score from multiple assessments

    Args:
        scores: QuerySet of StudentScore objects
        assessment_types: Dictionary mapping assessment type codes to weights

    Returns:
        Weighted total score
    """
    total = 0

    for score in scores:
        weight = assessment_types.get(
            score.assessment.assessment_type.code,
            score.assessment.assessment_type.weight,
        )

        # Calculate percentage then apply weight
        percentage = (score.score / score.assessment.max_score) * 100
        weighted = (percentage * weight) / 100
        total += weighted

    return round(total, 2)


def get_performance_trend(student, subject, num_terms=3):
    """
    Get performance trend for a student in a subject

    Args:
        student: Student object
        subject: Subject object
        num_terms: Number of recent terms to analyze

    Returns:
        List of dictionaries with term and score data
    """
    results = TermResult.objects.filter(student=student, subject=subject).order_by(
        "-term__session__start_date", "-term__name"
    )[:num_terms]

    trend = []
    for result in results:
        trend.append(
            {
                "term": str(result.term),
                "score": float(result.total_score),
                "grade": result.grade,
                "position": result.position,
            }
        )

    # Reverse to show oldest to newest
    return list(reversed(trend))


def generate_teacher_comment(average_score, attendance_rate=None):
    """
    Generate automatic teacher comment based on performance

    Args:
        average_score: Student's average score
        attendance_rate: Optional attendance percentage

    Returns:
        Generated comment string
    """
    comments = []

    # Performance comment
    if average_score >= 75:
        comments.append("Excellent performance. Keep up the outstanding work!")
    elif average_score >= 65:
        comments.append("Very good performance. Continue working hard.")
    elif average_score >= 55:
        comments.append("Good performance. You can do better with more effort.")
    elif average_score >= 45:
        comments.append("Fair performance. More dedication is needed.")
    elif average_score >= 40:
        comments.append(
            "Satisfactory performance. Significant improvement is required."
        )
    else:
        comments.append("Poor performance. Serious attention is needed.")

    # Attendance comment if provided
    if attendance_rate is not None:
        if attendance_rate >= 90:
            comments.append("Excellent attendance.")
        elif attendance_rate >= 75:
            comments.append("Good attendance.")
        else:
            comments.append("Attendance needs improvement.")

    return " ".join(comments)


def validate_score_entry(score, max_score):
    """
    Validate score entry

    Args:
        score: Score to validate
        max_score: Maximum allowed score

    Returns:
        Tuple (is_valid, error_message)
    """
    if score < 0:
        return False, "Score cannot be negative"

    if score > max_score:
        return False, f"Score cannot exceed {max_score}"

    return True, None


def get_subject_performance_summary(term, classroom=None):
    """
    Get performance summary for all subjects

    Args:
        term: Term object
        classroom: Optional ClassRoom object to filter by

    Returns:
        List of dictionaries with subject performance data
    """
    results = TermResult.objects.filter(term=term)

    if classroom:
        results = results.filter(classroom=classroom)

    # Group by subject
    summary = (
        results.values("subject__name")
        .annotate(
            avg_score=Avg("total_score"),
            total_students=Count("student", distinct=True),
            pass_count=Count("id", filter=Q(total_score__gte=40)),
        )
        .order_by("-avg_score")
    )

    # Add pass rate
    for item in summary:
        item["pass_rate"] = (
            (item["pass_count"] / item["total_students"] * 100)
            if item["total_students"] > 0
            else 0
        )
        item["fail_count"] = item["total_students"] - item["pass_count"]

    return list(summary)


def compare_term_performance(student, term1, term2):
    """
    Compare student performance between two terms

    Args:
        student: Student object
        term1: First Term object (older)
        term2: Second Term object (newer)

    Returns:
        Dictionary with comparison data
    """
    results1 = TermResult.objects.filter(student=student, term=term1)
    results2 = TermResult.objects.filter(student=student, term=term2)

    if not results1.exists() or not results2.exists():
        return None

    avg1 = results1.aggregate(avg=Avg("total_score"))["avg"]
    avg2 = results2.aggregate(avg=Avg("total_score"))["avg"]

    difference = avg2 - avg1
    percentage_change = (difference / avg1 * 100) if avg1 > 0 else 0

    return {
        "term1": {
            "term": str(term1),
            "average": round(avg1, 2),
            "results_count": results1.count(),
        },
        "term2": {
            "term": str(term2),
            "average": round(avg2, 2),
            "results_count": results2.count(),
        },
        "difference": round(difference, 2),
        "percentage_change": round(percentage_change, 2),
        "improved": difference > 0,
    }


def get_top_performers(term, classroom=None, limit=10):
    """
    Get top performing students for a term

    Args:
        term: Term object
        classroom: Optional ClassRoom object to filter by
        limit: Number of top students to return

    Returns:
        List of dictionaries with student data
    """
    results = TermResult.objects.filter(term=term)

    if classroom:
        results = results.filter(classroom=classroom)

    # Group by student and calculate average
    top_students = (
        results.values(
            "student__id",
            "student__surname",
            "student__other_name",
            "student__admission_no",
            "classroom__level",
            "classroom__arm",
        )
        .annotate(avg_score=Avg("total_score"), subject_count=Count("subject"))
        .order_by("-avg_score")[:limit]
    )

    return list(top_students)


def calculate_cumulative_average(student, session):
    """
    Calculate cumulative average for a student across all terms in a session

    Args:
        student: Student object
        session: AcademicSession object

    Returns:
        Cumulative average score
    """
    results = TermResult.objects.filter(student=student, term__session=session)

    if not results.exists():
        return None

    cumulative_avg = results.aggregate(avg=Avg("total_score"))["avg"]

    return round(cumulative_avg, 2) if cumulative_avg else None
