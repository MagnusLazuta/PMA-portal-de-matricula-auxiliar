from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional
from datetime import time
from .enums import CourseImportanceLevel, DayOfWeek, RestrictionType

class TimeRestrictionBase(BaseModel):
    student_id: int = 1
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None
    restriction_type: RestrictionType = RestrictionType.HARD_BLOCK
    course_id: Optional[int] = None
    preferred_professor: Optional[str] = None
    preference_order: Optional[int] = None
    importance_level: Optional[CourseImportanceLevel] = None
    score_weight: Optional[int] = None
    is_mandatory: Optional[bool] = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.restriction_type in {
            RestrictionType.HARD_BLOCK,
            RestrictionType.PREFERRED_WINDOW,
        }:
            if self.day_of_week is None or self.start_time is None or self.end_time is None:
                raise ValueError(
                    "day_of_week, start_time and end_time are required for time-based restrictions"
                )

        if self.restriction_type == RestrictionType.PROFESSOR_PREFERENCE:
            if self.course_id is None or not self.preferred_professor:
                raise ValueError(
                    "course_id and preferred_professor are required for professor preferences"
                )

        if self.restriction_type == RestrictionType.COURSE_IMPORTANCE:
            if self.course_id is None or self.importance_level is None:
                raise ValueError(
                    "course_id and importance_level are required for course importance preferences"
                )

        return self

class TimeRestrictionCreate(TimeRestrictionBase):
    pass

class TimeRestrictionResponse(TimeRestrictionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
