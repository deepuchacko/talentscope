from typing import Literal, Optional
from pydantic import BaseModel, Field


class ReasonItem(BaseModel):
    label: str
    evidence: str
    signal: Literal["positive", "gap"]


class HiringRecommendation(BaseModel):
    recommendation: Literal["recommend", "hold", "reject"]
    confidence: float = Field(ge=0.0, le=1.0)
    must_have_coverage: float = Field(ge=0.0, le=1.0)
    reasons: list[ReasonItem]
    flags: list[Literal["low_confidence", "incomplete_data"]] = Field(default_factory=list)


class ResumeValidation(BaseModel):
    is_english: bool
    is_valid_resume: bool
    issue: Optional[str] = None
