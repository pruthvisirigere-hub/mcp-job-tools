"""SQLite job-application database: schema, seed data, and tool logic.

This module is the "business logic" layer. The MCP server (server.py) is a
thin wrapper around these functions, and the tests call them directly.
Keeping the logic here (not inside the MCP handlers) is what makes it
testable without starting a server.
"""

import json
import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL,
    industry TEXT,
    location TEXT,
    website TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id),
    job_title TEXT NOT NULL,
    location TEXT,
    employment_type TEXT,
    work_mode TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    job_url TEXT,
    date_posted TEXT,
    status TEXT NOT NULL DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS applications (
    application_id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(job_id),
    application_date TEXT,
    status TEXT NOT NULL DEFAULT 'applied',
    source TEXT,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS interviews (
    interview_id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id),
    interview_date TEXT,
    interview_type TEXT,
    interviewer_name TEXT,
    result TEXT,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL REFERENCES jobs(job_id),
    skill_id INTEGER NOT NULL REFERENCES skills(skill_id),
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE IF NOT EXISTS user_skills (
    skill_id INTEGER PRIMARY KEY REFERENCES skills(skill_id),
    level TEXT NOT NULL DEFAULT 'intermediate'
);
"""

COMPANIES = [
    (1, "NovaMind AI", "Artificial Intelligence", "New York, NY", "https://novamind.ai"),
    (2, "Lumen Health", "HealthTech", "Boston, MA", "https://lumenhealth.com"),
    (3, "QuantBridge", "FinTech", "Chicago, IL", "https://quantbridge.io"),
    (4, "Orbital Robotics", "Robotics", "Austin, TX", "https://orbitalrobotics.com"),
    (5, "ClearPath Analytics", "Data Analytics", "Remote", "https://clearpath.io"),
    (6, "Vertex Labs", "AI Infrastructure", "San Francisco, CA", "https://vertexlabs.dev"),
]

JOBS = [
    # (job_id, company_id, title, location, type, work_mode, sal_min, sal_max, url, posted, status)
    (1, 1, "Junior AI Engineer", "New York, NY", "Full-time", "Hybrid", 85000, 110000,
     "https://novamind.ai/careers/junior-ai-engineer", "2026-11-10", "open"),
    (2, 1, "Machine Learning Engineer", "New York, NY", "Full-time", "Hybrid", 110000, 140000,
     "https://novamind.ai/careers/ml-engineer", "2026-11-05", "open"),
    (3, 2, "AI Engineer, Clinical NLP", "Boston, MA", "Full-time", "On-site", 95000, 125000,
     "https://lumenhealth.com/careers/ai-nlp", "2026-11-12", "open"),
    (4, 3, "Junior Data Scientist", "Chicago, IL", "Full-time", "Hybrid", 80000, 105000,
     "https://quantbridge.io/careers/junior-data-scientist", "2026-11-08", "open"),
    (5, 4, "Robotics Software Engineer", "Austin, TX", "Full-time", "On-site", 100000, 130000,
     "https://orbitalrobotics.com/careers/robotics-swe", "2026-11-02", "closed"),
    (6, 5, "Data Analyst", "Remote", "Full-time", "Remote", 70000, 90000,
     "https://clearpath.io/careers/data-analyst", "2026-11-15", "open"),
    (7, 6, "ML Platform Engineer", "San Francisco, CA", "Full-time", "Hybrid", 120000, 150000,
     "https://vertexlabs.dev/careers/ml-platform", "2026-11-09", "open"),
    (8, 6, "Junior Generative AI Engineer", "San Francisco, CA", "Full-time", "Remote", 90000, 120000,
     "https://vertexlabs.dev/careers/gen-ai-engineer", "2026-11-14", "open"),
    (9, 2, "Data Engineer", "Boston, MA", "Full-time", "Hybrid", 95000, 120000,
     "https://lumenhealth.com/careers/data-engineer", "2026-11-06", "open"),
    (10, 3, "Quantitative Research Analyst", "Chicago, IL", "Full-time", "On-site", 90000, 115000,
     "https://quantbridge.io/careers/quant-analyst", "2026-11-01", "closed"),
]

APPLICATIONS = [
    # (app_id, job_id, date, status, source, notes)
    (1, 1, "2026-11-12", "interviewing", "Company careers page", "Recruiter reached out on LinkedIn first."),
    (2, 3, "2026-11-13", "applied", "Greenhouse", "Tailored resume to NLP focus."),
    (3, 8, "2026-11-15", "applied", "Lever", "Used CodeRAG project as the headline bullet."),
    (4, 4, "2026-11-11", "rejected", "Company careers page", "Rejected after resume screen."),
    (5, 6, "2026-11-16", "offer", "Indeed", "Offer received, deciding."),
    (6, 2, "2026-11-10", "applied", "Company careers page", ""),
    (7, 9, "2026-11-14", "interviewing", "Referral", "Referred by a former classmate."),
    (8, 7, "2026-11-17", "applied", "LinkedIn", "Hiring manager viewed my profile."),
]

INTERVIEWS = [
    # (interview_id, app_id, date, type, interviewer, result, notes)
    (1, 1, "2026-11-18", "Phone screen", "Priya Nair", "passed", "30 min, walked through CodeRAG."),
    (2, 1, "2026-11-20", "Technical", "Daniel Kim", "pending", "Live coding: RAG retrieval question."),
    (3, 5, "2026-11-19", "Final round", "Sarah Lee", "passed", "SQL + case study, went well."),
    (4, 7, "2026-11-19", "Phone screen", "Marcus Chen", "passed", "Asked about ViDAR project."),
    (5, 7, "2026-11-21", "Technical", "Elena Ruiz", "pending", "System design: data pipeline."),
]

SKILLS = [
    (1, "Python"), (2, "SQL"), (3, "Machine Learning"), (4, "PyTorch"),
    (5, "TensorFlow"), (6, "LangChain"), (7, "RAG"), (8, "Docker"),
    (9, "AWS"), (10, "FastAPI"), (11, "NLP"), (12, "Vector Databases"),
]

JOB_SKILLS = [
    (1, 1), (1, 3), (1, 6), (1, 7), (1, 12),            # Junior AI Engineer
    (2, 1), (2, 3), (2, 4), (2, 5), (2, 8),            # ML Engineer
    (3, 1), (3, 3), (3, 11), (3, 6), (3, 7),           # Clinical NLP
    (4, 1), (4, 2), (4, 3),                             # Junior Data Scientist
    (5, 1), (5, 4), (5, 8),                             # Robotics SWE
    (6, 1), (6, 2),                                   # Data Analyst
    (7, 1), (7, 8), (7, 9), (7, 10),                    # ML Platform Engineer
    (8, 1), (8, 3), (8, 6), (8, 7), (8, 10),           # Gen AI Engineer
    (9, 1), (9, 2), (9, 8), (9, 9),                    # Data Engineer
    (10, 1), (10, 2), (10, 3),                         # Quant Analyst
]

USER_SKILLS = [
    (1, "advanced"), (2, "intermediate"), (3, "intermediate"), (4, "beginner"),
    (7, "intermediate"), (8, "beginner"), (10, "beginner"),
]


def get_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DEFAULT_DB_PATH):
    """Create tables and seed sample data. Safe to call repeatedly:
    seeding only happens when the companies table is empty."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 0:
            conn.executemany("INSERT INTO companies VALUES (?, ?, ?, ?, ?)", COMPANIES)
            conn.executemany("INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", JOBS)
            conn.executemany("INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?)", APPLICATIONS)
            conn.executemany("INSERT INTO interviews VALUES (?, ?, ?, ?, ?, ?, ?)", INTERVIEWS)
            conn.executemany("INSERT INTO skills VALUES (?, ?)", SKILLS)
            conn.executemany("INSERT INTO job_skills VALUES (?, ?)", JOB_SKILLS)
            conn.executemany("INSERT INTO user_skills VALUES (?, ?)", USER_SKILLS)
            conn.commit()
    finally:
        conn.close()


def _row_to_dict(row):
    return dict(row) if row is not None else None


def search_jobs(db_path=DEFAULT_DB_PATH, keyword="", status=""):
    """Search jobs by keyword (title/company/location) and/or status.

    Both filters are optional. Returns a list of dicts, each with the
    company name joined in.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        query = """
            SELECT j.job_id, j.job_title, j.location, j.employment_type,
                   j.work_mode, j.salary_min, j.salary_max, j.date_posted,
                   j.status, c.company_name, c.industry
            FROM jobs j JOIN companies c ON c.company_id = j.company_id
            WHERE 1 = 1
        """
        params = []
        if keyword:
            query += " AND (j.job_title LIKE ? OR c.company_name LIKE ? OR j.location LIKE ?)"
            like = f"%{keyword}%"
            params.extend([like, like, like])
        if status:
            query += " AND j.status = ?"
            params.append(status)
        query += " ORDER BY j.date_posted DESC"
        rows = conn.execute(query, params).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_application(db_path=DEFAULT_DB_PATH, application_id=0):
    """Full lifecycle for one application: company -> job -> application
    -> interviews. Raises ValueError for an unknown application id."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        app = conn.execute(
            "SELECT * FROM applications WHERE application_id = ?", (application_id,)
        ).fetchone()
        if app is None:
            raise ValueError(f"No application with id {application_id}")
        app = _row_to_dict(app)
        job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (app["job_id"],)).fetchone()
        job = _row_to_dict(job)
        company = conn.execute(
            "SELECT * FROM companies WHERE company_id = ?", (job["company_id"],)
        ).fetchone()
        interviews = conn.execute(
            "SELECT * FROM interviews WHERE application_id = ? ORDER BY interview_date",
            (application_id,),
        ).fetchall()
        return {
            "company": _row_to_dict(company),
            "job": job,
            "application": app,
            "interviews": [_row_to_dict(i) for i in interviews],
        }
    finally:
        conn.close()


