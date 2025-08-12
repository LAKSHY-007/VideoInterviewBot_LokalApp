import os
import re
import json
from typing import List, Dict, Optional, Union
from pathlib import Path

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

from config import Parameters


# --- Gemini Setup ---
try:
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in .env")

    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": Parameters.TEMPERATURE,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": Parameters.MAX_TOKENS,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=generation_config,
        safety_settings=safety_settings
    )

except Exception as e:
    print(f"Gemini init failed: {e}")
    raise


# --- Error Handling ---
class APIErrorHandler:
    ERRORS = {
        Exception: "Service unavailable. Try again later.",
        ValueError: "Invalid request. Check your input.",
        "quota_exceeded": "Request limit reached. Wait before retrying.",
        "safety_restriction": "Blocked by safety filters. Rephrase your request."
    }

    @classmethod
    def handle(cls, error: Exception) -> str:
        err_str = str(error).lower()
        if "quota" in err_str:
            return cls.ERRORS["quota_exceeded"]
        if "safety" in err_str:
            return cls.ERRORS["safety_restriction"]
        return cls.ERRORS.get(type(error), cls.ERRORS[Exception])


# --- Gemini Calls ---
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_completion(prompt: str, system_message: Optional[str] = None, **kwargs) -> str:
    try:
        full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
        response = model.generate_content(full_prompt)

        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        return "No response generated."

    except Exception as e:
        msg = APIErrorHandler.handle(e)
        print(f"API Error: {e}")
        return f"{msg} [Error Type: {type(e).__name__}]"


# --- Helpers ---
def get_questions(text_response: str) -> List[str]:
    """Pulls question list from AI text output."""
    try:
        # JSON format
        if text_response.strip().startswith('['):
            data = json.loads(text_response)
            if isinstance(data, list):
                return [q.strip() for q in data if q.strip()]

        # Numbered list
        numbered = re.findall(r'(?:\d+[.)]\s*)(.*?)(?=\n\s*\d+[.)]|$)', text_response, re.DOTALL)
        if numbered:
            return [q.strip() for q in numbered if q.strip()]

        # Markdown list
        dashed = re.findall(r'(?:[-*]\s*)(.*?)(?=\n\s*[-*]|$)', text_response, re.DOTALL)
        if dashed:
            return [q.strip() for q in dashed if q.strip()]

        # Fallback: split by line
        return [q.strip() for q in text_response.split('\n') if q.strip()]

    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Parse error: {e}")
        return ["Could not parse questions."]


def generate_evaluation_data(questions: List[str], answers: List[str], job_description: str) -> Dict:
    """Pairs Q&A for evaluation."""
    return {
        "job_description": job_description,
        "qa_pairs": [{"question": q, "answer": a} for q, a in zip(questions, answers)],
        "summary": f"Interview with {len(questions)} questions"
    }


def format_transcript(transcript: str) -> str:
    """Adds speaker labels and trims whitespace."""
    lines = []
    for line in transcript.split('\n'):
        if '>>' in line:
            speaker, text = line.split('>>', 1)
            lines.append(f"\n[Speaker {speaker.strip()}]: {text.strip()}")
        else:
            lines.append(line.strip())
    return '\n'.join(lines)


def _test_gemini_connection():
    try:
        result = get_completion("Hello world")
        print(f"Gemini connection OK. Sample: {result[:50]}...")
        return True
    except Exception as e:
        print(f"Gemini connection failed: {e}")
        return False


if __name__ == "__main__":
    _test_gemini_connection()
