import json
import sys
from pathlib import Path

from agent.agent import LoanApplication, agent


def main():
    cases = json.loads((Path(__file__).parent / "cases.json").read_text())
    n = min(int(sys.argv[1]) if len(sys.argv) > 1 else len(cases), len(cases))
    print(f"Running {n}/{len(cases)} cases\n")

    for i, case in enumerate(cases[:n]):
        app = LoanApplication(case["annual_income"], case["total_debt"], case["credit_score"], case["loan_amount"])
        print(f"--- Case {i+1}: {case['description']}")
        print(f"    Income: ${app.annual_income:,.0f} | Debt: ${app.total_debt:,.0f} | Score: {app.credit_score} | Loan: ${app.loan_amount:,.0f}")
        result = agent.run_sync(f"Evaluate this loan application for ${app.loan_amount:,.0f}", deps=app)
        d = result.output
        status = "APPROVED" if d.approved else "DENIED"
        print(f"    -> {status} | Max: ${d.max_loan:,.0f} | Payment: ${d.monthly_payment:,.0f}/mo")
        print(f"    Reasoning: {d.reasoning}\n")


if __name__ == "__main__":
    main()
