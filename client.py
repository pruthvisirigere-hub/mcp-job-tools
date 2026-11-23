"""MCP client: starts the server over stdio, lists its tools, and calls two.

Run with:  python client.py
No API key needed. The client spawns `server.py` as a subprocess and talks
to it with JSON-RPC over stdin/stdout (the stdio transport).
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _text(result) -> str:
    """Pull the plain-text payload out of a CallToolResult."""
    return "\n".join(block.text for block in result.content if hasattr(block, "text"))


async def main() -> None:
    server_path = Path(__file__).with_name("server.py")
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        env=None,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("== Tools exposed by the server ==")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description.splitlines()[0]}")

            print("\n== search_jobs(keyword='AI', status='open') ==")
            result = await session.call_tool(
                "search_jobs", {"keyword": "AI", "status": "open"}
            )
            jobs = json.loads(_text(result))
            for job in jobs:
                print(
                    f"  [{job['job_id']}] {job['job_title']} @ {job['company_name']} "
                    f"({job['location']}) — ${job['salary_min']:,}-${job['salary_max']:,} — {job['status']}"
                )

            print("\n== skill_gap(job_id=1) — Junior AI Engineer @ NovaMind AI ==")
            result = await session.call_tool("skill_gap", {"job_id": 1})
            gap = json.loads(_text(result))
            print(f"  Required: {', '.join(gap['required_skills'])}")
            print("  Have: " + ", ".join(
                f"{s['skill']} ({s['level']})" for s in gap["have_skills"]
            ))
            print(f"  Missing: {', '.join(gap['missing_skills']) or 'none'}")
            print(f"  Coverage: {gap['coverage_percent']}%")


if __name__ == "__main__":
    asyncio.run(main())
