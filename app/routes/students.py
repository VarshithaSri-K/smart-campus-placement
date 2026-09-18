from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import Student, Skill, StudentSkill, User
from app.utils.decorators import login_required, role_required

bp = Blueprint("students", __name__, url_prefix="/api/students")


def _get_current_student():
    return Student.query.filter_by(user_id=session["user_id"]).first()


@bp.get("/me")
@role_required("student")
def get_my_profile():
    student = _get_current_student()
    if not student:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(student.to_dict()), 200


@bp.put("/me")
@role_required("student")
def update_my_profile():
    student = _get_current_student()
    if not student:
        return jsonify({"error": "Profile not found"}), 404

    data = request.get_json(silent=True) or {}
    if "branch" in data and data["branch"]:
        student.branch = data["branch"].strip()
    if "cgpa" in data and data["cgpa"] not in (None, ""):
        try:
            cgpa = float(data["cgpa"])
            if not (0 <= cgpa <= 10):
                raise ValueError
            student.cgpa = cgpa
        except ValueError:
            return jsonify({"error": "CGPA must be a number between 0 and 10"}), 400
    if "backlogs" in data:
        try:
            student.backlogs = max(0, int(data["backlogs"]))
        except (TypeError, ValueError):
            return jsonify({"error": "Backlogs must be an integer"}), 400
    if "phone" in data:
        student.phone = (data["phone"] or "").strip() or None
    if "resume_link" in data:
        student.resume_link = (data["resume_link"] or "").strip() or None
    if "name" in data and data["name"]:
        student.user.name = data["name"].strip()
        session["name"] = student.user.name

    db.session.commit()
    return jsonify({"message": "Profile updated", "student": student.to_dict()}), 200


@bp.get("/me/skills")
@role_required("student")
def list_my_skills():
    student = _get_current_student()
    return jsonify({"skills": [{"name": s.skill.name, "proficiency": s.proficiency} for s in student.skills]}), 200


@bp.post("/me/skills")
@role_required("student")
def add_my_skill():
    student = _get_current_student()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    proficiency = data.get("proficiency", 2)
    if not name:
        return jsonify({"error": "Skill name is required"}), 400
    try:
        proficiency = int(proficiency)
        if proficiency not in (1, 2, 3):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Proficiency must be 1 (beginner), 2 (intermediate) or 3 (advanced)"}), 400

    skill = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
    if not skill:
        skill = Skill(name=name)
        db.session.add(skill)
        db.session.flush()

    existing = StudentSkill.query.filter_by(student_id=student.id, skill_id=skill.id).first()
    if existing:
        existing.proficiency = proficiency
    else:
        db.session.add(StudentSkill(student_id=student.id, skill_id=skill.id, proficiency=proficiency))

    db.session.commit()
    return jsonify({"message": "Skill saved"}), 201


@bp.delete("/me/skills/<string:skill_name>")
@role_required("student")
def remove_my_skill(skill_name):
    student = _get_current_student()
    skill = Skill.query.filter(db.func.lower(Skill.name) == skill_name.lower()).first()
    if not skill:
        return jsonify({"error": "Skill not found"}), 404
    link = StudentSkill.query.filter_by(student_id=student.id, skill_id=skill.id).first()
    if not link:
        return jsonify({"error": "You don't have this skill on your profile"}), 404
    db.session.delete(link)
    db.session.commit()
    return jsonify({"message": "Skill removed"}), 200


@bp.get("/skills/catalog")
@login_required
def skills_catalog():
    skills = Skill.query.order_by(Skill.name.asc()).all()
    return jsonify({"skills": [s.to_dict() for s in skills]}), 200


# ---- Admin-facing student directory ----

@bp.get("")
@role_required("admin")
def list_students():
    branch = request.args.get("branch")
    min_cgpa = request.args.get("min_cgpa", type=float)
    q = Student.query
    if branch:
        q = q.filter(Student.branch.ilike(branch))
    if min_cgpa is not None:
        q = q.filter(Student.cgpa >= min_cgpa)
    students = q.order_by(Student.roll_no.asc()).all()
    return jsonify({"students": [s.to_dict() for s in students]}), 200


@bp.get("/<int:student_id>")
@role_required("admin")
def get_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student.to_dict()), 200
