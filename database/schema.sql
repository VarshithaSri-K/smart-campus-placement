-- Smart Campus Placement Management & Recommendation System
-- MySQL schema. Note: The Flask app auto-creates these tables via
-- SQLAlchemy on first run (db.create_all()). This file is provided
-- for reference, manual setup, or import into MySQL Workbench.

CREATE DATABASE IF NOT EXISTS campus_placement CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_placement;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student','admin') NOT NULL DEFAULT 'student',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    roll_no VARCHAR(40) NOT NULL UNIQUE,
    branch VARCHAR(80) NOT NULL,
    batch_year INT NOT NULL,
    cgpa FLOAT NOT NULL DEFAULT 0,
    backlogs INT DEFAULT 0,
    phone VARCHAR(20),
    resume_link VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS student_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    skill_id INT NOT NULL,
    proficiency INT DEFAULT 2,
    UNIQUE KEY uq_student_skill (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    website VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    job_type ENUM('Full-Time','Internship','PPO') DEFAULT 'Full-Time',
    location VARCHAR(120),
    package_lpa FLOAT,
    min_cgpa FLOAT DEFAULT 0,
    max_backlogs INT DEFAULT 0,
    allowed_branches TEXT,
    required_skills TEXT,
    deadline DATE,
    status ENUM('open','closed') DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    job_id INT NOT NULL,
    match_score FLOAT DEFAULT 0,
    status ENUM('Applied','Shortlisted','Interview','Rejected','Selected') DEFAULT 'Applied',
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_job (student_id, job_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Helpful indexes
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_students_branch ON students(branch);
