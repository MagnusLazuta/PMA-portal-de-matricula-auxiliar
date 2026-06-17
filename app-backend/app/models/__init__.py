from ..database import Base
from .user import User, Student, Admin, COMGRAD
from .course import Course, CourseWishlist, course_prerequisite
from .class_entity import ClassSection, ClassSchedule
from .completed_course import CompletedCourse
from .restriction import TimeRestriction
from .poll import ClassRequestPoll, PollVote
from .curriculum import Curriculum, CurriculumCourse

# Ensure Base is accessible if needed, although it comes from database.py
# The main point is to import all models here so that metadata knows about them.

__all__ = [
    "Base",
    "User",
    "Student",
    "Admin",
    "COMGRAD",
    "Course",
    "CourseWishlist",
    "course_prerequisite",
    "ClassSection",
    "ClassSchedule",
    "CompletedCourse",
    "TimeRestriction",
    "ClassRequestPoll",
    "PollVote",
    "Curriculum",
    "CurriculumCourse",
]
