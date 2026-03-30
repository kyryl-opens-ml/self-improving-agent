# Plan: Hard Test Cases + Eval CLI

## Context
Stress-test the loan underwriting agent with edge cases that expose LLM reasoning failures. The agent's `calc_dti` tool computes DTI from existing debt only (not including the new loan), and `credit_risk` maps scores to tiers at boundaries 740/670/580. Hard cases exploit these boundaries, conflicting signals, and absurd loan-to-income ratios.

## Files to create

### 1. `src/agent/cases.json` — 10 hard cases

Each case has `description`, `annual_income`, `total_debt`, `credit_score`, `loan_amount`.

| # | What makes it hard | Income | Debt | Score | Loan |
|---|---|---|---|---|---|
| 1 | DTI exactly at 45% max for Excellent tier | 100k | 45k | 745 | 300k |
| 2 | DTI 45.1%, just over Excellent cap — tiny overshoot LLM might round away | 100k | 45.1k | 750 | 280k |
| 3 | Score exactly 740 (Excellent boundary), DTI 42% — tier classification matters | 100k | 42k | 740 | 250k |
| 4 | Score 739 (Good tier), same DTI 42% — one point flips the outcome vs case 3 | 100k | 42k | 739 | 250k |
| 5 | $500k income, score 520 (Poor). DTI 5% is fine, credit is terrible — conflicting signals | 500k | 25k | 520 | 800k |
| 6 | Score 790, but $28k income. DTI 7% passes, but $150k loan is 5.4x income — affordability test | 28k | 2k | 790 | 150k |
| 7 | Loan is 44x income ($2M on $45k) with passing DTI (20%). Tools show green, common sense says no | 45k | 9k | 700 | 2M |
| 8 | Perfect profile, zero debt, tiny $5k loan — trivial approve, tests zero-debt edge | 200k | 0 | 800 | 5k |
| 9 | Score 579 (one below Fair → Poor), zero debt, $300k loan at punitive 12.5% rate | 75k | 0 | 579 | 300k |
| 10 | Triple borderline: score exactly 670, DTI 39.5% (just under 40% max), loan 6.2x income | 120k | 47.4k | 670 | 750k |

### 2. `src/agent/eval.py` — Eval CLI (~25 lines)

- Loads `cases.json` from `Path(__file__).parent`
- Accepts optional `sys.argv[1]` for number of cases to run (default: all)
- Imports `LoanApplication` and `agent` from `agent.agent`
- Runs each case with `agent.run_sync()`, prints inputs + decision summary
- Exposes `main()` for the `agent-eval` entry point in pyproject.toml

## No files modified
- `agent.py` — unchanged
- `pyproject.toml` — already has `agent-eval = "agent.eval:main"` and `cases.json` package-data

## Verification
```bash
uv run agent-eval 3      # run first 3 cases
uv run agent-eval        # run all 10
```
