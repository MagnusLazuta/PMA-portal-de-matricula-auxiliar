from pydantic import BaseModel
from typing import List, Optional
from .schedule import ClassScheduleResponse

class ScheduleRequest(BaseModel):
    student_id: int
    limit: int = 5
    semester: Optional[str] = None

class ScheduleItem(BaseModel):
    section_id: int
    section_code: str
    course_name: str
    course_code: str
    professor_name: Optional[str] = None
    schedules: List[ClassScheduleResponse]


class RankedScheduleOption(BaseModel):
    score: float
    selected_course_count: int
    total_course_priority: int
    matched_preference_count: int
    schedule: List[ScheduleItem]
