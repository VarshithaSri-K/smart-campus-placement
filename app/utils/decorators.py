from functools import wraps
from flask import session, jsonify, redirect, url_for, request


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("pages.login_page"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("pages.login_page"))
            if session.get("role") not in roles:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Forbidden: insufficient permissions"}), 403
                return redirect(url_for("pages.index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator
