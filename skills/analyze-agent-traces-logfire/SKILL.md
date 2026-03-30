---
name: analyze-agent-traces-logfire
description: Analyze PydanticAI agent traces from Logfire to find bugs, inefficiencies, and propose improvements to prompt, tools, and flow. Use when asked to review agent behavior, debug agent issues, or improve agent quality.
argument-hint: "[time-range] e.g. '1 hour', '24 hours', '7 days' (default: 24 hours)"
---

# Analyze Agent Traces from Logfire

You are an expert AI agent debugger. Analyze traces from Pydantic Logfire to find bugs, inefficiencies, and propose concrete improvements.

**Time range**: $ARGUMENTS (default: "24 hours" if not specified)

---

## Phase 1: Discovery

First, understand what agents and spans exist in the time range.

### Step 1.1 — Get span shape

Run this query to understand what agent types and span patterns exist:

```sql
SELECT span_name, kind, COUNT(*) as cnt
FROM records
WHERE start_timestamp >= now() - INTERVAL '{time_range}'
GROUP BY span_name, kind
ORDER BY cnt DESC
LIMIT 30
```

### Step 1.2 — Get trace overview

```sql
SELECT
  trace_id,
  COUNT(*) as span_count,
  MIN(start_timestamp) as started,
  MAX(duration) as total_duration_s,
  SUM(CASE WHEN is_exception THEN 1 ELSE 0 END) as errors
FROM records
WHERE start_timestamp >= now() - INTERVAL '{time_range}'
GROUP BY trace_id
ORDER BY started ASC
LIMIT 100
```

### Step 1.3 — Check for errors/exceptions

```sql
SELECT trace_id, span_name, message, exception_type, exception_message, otel_status_code
FROM records
WHERE start_timestamp >= now() - INTERVAL '{time_range}'
  AND (is_exception = true OR otel_status_code = 'ERROR' OR level >= 40)
ORDER BY start_timestamp ASC
LIMIT 50
```

Run all three queries in parallel. From the results, identify:
- Which span_names correspond to agent runs, LLM calls, and tool calls
- How many traces exist and their rough shape
- Any hard errors

---

## Phase 2: Extract Agent Decisions

### Step 2.1 — Get full agent run data

Query for agent run spans which contain the complete conversation, final result, and token usage:

```sql
SELECT trace_id, span_name, message, duration, attributes
FROM records
WHERE start_timestamp >= now() - INTERVAL '{time_range}'
  AND span_name = 'agent run'
ORDER BY start_timestamp ASC
LIMIT 50
```

If results are too large, query in batches by trace_id.

### Step 2.2 — Get tool call details

```sql
SELECT trace_id, span_name, message, duration, attributes
FROM records
WHERE start_timestamp >= now() - INTERVAL '{time_range}'
  AND span_name = 'running tool'
ORDER BY start_timestamp ASC
LIMIT 200
```

From the agent run attributes, extract for each trace:
- `attributes.final_result` — the structured output
- `attributes.pydantic_ai.all_messages` — the full conversation (user prompt, tool calls, tool responses, final answer)
- `attributes.gen_ai.system_instructions` — the system prompt
- `attributes.gen_ai.usage.details.input_tokens` / `output_tokens` — token usage
- `attributes.logfire.metrics.operation.cost` — dollar cost

From tool calls, extract:
- `attributes.gen_ai.tool.name` — which tool was called
- `attributes.tool_arguments` — what arguments were passed
- `attributes.tool_response` — what the tool returned

---

## Phase 3: Read the Agent Source Code

Before analyzing, read the actual agent implementation to understand intent vs. behavior:

1. Look for Python files in the project that define the agent (search for `Agent(`, `@agent.tool`, `pydantic_ai`)
2. Read the agent file(s) to understand:
   - System prompt / instructions
   - Tool definitions and their implementations
   - Input/output schemas
   - Any validation logic

---

## Phase 4: Analyze Each Trace

For EVERY trace, systematically check:

### 4.1 Tool Usage Analysis
- Did the agent call all available tools? Any skipped?
- Were tools called in parallel or sequentially? (parallel is better)
- Were any tools called redundantly (same tool, same args, multiple times)?
- Did tool responses contain the data the agent needed?
- Are tool docstrings accurate? Does the implementation match what it claims?

### 4.2 Decision Correctness
- Does the structured output (final_result) match the agent's reasoning?
- Are numerical values in the output (amounts, percentages, scores) mathematically correct given the tool outputs?
- Did the agent follow its system prompt rules, or did it invent new ones?
- Did the agent hallucinate facts not present in tool outputs or system prompt?

### 4.3 Consistency Across Traces
- Are similar inputs producing similar outputs?
- Is the agent using consistent methodology across cases? (e.g., same formulas, same assumptions)
- Are there edge cases where behavior changes unexpectedly?

### 4.4 Efficiency
- Token usage per trace — any outliers?
- Number of LLM round-trips — could tool calls be batched better?
- Duration — any traces significantly slower than others? Why?
- Cost per trace — proportional to complexity?

---

## Phase 5: Generate Report

Structure your findings as follows:

### Bugs Found (ordered by severity)

For each bug:
- **What**: One-line description
- **Traces affected**: List trace_ids
- **Evidence**: Quote the specific tool output and agent decision that demonstrates the bug
- **Root cause**: Tool bug? Prompt gap? LLM reasoning error?
- **Fix**: Concrete code change or prompt addition

### Inefficiencies

For each inefficiency:
- **What**: Description
- **Impact**: Wasted tokens, extra latency, or cost
- **Fix**: How to improve

### Proposed Improvements

Organize into categories:

1. **Tool fixes** — bugs in tool implementations
2. **New tools** — deterministic computations the LLM is currently guessing at
3. **Prompt improvements** — missing rules, ambiguous instructions
4. **Schema changes** — fields to add/remove from input/output
5. **Flow changes** — reordering steps, adding validation
6. **Test cases** — new edge cases to add based on discovered failure modes

For each improvement, provide:
- The specific code change (show before/after for tool and prompt changes)
- Which traced bugs this fixes
- Priority: P0 (causes wrong outputs), P1 (inconsistent), P2 (nice to have)

### Summary Statistics

| Metric | Value |
|--------|-------|
| Traces analyzed | N |
| Errors/exceptions | N |
| Decision bugs found | N |
| Avg duration | Xs |
| Avg tokens (in/out) | N/N |
| Avg cost per run | $X |
| Total cost | $X |

---

## Important Rules

1. **Read the source code** before concluding a tool is buggy — compare implementation to docstring and actual behavior in traces.
2. **Check every trace** — don't sample. Bugs often hide in edge cases.
3. **Be specific** — quote exact values from traces. "monthly_payment was $3,750 but should be $1,896" not "monthly_payment was wrong".
4. **Distinguish tool bugs from LLM bugs** — a tool returning wrong data is different from the LLM misinterpreting correct data.
5. **Propose minimal fixes** — don't redesign the agent. Target the specific failure modes found in traces.
6. **Never hallucinate trace data** — only report what you actually queried and read from Logfire.
