from __future__ import annotations as _annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from models import Questionnaire, Response

load_dotenv()


@dataclass
class Deps:
    questionnaire: Questionnaire
    response_path: Path = Path("data/response.json")
    min_investment_amount: float = 0.0
    required_fields: List[str] = field(default_factory=lambda: [
        "investor_name",
        "investor_address",
        "investment_amount",
        "is_accredited_investor",
        "signature_present",
        "tax_id_provided"
    ])
    suspicious_keywords: List[str] = field(default_factory=list)
    suspicious_patterns: List[Dict] = field(default_factory=list)


def load_suspicious_terms() -> tuple[List[str], List[Dict]]:
    """Load suspicious keywords and patterns from JSON file."""
    try:
        with open("data/suspicious_keywords.json", "r") as f:
            data = json.load(f)
            return data["keywords"], data["patterns"]
    except (FileNotFoundError, json.JSONDecodeError):
        return [], []


questionnaire_agent = Agent(
    'openai:gpt-4o',  # Using gpt-4o as the base model to run the agent
    instructions=(
        'You are an AI agent responsible for reviewing private equity fund subscription '
        'questionnaires. Use the available tools to check for missing '
        'fields, analyze text for concerning/ambigous terms, and make a final '
        'decision of Approved, Return or Escalate. Be thorough in your analysis.'
    ),
    deps_type=Deps,
    retries=2,
)


@questionnaire_agent.tool
async def basic_review(ctx: RunContext[Deps]) -> List[str]:
    """Check for required fields and perform basic validations."""
    q = ctx.deps.questionnaire
    missing_fields = []
    
    print("\nChecking required fields...")
    
    for field_name in ctx.deps.required_fields:
        value = getattr(q, field_name)
        if field_name in ["tax_id_provided", "signature_present"]:
            if not value:  # Check if boolean is False
                missing_fields.append(field_name)
                print(f"Missing {field_name}")
        elif value is None or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field_name)
            print(f"Missing {field_name}")
        elif field_name == "investment_amount" and (
            not value or value <= ctx.deps.min_investment_amount
        ):
            missing_fields.append(field_name)
            print(f"Invalid {field_name}: {value}")
    
    print(f"Found {len(missing_fields)} missing fields")
    
    return missing_fields


@questionnaire_agent.tool
async def ambiguity_checker(ctx: RunContext[Deps]) -> Optional[str]:
    """Analyze text fields for ambiguity and concerning terms."""
    q = ctx.deps.questionnaire
    text = (
        f"{q.accreditation_details} {q.source_of_funds_description}"
    ).lower()
    
    print("\nChecking for suspicious terms...")
    
    # Check for suspicious keywords with word boundaries
    for kw in ctx.deps.suspicious_keywords:
        # Use word boundaries to match whole words only
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            print(f"Found suspicious keyword: {kw}")
            return "Ambiguous source of funds"
    
    # Check for suspicious patterns
    for pattern in ctx.deps.suspicious_patterns:
        if re.search(pattern["pattern"], text, re.IGNORECASE):
            print(f"Found suspicious pattern: {pattern['description']}")
            return "Ambiguous source of funds"
    
    # Check for negative accreditation
    if "does not meet" in text:
        print("Found negative accreditation statement")
        return "Investor is not accredited"
    
    print("No suspicious terms found")
    return None


@questionnaire_agent.tool
async def decision_maker(ctx: RunContext[Deps]) -> str:
    """Determine the final decision based on review and ambiguity."""
    q = ctx.deps.questionnaire
    
    print("\nMaking final decision...")
    
    missing = await basic_review(ctx)

    if missing:
        print("Decision: Return (missing fields)")
        return "Return"

    if (not q.investment_amount or 
            q.investment_amount < ctx.deps.min_investment_amount):
        print("Decision: Return (invalid investment amount)")
        return "Return"

    if not q.is_accredited_investor:
        print("Decision: Escalate (not accredited)")
        return "Escalate"

    # Check for obvious issues
    ambiguity = await ambiguity_checker(ctx)
    if ambiguity:
        print(f"Decision: Escalate ({ambiguity})")
        return "Escalate"

    print("Decision: Approve (all checks passed)")
    return "Approve"


async def process_questionnaire(questionnaire: Questionnaire) -> Response:
    """Process a questionnaire and return a response."""
    # Load suspicious terms
    keywords, patterns = load_suspicious_terms()
    
    deps = Deps(
        questionnaire=questionnaire,
        suspicious_keywords=keywords,
        suspicious_patterns=patterns
    )
    
    # Run the agent with the prompt template questionnaire
    await questionnaire_agent.run(
        f"""Review this investment questionnaire:
        - Investor Name: {questionnaire.investor_name}
        - Investment Amount: {questionnaire.investment_amount}
        - Accreditation Status: {
            'Accredited' if questionnaire.is_accredited_investor 
            else 'Not Accredited'
        }
        - Accreditation Details: {questionnaire.accreditation_details}
        - Source of Funds: {questionnaire.source_of_funds_description}
        - Tax ID Provided: {questionnaire.tax_id_provided}
        - Signature Present: {questionnaire.signature_present}
        \n
        Use the tools to check for issues and make a decision (Approve, Return or Escalate).
        """,
        deps=deps
    )
    
    # Create a context for tool calls using the agent's model
    tool_ctx = RunContext(
        deps=deps,
        model=questionnaire_agent.model,
        usage={},
        prompt=""
    )
    
    # Get the decision and reasons
    decision = await decision_maker(tool_ctx)
    missing_fields = await basic_review(tool_ctx)
    
    # Only get escalation reason if decision is Escalate
    escalation_reason = None
    if decision == "Escalate":
        escalation_reason = await ambiguity_checker(tool_ctx)
    
    # Create response with all fields
    response = Response(
        questionnaire_id=questionnaire.questionnaire_id,
        decision=decision,
        missing_fields=missing_fields,
        escalation_reason=escalation_reason
    )
    
    # Load existing responses
    try:
        with open(deps.response_path, "r") as f:
            content = f.read().strip()
            responses = json.loads(content) if content else []
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize an empty reponse array if repsonse.json is uncreated
        responses = []
    
    # Convert to dict and format for output
    response_dict = response.model_dump()
    # Set missing_fields to null if empty
    if not response_dict["missing_fields"]:
        response_dict["missing_fields"] = None
    # Only include escalation_reason for Escalate decisions
    if decision != "Escalate":
        response_dict["escalation_reason"] = None
    
    responses.append(response_dict)
    
    # Save updated responses
    with open(deps.response_path, "w") as f:
        json.dump(responses, indent=2, fp=f)    
    return response
