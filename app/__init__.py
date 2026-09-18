import os
from flask import Flask
from app.config import Config
from app.extensions import db, cors


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_class)

    db.init_app(app)
    cors.init_app(app, supports_credentials=True)

    from app.routes import auth, students, jobs, applications, admin, pages
    app.register_blueprint(auth.bp)
    app.register_blueprint(students.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(applications.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(pages.bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}, 200

    with app.app_context():
        db.create_all()
        _ensure_admin(app)

    return app


def _ensure_admin(app):
    from app.models import User
    admin_email = app.config["ADMIN_EMAIL"]
    if not User.query.filter_by(email=admin_email).first():
        admin = User(name=app.config["ADMIN_NAME"], email=admin_email, role="admin")
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        app.logger.info(f"Created default admin account: {admin_email}")
