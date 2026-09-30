import anthropic

from .exceptions import InvalidResumeError, NonEnglishResumeError
from .models import HiringRecommendation, ResumeValidation
from .prompts import (
    EVALUATION_SYSTEM,
    EVALUATION_USER,
    VALIDATION_SYSTEM,
    VALIDATION_USER,
)

MODEL = "claude-opus-5-5"


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def validate_resume(resume_text: str) -> None:
    """Raise NonEnglishResumeError or InvalidResumeError if the resume fails validation."""
    client = _client()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=256,
        system=VALIDATION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": VALIDATION_USER.format(resume_text=resume_text[:8000]),
            }
        ],
        output_format=ResumeValidation,
    )
    result: ResumeValidation = response.parsed_output

    if not result.is_english:
        raise NonEnglishResumeError(
            result.issue or "The resume does not appear to be written in English."
        )
    if not result.is_valid_resume:
        raise InvalidResumeError(
            result.issue
            or "The uploaded document does not appear to be a valid resume. "
            "Please provide a document containing work experience, education, or skills."
        )


def evaluate(job_description: str, resume_text: str) -> HiringRecommendation:
    """Run the full evaluation and return a structured recommendation."""
    client = _client()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        system=EVALUATION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": EVALUATION_USER.format(
                    job_description=job_description,
                    resume_text=resume_text,
                ),
            }
        ],
        output_format=HiringRecommendation,
    )
    return response.parsed_output
