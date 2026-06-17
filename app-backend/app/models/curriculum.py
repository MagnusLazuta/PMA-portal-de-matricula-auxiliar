from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..database import Base

class Curriculum(Base):
    __tablename__ = "curriculum"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # e.g., "Ciência da Computação", "Engenharia de Computação"

    # Relationships
    curriculum_courses = relationship("CurriculumCourse", back_populates="curriculum", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="curriculum_obj")

class CurriculumCourse(Base):
    __tablename__ = "curriculum_course"

    id = Column(Integer, primary_key=True, index=True)
    curriculum_id = Column(Integer, ForeignKey("curriculum.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    semester = Column(Integer, nullable=False)  # Stage (1 to N)
    mandatory = Column(Boolean, default=True)  # True = Mandatory, False = Elective

    curriculum = relationship("Curriculum", back_populates="curriculum_courses")
    course = relationship("Course")
