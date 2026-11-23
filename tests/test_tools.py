"""Tests for the job-tools database logic (db.py).

The tool functions are tested directly — no MCP server is started here.
Each test gets a fresh, isolated database in tmp_path.
"""

import pytest

import db


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "test_jobs.db")
    db.init_db(path)
    return path


def test_seed_data_loads_correctly(db_path):
    jobs = db.search_jobs(db_path)
    assert len(jobs) == 10
    conn = db.get_connection(db_path)
    assert conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 6
    assert conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0] == 8
    assert conn.execute("SELECT COUNT(*) FROM interviews").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0] == 12
    conn.close()


def test_search_jobs_by_keyword(db_path):
    results = db.search_jobs(db_path, keyword="AI")
    assert len(results) >= 2
    assert all(
        "ai" in (r["job_title"] + r["company_name"]).lower() for r in results
    )
    titles = [r["job_title"] for r in results]
    assert "Junior AI Engineer" in titles


def test_search_jobs_by_status(db_path):
    closed = db.search_jobs(db_path, status="closed")
    assert len(closed) == 2
    assert all(r["status"] == "closed" for r in closed)
    open_jobs = db.search_jobs(db_path, status="open")
    assert len(open_jobs) == 8


def test_get_application_returns_full_lifecycle(db_path):
    result = db.get_application(db_path, application_id=1)
    assert result["company"]["company_name"] == "NovaMind AI"
    assert result["job"]["job_title"] == "Junior AI Engineer"
    assert result["application"]["status"] == "interviewing"
    assert len(result["interviews"]) == 2
    assert result["interviews"][0]["interviewer_name"] == "Priya Nair"


def test_add_note_persists(db_path):
    updated = db.add_note(db_path, application_id=2, note="Sent thank-you email.")
    assert "Sent thank-you email." in updated["notes"]
    # Read it back fresh from the database to prove it persisted.
    again = db.get_application(db_path, application_id=2)
    assert "Sent thank-you email." in again["application"]["notes"]


def test_skill_gap_math_is_correct(db_path):
    gap = db.skill_gap(db_path, job_id=1)
    # Job 1 needs: Python, Machine Learning, LangChain, RAG, Vector Databases
    assert gap["required_skills"] == [
        "LangChain", "Machine Learning", "Python", "RAG", "Vector Databases",
    ]
    # User has Python, Machine Learning, RAG — missing LangChain, Vector Databases
    assert [s["skill"] for s in gap["have_skills"]] == [
        "Machine Learning", "Python", "RAG",
    ]
    assert gap["missing_skills"] == ["LangChain", "Vector Databases"]
    assert gap["coverage_percent"] == 60.0


def test_unknown_job_id_returns_clean_error(db_path):
    with pytest.raises(ValueError, match="No job with id 999"):
        db.skill_gap(db_path, job_id=999)


def test_unknown_application_id_returns_clean_error(db_path):
    with pytest.raises(ValueError, match="No application with id 999"):
        db.get_application(db_path, application_id=999)
