from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint("pages", __name__)


@bp.get("/")
def index():
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("pages.admin_dashboard"))
        return redirect(url_for("pages.student_dashboard"))
    return render_template("index.html")


@bp.get("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("pages.index"))
    return render_template("login.html")


@bp.get("/register")
def register_page():
    if "user_id" in session:
        return redirect(url_for("pages.index"))
    return render_template("register.html")


@bp.get("/dashboard")
def student_dashboard():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("pages.login_page"))
    return render_template("student_dashboard.html", name=session.get("name"))


@bp.get("/jobs")
def jobs_page():
    if "user_id" not in session:
        return redirect(url_for("pages.login_page"))
    return render_template("jobs.html", role=session.get("role"))


@bp.get("/admin")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("pages.login_page"))
    return render_template("admin_dashboard.html", name=session.get("name"))


@bp.app_errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404
