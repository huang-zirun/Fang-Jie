from pydantic import BaseModel, field_validator


class ReportCreate(BaseModel):
    play_count: int
    comment_count: int
    message_count: int

    @field_validator("play_count", "comment_count", "message_count")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v

    @field_validator("play_count")
    @classmethod
    def validate_play_count_max(cls, v: int) -> int:
        if v > 100000000:
            raise ValueError("Play count exceeds maximum")
        return v


class DiagnosisOut(BaseModel):
    problem_type: str
    problem_desc: str
    optimization_direction: str
    optimization_detail: str
    ai_analysis: str | None = None
    rule_confidence: float | None = None
    snapshot_count: int = 0
    days_since_deploy: int = 0
    play_trend: str | None = None
    avg_daily_play_growth: float = 0.0

    model_config = {"from_attributes": True, "extra": "ignore"}


class ReportResponse(BaseModel):
    diagnosis: DiagnosisOut
