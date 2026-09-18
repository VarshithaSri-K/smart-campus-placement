from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import User, Student

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

BRANCHES = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL", "AI&DS", "CHEM"]


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ["name", "email", "password", "roll_no", "branch", "batch_year", "cgpa"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    if Student.query.filter_by(roll_no=data["roll_no"].strip()).first():
        return jsonify({"error": "Roll number already registered"}), 409

    try:
        cgpa = float(data["cgpa"])
        batch_year = int(data["batch_year"])
    except (TypeError, ValueError):
        return jsonify({"error": "CGPA and batch year must be numeric"}), 400

    if not (0 <= cgpa <= 10):
        return jsonify({"error": "CGPA must be between 0 and 10"}), 400

    user = User(name=data["name"].strip(), email=email, role="student")
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        roll_no=data["roll_no"].strip(),
        branch=data["branch"].strip(),
        batch_year=batch_year,
        cgpa=cgpa,
        backlogs=int(data.get("backlogs", 0) or 0),
        phone=data.get("phone", "").strip() or None,
        resume_link=data.get("resume_link", "").strip() or None,
    )
    db.session.add(student)
    db.session.commit()

    session.permanent = True
    session["user_id"] = user.id
    session["role"] = user.role
    session["name"] = user.name

    return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    session.permanent = True
    session["user_id"] = user.id
    session["role"] = user.role
    session["name"] = user.name

    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@bp.get("/me")
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False}), 200
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"authenticated": False}), 200
    payload = {"authenticated": True, "user": user.to_dict()}
    if user.role == "student" and user.student_profile:
        payload["student"] = user.student_profile.to_dict(include_user=False)
    return jsonify(payload), 200


@bp.get("/branches")
def branches():
    return jsonify({"branches": BRANCHES}), 200
