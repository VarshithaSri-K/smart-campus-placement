import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://placement_user:placement_pass@localhost:3306/campus_placement",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@campus.edu")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "Placement Officer")

    JSON_SORT_KEYS = False
