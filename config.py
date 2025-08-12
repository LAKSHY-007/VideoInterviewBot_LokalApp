from typing import Dict, Any

class Parameters:
    # Model settings
    MODEL: str = "gemini-1.5-pro-latest"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1000

    # Default job info
    DEFAULT_JOB_TITLE: str = "Technical Expert / Data Scientist"
    DEFAULT_JOB_DESCRIPTION: str = """
        TASKS:
        - Develop and implement ML/AI models
        - Focus on NLP or Computer Vision
        - Work with data scientists and subject experts
        - Evaluate use cases and consult on analytics
        - Support projects from idea to deployment

        QUALIFICATIONS:
        - Master's in CS, Math, Physics, or related with ML/AI focus
        - 3+ years implementing ML/AI models
        - Strong in current ML methods, especially LLMs
        - Skilled in Python and cloud platforms
        - Knowledge of NLP and/or CV
        - Problem-solving and analytical mindset
        - Fluent in English
    """

    # Prompt templates
    INTRODUCTION_PROMPT: str = """
        Create a friendly, professional intro for a video interview for the {job_title} position.
        The role requires: {job_description}
        Return only the introduction text.
        Example: "Welcome to your interview for [position]. We'll ask about [key skills]."
    """

    QUESTIONS_PROMPT: str = """
        Generate {num_questions} interview questions for {job_title}.
        Requirements: {job_description}

        Rules:
        1. Return as a JSON array of strings
        2. Include one behavioral and one technical question
        3. Keep each question under 25 words
        4. Focus on role-specific skills

        Example: ["How would you approach...?", "Describe a time when..."]
    """

    EVALUATION_PROMPT: str = """
        Analyze the responses for {job_title}.
        Return a markdown report with:

        ### Technical Skills Assessment
        - Relevance: /10
        - Depth: /10
        - Strengths: [list]
        - Weaknesses: [list]

        ### Problem-Solving
        - Approach: /10
        - Creativity: /10
        - Examples: [list]

        ### Recommendation
        - Fit: Strong / Potential / Not
        - Next Steps: [suggestions]

        Job Requirements: {job_description}
        Interview Responses: {interview_text}
    """

    TRANSCRIPTION_PROMPT: str = """
        Review this interview transcript:
        {transcript_text}

        Return JSON with:
        - technical_skills: [list]
        - knowledge_gaps: [list]
        - communication_style: [description]
        - confidence_score: 1-10
        - red_flags: [list or null]
    """

    # UI and defaults
    DEFAULT_NUM_QUESTIONS: int = 5
    MAX_QUESTIONS: int = 10
    MIN_QUESTIONS: int = 3

    RESPONSE_TYPES: Dict[str, str] = {
        "text": "Written Response",
        "video": "Video Response"
    }

    EVALUATION_CRITERIA: Dict[str, Any] = {
        "technical_skills": {
            "weight": 0.4,
            "description": "Depth and relevance of technical knowledge"
        },
        "problem_solving": {
            "weight": 0.3,
            "description": "Analytical and creative thinking"
        },
        "communication": {
            "weight": 0.2,
            "description": "Clarity and professionalism"
        },
        "culture_fit": {
            "weight": 0.1,
            "description": "Alignment with company values"
        }
    }

    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        return {
            "model": cls.MODEL,
            "temperature": cls.TEMPERATURE,
            "max_output_tokens": cls.MAX_TOKENS,
            "top_p": 1,
            "top_k": 40
        }
