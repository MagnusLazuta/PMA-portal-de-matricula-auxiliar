from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from .enums import CourseImportanceLevel

class CourseBase(BaseModel):
    code: str
    name: str
    credits: int
    min_credits_required: int

class CourseCreate(CourseBase):
    prerequisite_ids: Optional[List[int]] = None

class CourseShortResponse(CourseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CourseResponse(CourseBase):
    id: int
    prerequisites: List[CourseShortResponse] = []
    semester: Optional[int] = None
    mandatory: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class CurriculumResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class StudentDesiredCoursesUpdate(BaseModel):
    course_ids: List[int]


class CoursePriorityPreference(BaseModel):
    course_id: int
    importance_level: CourseImportanceLevel
