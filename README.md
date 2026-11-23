# mcp-job-tools

An MCP server plus a small client, built on a SQLite job-application
database. The server exposes job-search tools over the Model Context
Protocol; the client starts the server over stdio and calls them.
No API key needed anywhere.

## What MCP is (in 3 lines)

MCP (Model Context Protocol) is an open standard for connecting an AI
application to external tools and data. A **server** exposes capabilities
(tools, resources, prompts); a **client** (or host, like Claude) discovers
them and calls them. The two sides talk JSON-RPC over a transport — here,
**stdio**, meaning the server is a subprocess and messages travel over
stdin/stdout.

## What the server exposes

| Tool | What it does |
| --- | --- |
| `search_jobs(keyword, status)` | Search jobs by keyword and/or status (`open` / `closed`) |
| `get_application(application_id)` | Full lifecycle: company → job → application → interviews |
| `add_note(application_id, note)` | Append a note to an application |
| `skill_gap(job_id)` | Skills the job needs vs the user's recorded skills, with coverage % |

The database is seeded with realistic sample data: 6 companies, 10 jobs,
8 applications, 5 interviews, 12 skills.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the server (stdio)

```bash
python server.py
```

It reads JSON-RPC on stdin and writes replies on stdout. It is meant to
be started by a client, not used directly.

## Run the client

```bash
python client.py
```

The client spawns the server, lists its tools, then calls `search_jobs`
and `skill_gap` and prints the results.

## Example output

```
== Tools exposed by the server ==
  - search_jobs: Search jobs by keyword (title, company, or location) and/or status
  - get_application: Full lifecycle of one application: company -> job -> application
  - add_note: Append a note to an application. Returns the updated application.
  - skill_gap: Skills a job needs vs skills recorded for the user, with a

== search_jobs(keyword='AI', status='open') ==
  [8] Junior Generative AI Engineer @ Vertex Labs (San Francisco, CA) — $90,000-$120,000 — open
  [3] AI Engineer, Clinical NLP @ Lumen Health (Boston, MA) — $95,000-$125,000 — open
  [1] Junior AI Engineer @ NovaMind AI (New York, NY) — $85,000-$110,000 — open
  [2] Machine Learning Engineer @ NovaMind AI (New York, NY) — $110,000-$140,000 — open

== skill_gap(job_id=1) — Junior AI Engineer @ NovaMind AI ==
  Required: LangChain, Machine Learning, Python, RAG, Vector Databases
  Have: Machine Learning (intermediate), Python (advanced), RAG (intermediate)
  Missing: LangChain, Vector Databases
  Coverage: 60.0%
```

## Tests

```bash
pytest -v
```

8 tests: seed data loads, keyword/status search, full application
lifecycle, note persistence, skill-gap math, and clean errors for
unknown job/application ids.

## Project layout

```
mcp-job-tools/
├── server.py          # MCP server (FastMCP, stdio transport)
├── client.py          # MCP client (spawns server, lists + calls tools)
├── db.py              # SQLite schema, seed data, tool logic
├── tests/
│   └── test_tools.py  # pytest tests for db.py
├── conftest.py        # makes db.py importable from tests
├── requirements.txt   # mcp SDK + pytest
├── README.md
└── STUDY.md           # picture-first explainer + interview questions
```

## Notes

- The database file `jobs.db` is created on first run (seeded
  automatically) and is git-ignored — every clone starts from the same
  seed data. Set `JOB_DB=/path/to/file.db` to use a different file.
- Unknown ids return a JSON `{"error": ...}` from the server (and raise a
  `ValueError` from the db layer) — never a crash.
