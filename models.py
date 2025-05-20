from typing import Optional, List, Set
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


class Questionnaire(BaseModel):
    questionnaire_id: str
    investor_name: str
    investor_address: Optional[str] = None
    investment_amount: Optional[float] = None
    is_accredited_investor: bool
    accreditation_details: str
    source_of_funds_description: str
    tax_id_provided: bool
    signature_present: bool
    submission_date: str
    investor_type: Optional[str] = None


class Response(BaseModel):
    questionnaire_id: str
    decision: str
    missing_fields: Optional[list[str]] = None
    escalation_reason: Optional[str] = None


class Feedback(BaseModel):
    questionnaire: Questionnaire
    wrong_decision: str
    reasoning: str
    correct_decision: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def to_prompt_string(self) -> str:
        """Convert feedback to a string format suitable for prompting."""
        return (
            f"Previous Decision: {self.wrong_decision}\n"
            f"Correct Decision: {self.correct_decision}\n"
            f"Reasoning: {self.reasoning}\n"
            f"Questionnaire Details:\n"
            f"- Investor: {self.questionnaire.investor_name}\n"
            f"- Accreditation: {self.questionnaire.accreditation_details}\n"
            f"- Source of Funds: {self.questionnaire.source_of_funds_description}\n"
            f"- Investment Amount: {self.questionnaire.investment_amount}\n"
            f"- Accredited: {self.questionnaire.is_accredited_investor}\n"
            f"- Tax ID Provided: {self.questionnaire.tax_id_provided}\n"
            f"- Signature Present: {self.questionnaire.signature_present}\n"
        )


@dataclass
class Config:
    model_path: Path = Path("text_classifier.pkl")
    response_path: Path = Path("response.json")
    feedback_path: Path = Path("data/feedback.json")
    learning_path: Path = Path("learning_data.json")
    min_investment_amount: float = 0.0
    required_fields: List[str] = field(default_factory=lambda: [
        "investor_name",
        "investor_address",
        "investment_amount",
        "is_accredited_investor",
        "signature_present",
        "tax_id_provided"
    ])
    # Dynamic lists that can be updated based on feedback
    suspicious_keywords: Set[str] = field(default_factory=lambda: {
        "gambling", "crypto", "cryptocurrency", "gift",
        "offshore", "tbd", "undisclosed", "pending",
        "maybe", "perhaps", "possibly", "undetermined",
        "to be determined", "tbd", "pending review",
        "under review", "in progress", "not specified",
        "various", "including", "family contributions",
        "black market", "undisclosed source", "private",
        "confidential", "secret", "anonymous"
    })
    suspicious_patterns: List[str] = field(default_factory=lambda: [
        r'\?',  # Question marks
        r'\.{3,}',  # Ellipsis
        r'undisclosed',  # Undisclosed information
        r'pending',  # Pending status
        r'to be determined',  # TBD variations
        r'not specified',  # Missing information
        r'various sources',  # Vague sources
        r'including',  # Incomplete information
        r'black market',  # Illegal activities
        r'confidential',  # Hidden information
    ]) 