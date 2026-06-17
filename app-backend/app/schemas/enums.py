from enum import Enum

class DayOfWeek(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class RestrictionType(str, Enum):
    HARD_BLOCK = "hard_block"
    PREFERRED_WINDOW = "preferred_window"
    PROFESSOR_PREFERENCE = "professor_preference"
    COURSE_IMPORTANCE = "course_importance"


class CourseImportanceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
