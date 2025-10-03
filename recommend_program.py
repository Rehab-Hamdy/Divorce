# recommend_program.py
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME
import os, json

# Ensure API key exists
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) not set. Put it in .env.")

genai.configure(api_key=GEMINI_API_KEY)


def call_gemini_recommend(domains: dict, modules: dict):
    """
    Send risks + modules to Gemini and get structured program in markdown table.
    
    Args:
        domains (dict): {"communication": 0.7, "affection": 0.2, ...}
                       (0 = no risk, 1 = highest risk)
        modules (dict): {"communication": ["active listening", "weekly check-in"], ...}

    Returns:
        str: A structured 4-week program in Markdown table format.
    """

    # Explain the meaning of the values for LLM clarity
    risk_explanation = """
    - Each domain has a risk score between 0.0 and 1.0
      • 0.0 = No risk (healthy domain)
      • 0.3 = Mild concern
      • 0.5 = Moderate concern
      • 0.7 = High concern
      • 1.0 = Very high risk (critical domain)
    - Your task: Focus the 4-week plan on the highest risk domains first,
      while also strengthening medium and low risk areas.
    """

    prompt = f"""
    You are a professional couples therapist. 
    A couple completed a risk questionnaire, and here are the results.

    Risks per domain (0.0 = no risk, 1.0 = highest risk):
    {json.dumps(domains, indent=2)}

    Suggested intervention modules per domain:
    {json.dumps(modules, indent=2)}

    {risk_explanation}

    Please create a **4-week improvement program** in a Markdown table format with these columns:
    - Week
    - Domain Focus
    - Exercises / Tasks (at least 2 per week, drawn from suggested modules or creative new ones)

    Notes:
    - The program must cover the most critical domains (highest risks) first.
    - Use simple, supportive, and practical language.
    - Balance emotional connection, communication, and conflict resolution.
    """

    model = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text.strip()


