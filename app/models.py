import bcrypt
from datetime import datetime
from app.extensions import db


def now():
    return datetime.utcnow()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("student", "admin", name="user_role"), nullable=False, default="student")
    created_at = db.Column(db.DateTime, default=now)

    student_profile = db.relationship(
        "Student", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str):
        self.password_hash = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), self.password_hash.encode("utf-8"))
        except ValueError:
            return False

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class StudentSkill(db.Model):
    __tablename__ = "student_skills"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    # 1 = beginner, 2 = intermediate, 3 = advanced/expert
    proficiency = db.Column(db.Integer, default=2)

    skill = db.relationship("Skill")

    __table_args__ = (db.UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    roll_no = db.Column(db.String(40), unique=True, nullable=False)
    branch = db.Column(db.String(80), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float, nullable=False, default=0.0)
    backlogs = db.Column(db.Integer, default=0)
    phone = db.Column(db.String(20))
    resume_link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    skills = db.relationship(
        "StudentSkill", backref="student", cascade="all, delete-orphan", lazy="joined"
    )
    applications = db.relationship("Application", backref="student", cascade="all, delete-orphan")

    def skill_names(self):
        return [s.skill.name.lower() for s in self.skills]

    def to_dict(self, include_user=True):
        data = {
            "id": self.id,
            "roll_no": self.roll_no,
            "branch": self.branch,
            "batch_year": self.batch_year,
            "cgpa": self.cgpa,
            "backlogs": self.backlogs,
            "phone": self.phone,
            "resume_link": self.resume_link,
            "skills": [
                {"name": s.skill.name, "proficiency": s.proficiency} for s in self.skills
            ],
        }
        if include_user and self.user:
            data["name"] = self.user.name
            data["email"] = self.user.email
        return data


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now)

    jobs = db.relationship("Job", backref="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "website": self.website,
        }


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    job_type = db.Column(db.Enum("Full-Time", "Internship", "PPO", name="job_type"), default="Full-Time")
    location = db.Column(db.String(120))
    package_lpa = db.Column(db.Float)  # annual package in LPA
    min_cgpa = db.Column(db.Float, default=0.0)
    max_backlogs = db.Column(db.Integer, default=0)
    allowed_branches = db.Column(db.Text)  # comma separated, empty = all branches
    required_skills = db.Column(db.Text)  # comma separated skill names
    deadline = db.Column(db.Date)
    status = db.Column(db.Enum("open", "closed", name="job_status"), default="open")
    created_at = db.Column(db.DateTime, default=now)

    applications = db.relationship("Application", backref="job", cascade="all, delete-orphan")

    def branch_list(self):
        return [b.strip().lower() for b in (self.allowed_branches or "").split(",") if b.strip()]

    def skill_list(self):
        return [s.strip().lower() for s in (self.required_skills or "").split(",") if s.strip()]

    def to_dict(self, with_company=True):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "job_type": self.job_type,
            "location": self.location,
            "package_lpa": self.package_lpa,
            "min_cgpa": self.min_cgpa,
            "max_backlogs": self.max_backlogs,
            "allowed_branches": self.allowed_branches,
            "required_skills": self.required_skills,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status,
            "company_id": self.company_id,
        }
        if with_company and self.company:
            data["company_name"] = self.company.name
        return data


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    match_score = db.Column(db.Float, default=0.0)
    status = db.Column(
        db.Enum("Applied", "Shortlisted", "Interview", "Rejected", "Selected", name="application_status"),
        default="Applied",
    )
    applied_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    __table_args__ = (db.UniqueConstraint("student_id", "job_id", name="uq_student_job"),)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "job_id": self.job_id,
            "match_score": self.match_score,
            "status": self.status,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "job": self.job.to_dict() if self.job else None,
            "student": self.student.to_dict() if self.student else None,
        }
