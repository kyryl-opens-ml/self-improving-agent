# Loan Underwriting Agent — Improvement Plan (from Logfire Trace Analysis)

## Context

Analyzed 10 Loan Underwriting Agent traces from Logfire (2026-03-29 18:47–18:48). The agent runs on `claude-sonnet-4-6` via PydanticAI with 2 tools (`calc_dti`, `credit_risk`) and a one-sentence system prompt. The eval suite uses 10 edge-case loan applications designed to stress-test boundary conditions.

**Core finding**: A tool bug causes systematic DTI under-estimation, and the under-specified prompt lets the LLM fill gaps with hallucinated rules, inconsistent math, and contradictory outputs.

---

## Bugs Found in Traces

### Critical: `calc_dti` tool doesn't include the proposed loan payment
- **Docstring says**: "Calculate debt-to-income ratio including the proposed loan"
- **Implementation does**: Only divides `total_debt` by income — completely ignores `loan_amount`
- **Impact**: Every DTI reported is artificially low. Cases 1, 3, 6, 10 were APPROVED when true post-loan DTI is 60–90%

### Critical: Case 6 — approved=true contradicts its own reasoning
- Agent calculated post-loan DTI = 64.8% > 45% max, recommended $139,700 max
- But structured output: `approved: true, max_loan: 150000`

### Critical: Case 10 — approved $750k loan with ~90% true post-loan DTI
- DTI tool returned 39.5% (existing debt only), agent approved
- Real post-loan DTI: (3950+5093)/10000 = 90.4%

### Bug: Case 9 — max_loan=$0 for qualifying applicant
- Zero debt, $6,250/mo income, 30% DTI cap = $1,875/mo capacity
- Agent returned max_loan=0, hallucinated "minimum score 580-620" rule

### Inconsistency: monthly_payment varies wildly
- Case 1: $3,750 (existing monthly debt, not loan payment)
- Case 3: $1,580 (correct 30yr amortization)
- Case 8: $97 (5yr term assumed)
- Case 10: $3,950 (existing monthly debt again)

### Inconsistency: max_loan methodology
- Sometimes the requested amount, sometimes a rough guess, sometimes $0

---

## What Works Well
- Both tools called in parallel (efficient, single LLM round-trip)
- Credit tier classification always correct
- Denial decisions on obviously bad cases (2, 4, 5, 7) are correct
- Token usage reasonable (~1,835 in / 233–536 out per run)
- No errors, no retries, no wasted tool calls

---

## Changes

### 1. Add helper functions (agent.py)

Two pure functions extracted from tool logic:

- `_get_rate(score) -> (tier, max_dti_pct, rate_pct)` — shared by all tools, eliminates duplicated tier logic
- `_monthly_payment(principal, annual_rate, years=30) -> float` — standard amortization formula

### 2. Fix `calc_dti` tool (agent.py:34)

Rewrite to include proposed loan payment:
- Use `_get_rate` to get the interest rate for this applicant
- Use `_monthly_payment` to compute proposed loan payment
- Return: existing debt, proposed payment, total monthly debt, post-loan DTI, max DTI for tier

### 3. Add `calc_max_loan` tool (agent.py, new)

Reverse amortization: given remaining DTI capacity, compute max affordable principal. Eliminates LLM guesswork for `max_loan` field.

### 4. Simplify `credit_risk` tool (agent.py:42)

Use `_get_rate` helper. Functionally identical output but no duplicated tier thresholds.

### 5. Expand system prompt (agent.py:30)

Replace one-sentence prompt with explicit rules:
1. Call ALL tools before deciding
2. APPROVE only if post-loan DTI <= max DTI for tier
3. Set max_loan from `calc_max_loan` tool, not your own estimate
4. Set monthly_payment to the proposed loan payment from `calc_dti`, not existing debt
5. All loans are 30-year fixed rate
6. Do not invent rules not listed here
7. Reasoning must be consistent with structured output fields

### 6. Add `post_loan_dti` field to `UnderwritingDecision` (agent.py:19)

Makes DTI auditable in structured output. Enables programmatic cross-check.

### 7. Add `validate_decision()` function (agent.py, new)

Post-hoc validation: checks monthly_payment matches amortization, checks approved vs DTI consistency. Called in `main()` and `eval.py` — safety net for any remaining LLM errors.

### 8. Add expected outcomes to cases.json

Add `expected_approved` field. With corrected DTI that includes loan payments, 9/10 cases should be DENIED (only Case 8 — trivial $5k loan — should approve).

### 9. Update eval.py for pass/fail reporting

Compare `decision.approved` against `expected_approved`, call `validate_decision()`, print pass/fail.

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/agent/agent.py` | Fix calc_dti, add calc_max_loan, add helpers, expand prompt, add post_loan_dti field, add validate_decision |
| `src/agent/cases.json` | Add expected_approved to each case |
| `src/agent/eval.py` | Add pass/fail checking and validation |

## Verification

1. Run `uv run agent-eval` — all 10 cases should produce correct approve/deny decisions
2. Check Logfire traces — new tool outputs should contain post-loan DTI, proposed payment, max loan
3. Verify Case 8 approved, Cases 1-7 and 9-10 denied
4. Verify no `validate_decision` warnings on any case
