from pydantic import BaseModel, Field


class BehaviourRecordCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)
    course_id: str = Field(..., min_length=1, max_length=50)
    sequence: int = Field(..., ge=1, le=8)

    freq_course_view: int = Field(..., ge=0)
    freq_forum_consume: int = Field(..., ge=0)
    freq_forum_contribute: int = Field(..., ge=0)
    freq_lecture_view: int = Field(..., ge=0)

    regularity_course_view: float = Field(..., ge=0, le=1)
    regularity_lecture_view: float = Field(..., ge=0, le=1)
    regularity_forum_consume: float = Field(..., ge=0, le=1)
    regularity_forum_contribute: float = Field(..., ge=0, le=1)

    session_count: int = Field(..., ge=0)
    total_duration: int = Field(..., ge=0)
    active_days: int = Field(..., ge=0)

    final_grade: float | None = Field(None, ge=0, le=100)