"""server.py: the MCP wrapper. Two tools, stdio.

    claude mcp add org-knowledge -e QDRANT_URL=... -e QDRANT_API_KEY=... -- org-knowledge-mcp
"""
import json

from mcp.server.fastmcp import FastMCP

from . import core

mcp = FastMCP("org-knowledge")


@mcp.tool()
def ask(question: str, source: str = "") -> str:
    """Evidence for a question about the company's product, customers and support history, from its
    own sources. Each line starts with the [id] to cite. Leave `source` empty to hear from every
    lane, or name one (docs, field, tickets) to stay inside it."""
    return core.ask(question, source)


@mcp.tool()
def check(claims: list[dict]) -> str:
    """Check an answer before giving it. Each claim is {"text", "source_id", "quote"}: the sentence
    you want to say, the [id] it rests on, and the words from that line that support it. Returns
    which claims are sourced and why the rest are not. Drop or fix every rejected claim."""
    return json.dumps(core.check(claims), indent=1)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
