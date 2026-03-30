# self-improving-agent# Self-Improving Agent

A Claude Code plugin that analyzes PydanticAI agent traces from Logfire to find bugs, inefficiencies, and propose improvements.

Read the full story: [README.blog.md](README.blog.md)

## Install

```
/plugin install github:koml/self-improving-agent
```

Requires the [Logfire MCP server](https://logfire.pydantic.dev/docs/integrations/mcp/) configured in your Claude Code settings.

## Skill: `/analyze-agent-traces-logfire`

Analyzes your agent's Logfire traces and produces a report with:

- **Bugs** — wrong outputs, hallucinated values, tool misuse
- **Inefficiencies** — wasted tokens, redundant calls, slow traces
- **Fixes** — concrete code/prompt changes, prioritized P0-P2

Usage:

```
/analyze-agent-traces-logfire 24 hours
/analyze-agent-traces-logfire 7 days
```
