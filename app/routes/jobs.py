from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import Job, Company, Student
from app.utils.decorators import login_required, role_required
from app.utils.matching import compute_match_score, is_eligible, rank_students_for_job

bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


@bp.get("")
@login_required
def list_jobs():
    status = request.args.get("status", "open")
    q = Job.query
    if status in ("open", "closed"):
        q = q.filter_by(status=status)
    jobs = q.order_by(Job.created_at.desc()).all()

    result = [j.to_dict() for j in jobs]

    if session.get("role") == "student":
        student = Student.query.filter_by(user_id=session["user_id"]).first()
        if student:
            for j, job_obj in zip(result, jobs):
                j["match_score"] = compute_match_score(student, job_obj)
                eligible, reason = is_eligible(student, job_obj)
                j["eligible"] = eligible
                j["eligibility_reason"] = reason
        result.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return jsonify({"jobs": result}), 200


@bp.get("/recommendations")
@role_required("student")
def recommendations():
    student = Student.query.filter_by(user_id=session["user_id"]).first()
    if not student:
        return jsonify({"error": "Profile not found"}), 404
    jobs = Job.query.filter_by(status="open").all()
    from app.utils.matching import rank_jobs_for_student
    ranked = rank_jobs_for_student(student, jobs)
    top = ranked[:10]
    return jsonify({
        "recommendations": [
            {
                "job": r["job"].to_dict(),
                "match_score": r["score"],
                "eligible": r["eligible"],
                "eligibility_reason": r["reason"],
            }
            for r in top
        ]
    }), 200


@bp.get("/<int:job_id>")
@login_required
def get_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    data = job.to_dict()
    if session.get("role") == "student":
        student = Student.query.filter_by(user_id=session["user_id"]).first()
        if student:
            data["match_score"] = compute_match_score(student, job)
            eligible, reason = is_eligible(student, job)
            data["eligible"] = eligible
            data["eligibility_reason"] = reason
    return jsonify(data), 200


@bp.get("/<int:job_id>/candidates")
@role_required("admin")
def job_candidates(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    students = Student.query.all()
    ranked = rank_students_for_job(job, students)
    return jsonify({
        "candidates": [
            {
                "student": r["student"].to_dict(),
                "match_score": r["score"],
                "eligible": r["eligible"],
                "eligibility_reason": r["reason"],
            }
            for r in ranked
        ]
    }), 200


# ---------- Admin: create/update/delete jobs & companies ----------

@bp.post("")
@role_required("admin")
def create_job():
    data = request.get_json(silent=True) or {}
    required = ["title", "company_name"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    company_name = data["company_name"].strip()
    company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()
    if not company:
        company = Company(
            name=company_name,
            description=data.get("company_description", ""),
            website=data.get("company_website", ""),
        )
        db.session.add(company)
        db.session.flush()

    deadline = None
    if data.get("deadline"):
        try:
            deadline = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Deadline must be in YYYY-MM-DD format"}), 400

    job = Job(
        company_id=company.id,
        title=data["title"].strip(),
        description=data.get("description", ""),
        job_type=data.get("job_type", "Full-Time"),
        location=data.get("location", ""),
        package_lpa=float(data["package_lpa"]) if data.get("package_lpa") else None,
        min_cgpa=float(data.get("min_cgpa", 0) or 0),
        max_backlogs=int(data.get("max_backlogs", 0) or 0),
        allowed_branches=",".join([b.strip() for b in data.get("allowed_branches", []) if b.strip()])
        if isinstance(data.get("allowed_branches"), list)
        else (data.get("allowed_branches") or ""),
        required_skills=",".join([s.strip() for s in data.get("required_skills", []) if s.strip()])
        if isinstance(data.get("required_skills"), list)
        else (data.get("required_skills") or ""),
        deadline=deadline,
        status=data.get("status", "open"),
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"message": "Job posted successfully", "job": job.to_dict()}), 201


@bp.put("/<int:job_id>")
@role_required("admin")
def update_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    data = request.get_json(silent=True) or {}

    simple_fields = ["title", "description", "job_type", "location", "status"]
    for f in simple_fields:
        if f in data and data[f] is not None:
            setattr(job, f, data[f])

    if "package_lpa" in data and data["package_lpa"] not in (None, ""):
        job.package_lpa = float(data["package_lpa"])
    if "min_cgpa" in data and data["min_cgpa"] not in (None, ""):
        job.min_cgpa = float(data["min_cgpa"])
    if "max_backlogs" in data and data["max_backlogs"] not in (None, ""):
        job.max_backlogs = int(data["max_backlogs"])
    if "allowed_branches" in data:
        val = data["allowed_branches"]
        job.allowed_branches = ",".join(val) if isinstance(val, list) else (val or "")
    if "required_skills" in data:
        val = data["required_skills"]
        job.required_skills = ",".join(val) if isinstance(val, list) else (val or "")
    if "deadline" in data and data["deadline"]:
        try:
            job.deadline = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Deadline must be in YYYY-MM-DD format"}), 400

    db.session.commit()
    return jsonify({"message": "Job updated", "job": job.to_dict()}), 200


@bp.delete("/<int:job_id>")
@role_required("admin")
def delete_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"}), 200


@bp.get("/companies/list")
@login_required
def list_companies():
    companies = Company.query.order_by(Company.name.asc()).all()
    return jsonify({"companies": [c.to_dict() for c in companies]}), 200
