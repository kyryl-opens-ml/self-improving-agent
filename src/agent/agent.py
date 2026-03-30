import sys
from dataclasses import dataclass
import logfire
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv
load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

@dataclass
class LoanApplication:
    annual_income: float
    total_debt: float
    credit_score: int
    loan_amount: float

class UnderwritingDecision(BaseModel):
    approved: bool
    max_loan: float
    monthly_payment: float
    reasoning: str

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    deps_type=LoanApplication,
    output_type=UnderwritingDecision,
    instrument=True,
    instructions="You are a loan underwriter. Use the provided tools to assess the applicant, then make a decision.",
)

@agent.tool
def calc_dti(ctx: RunContext[LoanApplication]) -> str:
    """Calculate debt-to-income ratio including the proposed loan."""
    monthly_income = ctx.deps.annual_income / 12
    monthly_debt = ctx.deps.total_debt / 12
    dti = (monthly_debt / monthly_income) * 100
    return f"DTI: {dti:.1f}% (monthly debt: ${monthly_debt:,.0f}, monthly income: ${monthly_income:,.0f})"

@agent.tool
def credit_risk(ctx: RunContext[LoanApplication]) -> str:
    """Look up credit risk category and max DTI allowed."""
    score = ctx.deps.credit_score
    if score >= 740: return f"Score {score}: Excellent. Max DTI: 45%. Rate: 6.5%"
    if score >= 670: return f"Score {score}: Good. Max DTI: 40%. Rate: 7.2%"
    if score >= 580: return f"Score {score}: Fair. Max DTI: 36%. Rate: 9.1%"
    return f"Score {score}: Poor. Max DTI: 30%. Rate: 12.5%"

def main():
    if len(sys.argv) != 5:
        print("Usage: uv run python -m agent.agent <income> <debt> <credit_score> <loan_amount>")
        sys.exit(1)
    app = LoanApplication(float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]))
    result = agent.run_sync(f"Evaluate this loan application for ${app.loan_amount:,.0f}", deps=app)
    print(result.output.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
