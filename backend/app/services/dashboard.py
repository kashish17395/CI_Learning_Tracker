from collections import defaultdict
from sqlalchemy import select
from app.models import Assignment, Employee, User
from app.services.learning import filter_rows, learning_rows
from app.services.common import today


def summary(rows):
    counts = {
        "assigned": len(rows),
        "completed": 0,
        "in_progress": 0,
        "enrolled": 0,
        "pending": 0,
        "overdue": 0,
    }
    keys = {
        "COMPLETED": "completed",
        "IN_PROGRESS": "in_progress",
        "ENROLLED": "enrolled",
        "NOT_STARTED": "pending",
    }
    for row in rows:
        counts[keys[row["status"]]] += 1
        counts["overdue"] += int(row["overdue"])
    counts["completion_percentage"] = (
        round(100 * counts["completed"] / len(rows), 1) if rows else None
    )
    return counts


def dashboard(db, actor, filters, *, personal=False):
    employee_id = filters.pop("employee_id", None)
    if personal:
        employee = db.scalar(select(Employee).where(Employee.user_id == actor.id))
        employee_id = employee.id if employee else "__none__"
        rows = learning_rows(db, actor, employee.id) if employee else []
    else:
        rows = learning_rows(db, actor, employee_id)
    rows = filter_rows(rows, **filters)
    employees = db.scalars(
        select(Employee)
        .join(User, User.id == Employee.user_id)
        .where(User.is_active.is_(True))
    ).all()
    selected_employees = [
        e
        for e in employees
        if (not employee_id or e.id == employee_id)
        and (not filters.get("department") or e.department == filters["department"])
    ]
    employee_groups, course_groups = defaultdict(list), defaultdict(list)
    for row in rows:
        employee_groups[row["employee_id"]].append(row)
        course_groups[row["course_id"]].append(row)
    team = [
        {
            "employee_id": e.id,
            "name": e.name,
            "department": e.department,
            **summary(employee_groups[e.id]),
        }
        for e in selected_employees
    ]
    courses = [
        {"course_id": id, "name": group[0]["course"]["name"], **summary(group)}
        for id, group in course_groups.items()
    ]
    assignment_ids = {context["id"] for row in rows for context in row["assignments"]}
    upcoming = sorted(
        [
            row
            for row in rows
            if row["target_date"]
            and row["target_date"] >= today()
            and row["status"] != "COMPLETED"
        ],
        key=lambda r: r["target_date"],
    )[:8]
    return {
        "summary": {
            **summary(rows),
            "total_employees": len(selected_employees),
            "total_assignments": len(assignment_ids),
        },
        "employees": team,
        "courses": sorted(
            courses, key=lambda c: (c["completion_percentage"] or 0, c["name"])
        ),
        "upcoming": upcoming,
        "overdue": [r for r in rows if r["overdue"]][:20],
        "capability_gaps": [c for c in courses if c["completed"] < c["assigned"]],
        "priority_development": [
            r
            for r in rows
            if r["status"] != "COMPLETED"
            and any(
                a["is_mandatory"] and a["target_date"] and a["target_date"] < today()
                for a in r["assignments"]
            )
        ],
    }
