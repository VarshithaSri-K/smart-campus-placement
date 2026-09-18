"""
Populate the database with sample data for demo/testing purposes.
Run with:  python seed.py
"""
import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User, Student, Skill, StudentSkill, Company, Job


def get_or_create_skill(name):
    skill = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
    if not skill:
        skill = Skill(name=name)
        db.session.add(skill)
        db.session.flush()
    return skill


def seed():
    app = create_app()
    with app.app_context():
        if Student.query.count() > 0:
            print("Database already has student data. Skipping seed.")
            return

        sample_students = [
            dict(name="Aditi Rao", email="aditi.rao@student.edu", roll_no="CSE001", branch="CSE",
                 batch_year=2026, cgpa=8.9, backlogs=0,
                 skills=[("Python", 3), ("Flask", 2), ("SQL", 2), ("React", 2)]),
            dict(name="Rohan Mehta", email="rohan.mehta@student.edu", roll_no="ECE002", branch="ECE",
                 batch_year=2026, cgpa=7.4, backlogs=1,
                 skills=[("C++", 2), ("Embedded Systems", 3), ("Python", 1)]),
            dict(name="Sneha Iyer", email="sneha.iyer@student.edu", roll_no="IT003", branch="IT",
                 batch_year=2026, cgpa=9.2, backlogs=0,
                 skills=[("Java", 3), ("Spring Boot", 3), ("SQL", 3), ("AWS", 2)]),
            dict(name="Karan Patel", email="karan.patel@student.edu", roll_no="CSE004", branch="CSE",
                 batch_year=2027, cgpa=6.8, backlogs=2,
                 skills=[("JavaScript", 2), ("Node.js", 2), ("MongoDB", 1)]),
            dict(name="Divya Nair", email="divya.nair@student.edu", roll_no="AIDS005", branch="AI&DS",
                 batch_year=2026, cgpa=8.5, backlogs=0,
                 skills=[("Python", 3), ("Machine Learning", 3), ("SQL", 2), ("TensorFlow", 2)]),
        ]

        for s in sample_students:
            user = User(name=s["name"], email=s["email"], role="student")
            user.set_password("Student@123")
            db.session.add(user)
            db.session.flush()

            student = Student(
                user_id=user.id, roll_no=s["roll_no"], branch=s["branch"],
                batch_year=s["batch_year"], cgpa=s["cgpa"], backlogs=s["backlogs"],
                phone="9999999999", resume_link=None,
            )
            db.session.add(student)
            db.session.flush()

            for skill_name, prof in s["skills"]:
                skill = get_or_create_skill(skill_name)
                db.session.add(StudentSkill(student_id=student.id, skill_id=skill.id, proficiency=prof))

        companies = [
            dict(name="TechNova Solutions", description="Product-based software company.", website="https://technova.example.com"),
            dict(name="DataForge Analytics", description="Data & AI consultancy.", website="https://dataforge.example.com"),
            dict(name="CoreEdge Systems", description="Embedded & hardware systems.", website="https://coreedge.example.com"),
        ]
        company_objs = {}
        for c in companies:
            company = Company(**c)
            db.session.add(company)
            db.session.flush()
            company_objs[c["name"]] = company

        jobs = [
            dict(company="TechNova Solutions", title="Software Engineer - Backend", job_type="Full-Time",
                 location="Bengaluru", package_lpa=9.5, min_cgpa=7.0, max_backlogs=1,
                 allowed_branches="CSE,IT,AI&DS", required_skills="Python,Flask,SQL",
                 description="Work on scalable backend REST APIs and microservices.",
                 deadline=date.today() + timedelta(days=20)),
            dict(company="TechNova Solutions", title="Frontend Developer Intern", job_type="Internship",
                 location="Remote", package_lpa=4.0, min_cgpa=6.0, max_backlogs=2,
                 allowed_branches="CSE,IT", required_skills="JavaScript,React",
                 description="Build responsive UI components for our web platform.",
                 deadline=date.today() + timedelta(days=15)),
            dict(company="DataForge Analytics", title="Data Scientist", job_type="Full-Time",
                 location="Hyderabad", package_lpa=12.0, min_cgpa=8.0, max_backlogs=0,
                 allowed_branches="CSE,AI&DS,IT", required_skills="Python,Machine Learning,SQL",
                 description="Build ML models for customer analytics pipelines.",
                 deadline=date.today() + timedelta(days=30)),
            dict(company="CoreEdge Systems", title="Embedded Systems Engineer", job_type="Full-Time",
                 location="Pune", package_lpa=7.5, min_cgpa=6.5, max_backlogs=2,
                 allowed_branches="ECE,EEE", required_skills="C++,Embedded Systems",
                 description="Design firmware for IoT devices.",
                 deadline=date.today() + timedelta(days=25)),
            dict(company="DataForge Analytics", title="Java Backend Developer", job_type="Full-Time",
                 location="Chennai", package_lpa=8.0, min_cgpa=7.0, max_backlogs=1,
                 allowed_branches="", required_skills="Java,Spring Boot,SQL",
                 description="Develop enterprise-grade backend services in Java.",
                 deadline=date.today() + timedelta(days=18)),
        ]

        for j in jobs:
            job = Job(
                company_id=company_objs[j["company"]].id,
                title=j["title"], job_type=j["job_type"], location=j["location"],
                package_lpa=j["package_lpa"], min_cgpa=j["min_cgpa"], max_backlogs=j["max_backlogs"],
                allowed_branches=j["allowed_branches"], required_skills=j["required_skills"],
                description=j["description"], deadline=j["deadline"], status="open",
            )
            db.session.add(job)

        db.session.commit()
        print("Seed data created successfully.")
        print("Sample student login -> email: aditi.rao@student.edu / password: Student@123")
        print(f"Admin login -> email: {app.config['ADMIN_EMAIL']} / password: {app.config['ADMIN_PASSWORD']}")


if __name__ == "__main__":
    seed()
