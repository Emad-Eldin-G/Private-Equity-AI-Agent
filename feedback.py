from __future__ import annotations as _annotations
from dotenv import load_dotenv

import json
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from pydantic_ai import Agent, RunContext

load_dotenv()


@dataclass
class FeedbackDeps:
    keywords_file: Path = Path("data/suspicious_keywords.json")
    current_keywords: List[str] = field(default_factory=list)
    current_patterns: List[Dict] = field(default_factory=list)


feedback_agent = Agent(
    'openai:gpt-4',
    instructions=(
        'You are an AI agent responsible for reviewing investment questionnaires. '
        'You analyze questionnaires and make decisions based on missing fields, '
        'suspicious patterns, and accreditation status. '
        'Your decisions should be: Approve, Return, or Escalate.'
    ),
    deps_type=FeedbackDeps,
    retries=2,
)


@feedback_agent.tool
async def load_current_data(ctx: RunContext[FeedbackDeps]) -> Dict:
    """Load current keywords and patterns from JSON file."""
    try:
        with open(ctx.deps.keywords_file, "r") as f:
            data = json.load(f)
            ctx.deps.current_keywords = data["keywords"]
            ctx.deps.current_patterns = data["patterns"]
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"keywords": [], "patterns": []}


@feedback_agent.tool
async def add_keyword(ctx: RunContext[FeedbackDeps], keyword: str) -> None:
    """Add a new keyword to the list."""
    if keyword not in ctx.deps.current_keywords:
        ctx.deps.current_keywords.append(keyword)
        # Save updated keywords
        with open(ctx.deps.keywords_file, "r+") as f:
            data = json.load(f)
            data["keywords"] = ctx.deps.current_keywords
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()


@feedback_agent.tool
async def add_pattern(
    ctx: RunContext[FeedbackDeps], 
    pattern: str, 
    description: str
) -> None:
    """Add a new pattern with description."""
    new_pattern = {"pattern": pattern, "description": description}
    if new_pattern not in ctx.deps.current_patterns:
        ctx.deps.current_patterns.append(new_pattern)
        # Save updated patterns
        with open(ctx.deps.keywords_file, "r+") as f:
            data = json.load(f)
            data["patterns"] = ctx.deps.current_patterns
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()


def main():
    deps = FeedbackDeps()
    ctx = RunContext(
        deps=deps,
        model=feedback_agent.model,
        usage={},
        prompt=""
    )
    
    # Load initial data
    asyncio.run(load_current_data(ctx))
    
    # Example: Add a new keyword
    asyncio.run(add_keyword(ctx, "suspicious_transfer"))
    
    # Example: Add a new pattern
    asyncio.run(add_pattern(
        ctx,
        "\\b(?:unusual|suspicious)\\s+activity\\b",
        "References to suspicious activity"
    ))
    
    print("\nUpdated suspicious terms:")
    print("\nKeywords:")
    for kw in ctx.deps.current_keywords:
        print(f"- {kw}")
    
    print("\nPatterns:")
    for pattern in ctx.deps.current_patterns:
        print(f"- {pattern['pattern']}: {pattern['description']}")


if __name__ == "__main__":
    main() 