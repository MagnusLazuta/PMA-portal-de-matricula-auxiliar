from sqlalchemy import Column, Integer, String, ForeignKey, Time
from sqlalchemy.orm import relationship
from ..database import Base

class ClassSection(Base):
    __tablename__ = "class_section"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"))
    section_code = Column(String)
    semester = Column(String)
    capacity = Column(Integer)
    professor_name = Column(String)

    course = relationship("Course", back_populates="sections")
    schedules = relationship("ClassSchedule", back_populates="section")


class ClassSchedule(Base):
    __tablename__ = "class_schedule"

    id = Column(Integer, primary_key=True, index=True)
    class_section_id = Column(Integer, ForeignKey("class_section.id"))
    day_of_week = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    room = Column(String)

    section = relationship("ClassSection", back_populates="schedules")
