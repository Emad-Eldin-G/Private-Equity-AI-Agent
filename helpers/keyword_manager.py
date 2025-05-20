import json
from typing import Dict, List, Set
from pathlib import Path


class KeywordManager:
    def __init__(self, file_path: str = "data/suspicious_keywords.json"):
        self.file_path = Path(file_path)
        self.keywords: Dict = {}
        self.patterns: List[Dict] = []
        self.load_keywords()

    def load_keywords(self) -> None:
        """Load keywords and patterns from JSON file."""
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                self.keywords = data["keywords"]
                self.patterns = data["patterns"]
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize with default values if file doesn't exist
            self.keywords = {}
            self.patterns = []
            self.save_keywords()

    def save_keywords(self) -> None:
        """Save keywords and patterns to JSON file."""
        data = {
            "keywords": self.keywords,
            "patterns": self.patterns
        }
        with open(self.file_path, "w") as f:
            json.dump(data, indent=4, fp=f)

    def get_all_keywords(self) -> Set[str]:
        """Get all keywords as a flat set."""
        keywords = set()
        for category in self.keywords.values():
            keywords.update(category["examples"])
        return keywords

    def get_all_patterns(self) -> List[str]:
        """Get all patterns as a list."""
        return [p["pattern"] for p in self.patterns]

    def add_keyword(self, category: str, keyword: str,
                   description: str = None) -> None:
        """Add a new keyword to a category."""
        if category not in self.keywords:
            self.keywords[category] = {
                "category": "medium_risk",
                "description": description or 
                    f"Keywords related to {category}",
                "examples": []
            }
        if keyword not in self.keywords[category]["examples"]:
            self.keywords[category]["examples"].append(keyword)
            self.save_keywords()

    def add_pattern(self, pattern: str, description: str) -> None:
        """Add a new pattern."""
        if not any(p["pattern"] == pattern for p in self.patterns):
            self.patterns.append({
                "pattern": pattern,
                "description": description
            })
            self.save_keywords()

    def remove_keyword(self, category: str, keyword: str) -> None:
        """Remove a keyword from a category."""
        if category in self.keywords:
            if keyword in self.keywords[category]["examples"]:
                self.keywords[category]["examples"].remove(keyword)
                self.save_keywords()

    def remove_pattern(self, pattern: str) -> None:
        """Remove a pattern."""
        self.patterns = [p for p in self.patterns if p["pattern"] != pattern]
        self.save_keywords()

    def update_from_feedback(self, feedback_text: str) -> None:
        """Update keywords and patterns based on feedback text."""
        # This is a simple implementation - you might want to use NLP
        # or other techniques to extract new keywords/patterns
        words = feedback_text.lower().split()
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                self.add_keyword(
                    "feedback", 
                    word,
                    f"Added from feedback: {feedback_text[:50]}..."
                ) 