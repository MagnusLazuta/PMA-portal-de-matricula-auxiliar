from sqlalchemy import Boolean, Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class TimeRestriction(Base):
    __tablename__ = "time_restriction"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.user_id"))
    day_of_week = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    reason = Column(String)
    restriction_type = Column(String, default="hard_block")
    course_id = Column(Integer, ForeignKey("course.id"))
    preferred_professor = Column(String)
    preference_order = Column(Integer)
    importance_level = Column(String)
    score_weight = Column(Integer, default=0)
    is_mandatory = Column(Boolean, default=True)

    student = relationship("Student", back_populates="restrictions")
    course = relationship("Course")
