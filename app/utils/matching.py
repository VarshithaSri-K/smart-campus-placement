"""
Candidate <-> Job compatibility scoring.

The final match score (0-100) is a weighted blend of three signals:

  1. Skill overlap (60%)  - how many of the job's required skills the
     student has, weighted by the student's self-rated proficiency
     (1=beginner, 2=intermediate, 3=advanced).
  2. Academic strength (25%) - normalized CGPA relative to a 10-point scale,
     with a small bonus for having zero backlogs.
  3. Branch fit (15%) - full marks if the job has no branch restriction or
     the student's branch is explicitly allowed, otherwise 0.

Eligibility (a hard gate, independent of the score) is computed separately
via `is_eligible()` and checks minimum CGPA, backlog ceiling and branch
restriction. A student can only apply to a job they are eligible for, but
the match score is still useful for ranking/recommendations even for jobs
they are not yet eligible for (e.g. "almost eligible" suggestions).
"""

SKILL_WEIGHT = 0.60
CGPA_WEIGHT = 0.25
BRANCH_WEIGHT = 0.15


def _skill_score(student_skills, required_skills):
    """
    student_skills: list of {"name": str, "proficiency": int(1-3)}
    required_skills: list[str] (already lowercased)
    Returns 0-100.
    """
    if not required_skills:
        # No specific skills required -> neutral full score
        return 100.0

    skill_map = {s["name"].lower(): s.get("proficiency", 2) for s in student_skills}

    total_weight = 0.0
    matched_weight = 0.0
    for req in required_skills:
        total_weight += 3.0  # max possible proficiency
        if req in skill_map:
            matched_weight += skill_map[req]

    if total_weight == 0:
        return 100.0
    return round((matched_weight / total_weight) * 100, 2)


def _cgpa_score(cgpa, backlogs):
    base = max(0.0, min(10.0, cgpa or 0.0)) / 10.0 * 100
    penalty = min(backlogs or 0, 5) * 4  # each backlog trims a little
    return round(max(0.0, base - penalty), 2)


def _branch_score(student_branch, allowed_branches):
    if not allowed_branches:
        return 100.0
    return 100.0 if (student_branch or "").strip().lower() in allowed_branches else 0.0


def compute_match_score(student, job):
    """
    student: models.Student instance
    job: models.Job instance
    Returns float 0-100 rounded to 2 decimals.
    """
    student_skills = [{"name": s.skill.name, "proficiency": s.proficiency} for s in student.skills]
    required_skills = job.skill_list()
    allowed_branches = job.branch_list()

    s_score = _skill_score(student_skills, required_skills)
    c_score = _cgpa_score(student.cgpa, student.backlogs)
    b_score = _branch_score(student.branch, allowed_branches)

    final = (s_score * SKILL_WEIGHT) + (c_score * CGPA_WEIGHT) + (b_score * BRANCH_WEIGHT)
    return round(final, 2)


def is_eligible(student, job):
    """Hard eligibility gate used before allowing an application."""
    if job.status != "open":
        return False, "This job posting is closed."
    if (student.cgpa or 0) < (job.min_cgpa or 0):
        return False, f"Minimum CGPA required is {job.min_cgpa}."
    if (student.backlogs or 0) > (job.max_backlogs or 0):
        return False, f"Maximum allowed backlogs is {job.max_backlogs}."
    allowed = job.branch_list()
    if allowed and (student.branch or "").strip().lower() not in allowed:
        return False, "Your branch is not eligible for this job."
    return True, "Eligible"


def rank_jobs_for_student(student, jobs):
    """
    Given a student and a list of Job objects, return a list of
    {job, score, eligible, reason} sorted by score descending.
    """
    results = []
    for job in jobs:
        score = compute_match_score(student, job)
        eligible, reason = is_eligible(student, job)
        results.append({"job": job, "score": score, "eligible": eligible, "reason": reason})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def rank_students_for_job(job, students):
    """Given a job and a list of Student objects, rank candidates by score."""
    results = []
    for student in students:
        score = compute_match_score(student, job)
        eligible, reason = is_eligible(student, job)
        results.append({"student": student, "score": score, "eligible": eligible, "reason": reason})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results
