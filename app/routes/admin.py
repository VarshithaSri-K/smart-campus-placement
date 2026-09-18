from flask import Blueprint, jsonify
from app.extensions import db
from app.models import Student, Job, Application, Company
from app.utils.decorators import role_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/stats")
@role_required("admin")
def stats():
    total_students = Student.query.count()
    total_jobs = Job.query.count()
    open_jobs = Job.query.filter_by(status="open").count()
    total_companies = Company.query.count()
    total_applications = Application.query.count()
    selected = Application.query.filter_by(status="Selected").count()

    branch_rows = (
        db.session.query(Student.branch, db.func.count(Student.id))
        .group_by(Student.branch)
        .all()
    )
    status_rows = (
        db.session.query(Application.status, db.func.count(Application.id))
        .group_by(Application.status)
        .all()
    )

    return jsonify({
        "total_students": total_students,
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "total_companies": total_companies,
        "total_applications": total_applications,
        "selected": selected,
        "students_by_branch": {b: c for b, c in branch_rows},
        "applications_by_status": {s: c for s, c in status_rows},
    }), 200
