import asyncio
import json
from pathlib import Path
from models import Questionnaire
from agent import process_questionnaire


def process_questionnaire_data(data: dict) -> None:
    """Process a questionnaire from dictionary data."""
    try:
        questionnaire = Questionnaire(**data)
        asyncio.run(process_questionnaire(questionnaire))
    except Exception as e:
        print(f"Error processing questionnaire: {str(e)}")


def main():
    # Load questionnaires from JSON file
    questionnaire_path = Path("data/questionnaire.json")
    try:
        with open(questionnaire_path, "r") as f:
            questionnaires = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {questionnaire_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {questionnaire_path}")
        return
    
    # Process each questionnaire
    for questionnaire_data in questionnaires:
        process_questionnaire_data(questionnaire_data)
    
    print(
        f"Processed {len(questionnaires)} questionnaires. \n"
        "Results saved to data/response.json"
    )


if __name__ == "__main__":
    main()