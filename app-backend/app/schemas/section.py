from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from .schedule import ClassScheduleCreate, ClassScheduleResponse

class ClassSectionBase(BaseModel):
    course_id: int
    section_code: str
    semester: str
    capacity: int
    professor_name: Optional[str] = None

class ClassSectionCreate(ClassSectionBase):
    schedules: List[ClassScheduleCreate]

class ClassSectionResponse(ClassSectionBase):
    id: int
    schedules: List[ClassScheduleResponse]

    model_config = ConfigDict(from_attributes=True)
