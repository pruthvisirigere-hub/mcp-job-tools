"""MCP server for the job-application tools.

Run with:  python server.py
Transport: stdio (the server reads JSON-RPC messages on stdin and writes
replies on stdout). No network port, no API key.

Tools exposed:
  - search_jobs(keyword, status)
  - get_application(application_id)
  - add_note(application_id, note)
  - skill_gap(job_id)

The server is a thin wrapper: every tool calls the matching function in
db.py and returns its result as a JSON string. All real logic lives in
db.py so it can be unit-tested without a server running.
"""

import json
import os

from mcp.server.fastmcp import FastMCP

import db

DB_PATH = os.environ.get("JOB_DB", db.DEFAULT_DB_PATH)

mcp = FastMCP("mcp-job-tools")


@mcp.tool()
def search_jobs(keyword: str = "", status: str = "") -> str:
    """Search jobs by keyword (title, company, or location) and/or status
    ('open' or 'closed'). Both filters are optional."""
    return json.dumps(db.search_jobs(DB_PATH, keyword=keyword, status=status), indent=2)


@mcp.tool()
def get_application(application_id: int) -> str:
    """Full lifecycle of one application: company -> job -> application
    -> interviews. Raises a clean error for an unknown id."""
    try:
        return json.dumps(db.get_application(DB_PATH, application_id), indent=2)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def add_note(application_id: int, note: str) -> str:
    """Append a note to an application. Returns the updated application."""
    try:
        return json.dumps(db.add_note(DB_PATH, application_id, note), indent=2)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def skill_gap(job_id: int) -> str:
    """Skills a job needs vs skills recorded for the user, with a
    coverage percentage. Raises a clean error for an unknown job id."""
    try:
        return json.dumps(db.skill_gap(DB_PATH, job_id), indent=2)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})


if __name__ == "__main__":
    db.init_db(DB_PATH)
    mcp.run(transport="stdio")
