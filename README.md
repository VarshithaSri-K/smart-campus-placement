# Smart Campus Placement Management & Recommendation System

A full-stack platform for managing student profiles, job postings, eligibility
screening and placement applications — with a skill-matching algorithm that
scores candidate–job compatibility.

**Stack:** Python (Flask) · MySQL (SQLAlchemy) · REST APIs · HTML/CSS/JavaScript

---

## Features

- **Student self-service:** register, maintain academic profile (branch, CGPA,
  backlogs), add/remove skills with proficiency levels.
- **Admin/placement-officer dashboard:** post jobs, view stats, manage
  applications, browse the student directory.
- **Eligibility screening:** a student can only apply if they meet a job's
  minimum CGPA, backlog ceiling and branch restriction.
- **Skill-matching algorithm** (`app/utils/matching.py`): scores every
  candidate–job pair 0–100 using a weighted blend of skill overlap (60%),
  CGPA strength (25%) and branch fit (15%). Used for:
  - Ranked job recommendations per student
  - Ranked candidate lists per job (for admins shortlisting)
- **REST API** covering auth, students, skills, jobs, companies and
  applications (see `API_REFERENCE` below).
- Session-based auth, bcrypt password hashing, CORS enabled for API use from
  other clients if needed.

---

## Project Structure

```
smart-campus-placement/
├── app/
│   ├── __init__.py        # App factory, blueprint registration, DB init
│   ├── config.py          # Config from environment variables
│   ├── extensions.py      # db, cors singletons
│   ├── models.py          # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py        # /api/auth/*
│   │   ├── students.py    # /api/students/*
│   │   ├── jobs.py        # /api/jobs/*
│   │   ├── applications.py# /api/applications/*
│   │   ├── admin.py       # /api/admin/*
│   │   └── pages.py       # HTML page routes
│   └── utils/
│       ├── matching.py    # Skill-matching / recommendation algorithm
│       └── decorators.py  # login_required / role_required
├── static/{css,js}        # Frontend assets (vanilla JS, no build step)
├── templates/             # Jinja2 HTML templates
├── database/schema.sql    # Reference MySQL schema (auto-created by the app too)
├── seed.py                # Sample data loader
├── run.py                 # Local dev entrypoint
├── wsgi.py                # Production entrypoint (gunicorn)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml      # App + MySQL, one command spin-up
├── Procfile                # For Render/Railway/Heroku-style platforms
└── .env.example
```

---

## 1. Local Setup (without Docker)

### Prerequisites
- Python 3.10+
- MySQL 8.0+ running locally (or a hosted MySQL instance)

### Steps

```bash
# 1. Clone / unzip the project, then enter the folder
cd smart-campus-placement

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the MySQL database and user
mysql -u root -p
```
```sql
CREATE DATABASE campus_placement CHARACTER SET utf8mb4;
CREATE USER 'placement_user'@'localhost' IDENTIFIED BY 'placement_pass';
GRANT ALL PRIVILEGES ON campus_placement.* TO 'placement_user'@'localhost';
FLUSH PRIVILEGES;
```

```bash
# 5. Configure environment variables
cp .env.example .env
# edit .env with your DB credentials and a real SECRET_KEY

# 6. Run the app (tables are auto-created on first run)
python run.py
```

The app is now running at **http://localhost:5000**.
A default admin account is created automatically using `ADMIN_EMAIL` /
`ADMIN_PASSWORD` from your `.env` (defaults: `admin@campus.edu` / `Admin@123`).

### Optional: load sample data

```bash
python seed.py
```
This adds 5 sample students, 3 companies and 5 job postings so you can see
the matching algorithm and dashboards populated immediately.
(Sample student login: `aditi.rao@student.edu` / `Student@123`)

---

## 2. Run with Docker (recommended for a quick deploy-ready demo)

This spins up **both** the Flask app and a MySQL container:

```bash
docker compose up --build
```

Then visit **http://localhost:5000**. Data persists in a Docker volume
(`db_data`) across restarts. To load sample data into the running container:

```bash
docker compose exec web python seed.py
```

To stop:
```bash
docker compose down          # keep data
docker compose down -v       # wipe data too
```

---

## 3. Deploying to Production

