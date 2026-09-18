from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import Application, Job, Student
from app.utils.decorators import role_required
from app.utils.matching import compute_match_score, is_eligible

bp = Blueprint("applications", __name__, url_prefix="/api/applications")


@bp.get("/me")
@role_required("student")
def my_applications():
    student = Student.query.filter_by(user_id=session["user_id"]).first()
    if not student:
        return jsonify({"error": "Profile not found"}), 404
    apps = Application.query.filter_by(student_id=student.id).order_by(Application.applied_at.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps]}), 200


@bp.post("/jobs/<int:job_id>")
@role_required("student")
def apply_to_job(job_id):
    student = Student.query.filter_by(user_id=session["user_id"]).first()
    if not student:
        return jsonify({"error": "Profile not found"}), 404

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    existing = Application.query.filter_by(student_id=student.id, job_id=job.id).first()
    if existing:
        return jsonify({"error": "You have already applied to this job"}), 409

    eligible, reason = is_eligible(student, job)
    if not eligible:
        return jsonify({"error": f"Not eligible: {reason}"}), 403

    score = compute_match_score(student, job)
    application = Application(student_id=student.id, job_id=job.id, match_score=score, status="Applied")
    db.session.add(application)
    db.session.commit()

    return jsonify({"message": "Application submitted", "application": application.to_dict()}), 201


@bp.delete("/<int:application_id>")
@role_required("student")
def withdraw_application(application_id):
    student = Student.query.filter_by(user_id=session["user_id"]).first()
    application = Application.query.get(application_id)
    if not application or application.student_id != student.id:
        return jsonify({"error": "Application not found"}), 404
    if application.status in ("Selected",):
        return jsonify({"error": "Cannot withdraw a finalized selection"}), 400
    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Application withdrawn"}), 200


# ---------- Admin ----------

@bp.get("")
@role_required("admin")
def list_all_applications():
    job_id = request.args.get("job_id", type=int)
    status = request.args.get("status")
    q = Application.query
    if job_id:
        q = q.filter_by(job_id=job_id)
    if status:
        q = q.filter_by(status=status)
    apps = q.order_by(Application.match_score.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps]}), 200


@bp.put("/<int:application_id>/status")
@role_required("admin")
def update_status(application_id):
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    valid = ["Applied", "Shortlisted", "Interview", "Rejected", "Selected"]
    if new_status not in valid:
        return jsonify({"error": f"Status must be one of {valid}"}), 400
    application.status = new_status
    db.session.commit()
    return jsonify({"message": "Status updated", "application": application.to_dict()}), 200