def add_note(db_path=DEFAULT_DB_PATH, application_id=0, note=""):
    """Append a note to an application (keeps old notes, adds a new line).
    Returns the updated application row. Raises ValueError for unknown id."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        app = conn.execute(
            "SELECT * FROM applications WHERE application_id = ?", (application_id,)
        ).fetchone()
        if app is None:
            raise ValueError(f"No application with id {application_id}")
        existing = app["notes"] or ""
        updated = (existing + "\n" + note).strip() if existing else note
        conn.execute(
            "UPDATE applications SET notes = ? WHERE application_id = ?",
            (updated, application_id),
        )
        conn.commit()
        app = conn.execute(
            "SELECT * FROM applications WHERE application_id = ?", (application_id,)
        ).fetchone()
        return _row_to_dict(app)
    finally:
        conn.close()


def skill_gap(db_path=DEFAULT_DB_PATH, job_id=0):
    """Compare the skills a job needs with the user's recorded skills.

    Returns the job, the required skills, the skills the user has,
    the missing skills, and a coverage percentage.
    Raises ValueError for an unknown job id (a clean error, not a crash).
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if job is None:
            raise ValueError(f"No job with id {job_id}")
        required = conn.execute(
            """SELECT s.skill_id, s.skill_name FROM skills s
               JOIN job_skills js ON js.skill_id = s.skill_id
               WHERE js.job_id = ? ORDER BY s.skill_name""",
            (job_id,),
        ).fetchall()
        required_names = [r["skill_name"] for r in required]
        have = conn.execute(
            """SELECT s.skill_name, us.level FROM skills s
               JOIN user_skills us ON us.skill_id = s.skill_id
               ORDER BY s.skill_name"""
        ).fetchall()
        have_map = {r["skill_name"]: r["level"] for r in have}
        have_names = [n for n in required_names if n in have_map]
        missing = [n for n in required_names if n not in have_map]
        coverage = round(100 * len(have_names) / len(required_names), 1) if required_names else 100.0
        return {
            "job": _row_to_dict(job),
            "required_skills": required_names,
            "have_skills": [{"skill": n, "level": have_map[n]} for n in have_names],
            "missing_skills": missing,
            "coverage_percent": coverage,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DEFAULT_DB_PATH}")
    print(f"Jobs seeded: {len(search_jobs())}")
    print(json.dumps(skill_gap(job_id=1), indent=2))