The app is stateless (all state lives in MySQL), uses `gunicorn` as the
production WSGI server, and reads all config from environment variables —
so it works on most PaaS providers with minimal changes.

### Option A — Render / Railway / Fly.io (Docker or buildpack)
1. Push this project to a Git repository.
2. Create a new **Web Service** from the repo.
   - If the platform supports Docker: it will pick up the `Dockerfile` automatically.
   - Otherwise, set the **Start Command** to the contents of `Procfile`:
     `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 3 --timeout 120`
3. Provision a managed MySQL database (Render/Railway both offer one-click MySQL/Postgres add-ons — for MySQL use PlanetScale, AWS RDS, or the platform's MySQL add-on).
4. Set environment variables on the platform:
   - `SECRET_KEY` (long random string)
   - `DATABASE_URL` = `mysql+pymysql://<user>:<password>@<host>:<port>/<db>`
   - `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME`
5. Deploy. On first boot the app auto-creates all tables and the admin account.

### Option B — Any VPS (Ubuntu) with Docker
```bash
git clone <your-repo-url>
cd smart-campus-placement
cp .env.example .env   # edit values
docker compose up -d --build
```
Put nginx (or Caddy) in front of port 5000 for TLS termination if exposing publicly.

### Option C — PythonAnywhere / traditional WSGI hosting
- Upload the project, create a virtualenv, `pip install -r requirements.txt`.
- Point the WSGI file to import `app` from `wsgi.py`.
- Set the same environment variables via the platform's "environment variables" panel or a `.env` file loaded by `python-dotenv`.
- Use the platform's MySQL database (most, like PythonAnywhere, provide one).

---

## API Reference (summary)

All endpoints are JSON over `POST/GET/PUT/DELETE`, prefixed with `/api`.
Session cookies handle auth — call `/api/auth/login` first, then the browser
automatically sends the cookie on subsequent requests.

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/api/auth/register` | POST | public | Register a new student |
| `/api/auth/login` | POST | public | Login |
| `/api/auth/logout` | POST | any | Logout |
| `/api/auth/me` | GET | any | Current session info |
| `/api/students/me` | GET/PUT | student | View/update own profile |
| `/api/students/me/skills` | GET/POST | student | List/add a skill |
| `/api/students/me/skills/<name>` | DELETE | student | Remove a skill |
| `/api/students` | GET | admin | List/filter all students |
| `/api/jobs` | GET | any | List jobs (students see match scores) |
| `/api/jobs` | POST | admin | Create a job posting |
| `/api/jobs/<id>` | GET/PUT/DELETE | mixed | Job detail / update / delete |
| `/api/jobs/recommendations` | GET | student | Top 10 ranked job matches |
| `/api/jobs/<id>/candidates` | GET | admin | Ranked candidate list for a job |
| `/api/applications/me` | GET | student | My applications |
| `/api/applications/jobs/<job_id>` | POST | student | Apply to a job |
| `/api/applications/<id>` | DELETE | student | Withdraw an application |
| `/api/applications` | GET | admin | List/filter all applications |
| `/api/applications/<id>/status` | PUT | admin | Update application status |
| `/api/admin/stats` | GET | admin | Dashboard summary statistics |

---

## Matching Algorithm

See `app/utils/matching.py`. For a student `S` and job `J`:

```
score = 0.60 * skill_overlap(S, J)     # skills matched, weighted by proficiency
      + 0.25 * cgpa_strength(S)        # CGPA normalized to 100, minus backlog penalty
      + 0.15 * branch_fit(S, J)        # 100 if branch allowed / no restriction, else 0
```

Eligibility (a hard gate before applying) is evaluated separately and checks
minimum CGPA, maximum backlogs and branch restriction — independent of the
match score, so students can still see "almost eligible" recommendations.

---

## Notes & Next Steps

- Passwords are hashed with `bcrypt`; never stored in plaintext.
- To reset the database, drop and recreate it, then restart the app (tables
  are recreated automatically) — or `docker compose down -v` for the Docker setup.
- Resume uploads are simplified to a URL field (`resume_link`) so the demo has
  no dependency on file storage; swap in S3/Cloud Storage for real file uploads.
- Extend `models.py` + `matching.py` similarly if you want to add weighted
  fields such as certifications or prior internship experience to the score.
