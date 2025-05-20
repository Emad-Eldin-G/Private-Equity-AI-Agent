# **Private Equity** Fund Subscription Processing

## AI Agent Workflow

1. **Questionnaire Submission**
   - System receives a questionnaire with investor details
   - The inputted details are translated into a Pydantic model
  
2. **Basic Review**
   - Checks for missing required fields
   - Validates investment amount against minimum threshold
   - Verifies tax ID and signature presence
   - If any of the above is not present, it is added to a missing_fields list to be used in the output
  
3. **Risk Analysis**
   - Analyzes source of funds description
   - Checks for suspicious/ambigous keywords and patterns
   - Evaluates accreditation details (true or false)
   - If any of the above fails the checks, it will result in an escalation, hence an escalation reason is added to the output
  
4. **Decision Making**
   - **Approve**: All requirements met, no concerns
   - **Return**: Missing required fields or invalid information
   - **Escalate**: Potential compliance issues or ambiguous information
   - The final ouput is translated into a Pydantic output model
   - Then translated into JSON
   - And finally added to the ouput response.json
  
5. **Feedback Loop**
   - Another simple AI Agent that takes input from user to improve the suspicious words list.
   - AI Agent learns translates user feedback into a single word or pattern to be added.
   - Updates suspicious terms database
   - Refines decision-making patterns


## How to Run Locally

1. **Setup Environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: source venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Create a `.env` file in the root directory
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

3. **Run the System**
   ```bash
   # To process questionnaires
   python agent.py

   # To update suspicious terms
   python feedback.py
   ```

4. **Data Structure**
   - Place questionnaires in `data/questionnaire.json`
   - Responses are stored in `data/response.json`
   - Suspicious terms are managed in `data/suspicious_keywords.json`  
