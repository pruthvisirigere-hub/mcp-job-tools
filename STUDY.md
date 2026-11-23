# STUDY.md — Understanding mcp-job-tools (picture first)

## The big picture

You already have a job-application tracker as SQL files. This project
puts a **standard front door** on that same data so that any AI
application — Claude, an agent you build, a chatbot — can *use* the data
without knowing SQL and without you writing a custom API for every app.

That front door is **MCP, the Model Context Protocol**.

```
  ┌─────────────┐      JSON-RPC over stdio       ┌──────────────┐
  │   CLIENT     │  ──────────────────────────▶  │    SERVER     │
  │  client.py   │  "call search_jobs"           │   server.py   │
  │  (the app    │  ◀──────────────────────────  │  (FastMCP)    │
  │   asking)    │  "here are 3 jobs"            └──────┬───────┘
  └─────────────┘                                       │ Python calls
                                                        ▼
                                                 ┌──────────────┐
                                                 │    db.py      │
                                                 │  SQLite DB    │
                                                 │  jobs.db      │
                                                 └──────────────┘
```

Three layers, three jobs:
1. **Client** — decides *what* to ask. It knows nothing about SQL.
2. **Server** — exposes *tools* (named functions with a description and
   a schema). It knows nothing about SQLite.
3. **Database layer (`db.py`)** — runs the SQL. It knows nothing about
   MCP.

If you can explain those three layers and what crosses each boundary,
you can explain the whole project.

## The words, in plain English

- **MCP (Model Context Protocol)** — an open standard (from Anthropic)
  for connecting AI apps to tools and data. Think "USB-C for AI apps":
  one plug shape, many devices. Before MCP, every AI app needed a
  custom integration for every data source; MCP makes the integration
  reusable.
- **Protocol** — the agreed rules of the conversation: message shapes,
  who speaks when, how errors look. MCP messages are **JSON-RPC 2.0**
  (JSON objects with `method`, `params`, `id`, and `result`/`error`).
- **Server** — a program that *offers* capabilities. Ours offers 4
  tools. It does not decide anything; it waits for calls.
- **Client** — a program that *uses* capabilities. Ours starts the
  server, asks "what tools do you have?", then calls two of them.
- **Host** — the app the user actually talks to (Claude Desktop, an
  agent framework). The host owns the client. In our demo the client
  script plays both roles, so you can see the whole loop with no extra
  app.
- **Transport** — how the bytes move. Ours is **stdio**: the server is
  a subprocess, the client writes JSON-RPC to its stdin and reads
  replies from its stdout. No port, no HTTP, no network. (The other
  common transport is Streamable HTTP, for servers that run over a
  network.)
- **Tool** — a function a model/client can call: a name, a human
  description, and a JSON Schema describing its inputs. The model reads
  the description and decides *when* to call it.
- **Resource** — read-only data a server exposes (like a file or a
  document) that a client can fetch. Our server doesn't expose any —
  tools were the right shape here, because every operation is a
  *question* or an *action*, not a document.
- **Prompt** — a reusable, server-side prompt template. Also not used
  here, for the same reason.

## How one tool call flows, step by step

Example: the client calls `skill_gap` for job 1.

1. **Client** builds a JSON-RPC request:
   `{"method": "tools/call", "params": {"name": "skill_gap",
   "arguments": {"job_id": 1}}, "id": 7}` and writes it to the
   server's stdin.
2. **Server (FastMCP)** reads the line, validates the arguments
   against the tool's JSON Schema (is `job_id` an integer? yes),
   and calls the Python function `skill_gap(job_id=1)` in `server.py`.
3. **`server.py`** is a thin wrapper: it calls `db.skill_gap(...)`
   and converts the returned dict to a JSON string. No SQL here.
4. **`db.py`** runs two SQL queries: one joins `job_skills` to get
   the 5 skills job 1 needs; one reads `user_skills` for the user's
   7 skills. It computes the overlap in Python: have 3, missing 2,
   coverage 60.0%.
5. The dict travels back up: `db.py` → `server.py` → FastMCP wraps
   it in a JSON-RPC response → stdout → **client** reads it and
   prints it.
6. If the job doesn't exist, `db.py` raises `ValueError("No job
   with id 999")`. The server catches it and returns
   `{"error": "No job with id 999"}` — a *clean error the client
   can show*, not a crash and not a stack trace leaking internals.

Notice what each layer *doesn't* know: the client never sees SQL; the
database never sees JSON-RPC. That separation is the whole point, and
it's what makes the server reusable by any MCP client, not just ours.

## Why this shape (and not a REST API)?

- A REST API needs a port, HTTP, auth, and a client written for *your*
  API. An MCP server needs none of that: any MCP host can discover
  and call your tools with zero custom code.
- Tools are **self-describing**: the description + schema travel with
  the tool, so a model can decide to call `skill_gap` after seeing a
  job — no hard-coded endpoint list in the client.
- stdio keeps the demo honest: no server to deploy, no key to manage,
  and the data stays on your machine.

## What to say in an interview (one line each)

- "MCP is a standard protocol so AI apps can call external tools
  without a custom integration per data source."
- "My server exposes four tools over stdio; the client discovers them
  with `tools/list` and calls them with `tools/call`."
- "The server is a thin wrapper — all logic and SQL live in `db.py`,
  which is why I could unit-test every tool without starting a
  server."
- "Unknown ids return a clean JSON error, never a crash."

## 5 interview questions you should be able to answer

1. **What problem does MCP solve that a REST API doesn't?**
   (Hint: discovery + self-describing tools + no per-app custom
   integration. A REST API works, but every client must be written
   for your endpoints; an MCP client works with *any* MCP server.)
2. **What is the difference between a tool, a resource, and a prompt
   in MCP — and why does this project only use tools?**
   (Hint: tools *do* things / answer questions; resources expose
   read-only data; prompts are reusable templates. Our operations
   are questions and one write — tool-shaped, not document-shaped.)
3. **Walk me through a `skill_gap` call from the client to SQLite
   and back. What crosses each boundary?**
   (Hint: the 6-step flow above — JSON-RPC → schema validation →
   Python function → SQL queries → dict → JSON-RPC response.)
4. **Why stdio instead of HTTP for this server? What would change if
   you switched to Streamable HTTP?**
   (Hint: stdio = subprocess, no port, local-only, no auth needed;
   HTTP = network-accessible, needs auth, deployment, and a host
   that can reach it. The tools and `db.py` would not change at
   all — only the transport.)
5. **How do you handle a bad input, like `skill_gap` for a job id
   that doesn't exist — and why return an error object instead of
   raising?**
   (Hint: `db.py` raises `ValueError`; the server catches it and
   returns `{"error": ...}` so the client gets a usable message and
   the server stays alive. A crash would kill the server process
   for every client.)

## If you want to go deeper later

- Add a **resource** (e.g. `jobs://summary`) that returns the whole
  tracker as one document, and explain when resources beat tools.
- Add **Streamable HTTP** transport and run the server on a port.
- Add a `search_jobs` **prompt** template ("find me AI jobs I'm
  qualified for") and let the host fill it in.
- Point the same server at your real tracker data instead of the
  seed data.
