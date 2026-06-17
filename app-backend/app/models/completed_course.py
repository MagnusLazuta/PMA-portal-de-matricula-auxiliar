from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base

class CompletedCourse(Base):
    __tablename__ = "completed_course"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.user_id"))
    course_id = Column(Integer, ForeignKey("course.id"))

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="_student_course_completed_uc"),)

    student = relationship("Student", back_populates="completed_courses")
    course = relationship("Course", back_populates="completed_by")
