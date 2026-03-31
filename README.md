# Self-Improving Agent

A Claude Code plugin that analyzes PydanticAI agent traces from Logfire to find bugs, inefficiencies, and propose improvements.

Read the full story: [Blog post](https://kyrylai.com/2026/03/30/self-improving-agent/) | [README.blog.md](README.blog.md)

## Install

**1. Add the marketplace and install the plugin:**

```
/plugin marketplace add https://github.com/kyryl-opens-ml/self-improving-agent.git#marketplace
/plugin install self-improving-agent@koml-self-improving-agent
/reload-plugins
```

**2. Add the [Logfire MCP server](https://logfire.pydantic.dev/docs/integrations/mcp/):**

```
claude mcp add logfire --transport http https://logfire-us.pydantic.dev/mcp
```

## Skill: `/analyze-agent-traces-logfire`

Analyzes your agent's Logfire traces and produces a report with:

- **Bugs** — wrong outputs, hallucinated values, tool misuse
- **Inefficiencies** — wasted tokens, redundant calls, slow traces
- **Fixes** — concrete code/prompt changes, prioritized P0-P2

Usage:

```
/self-improving-agent:analyze-agent-traces-logfire 24 hours
/self-improving-agent:analyze-agent-traces-logfire 7 days
```
