from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)

    offerings = relationship("Offering", back_populates="course")
    students = relationship("Student", secondary="student_desired_courses", back_populates="desired_courses")

class Offering(Base):
    __tablename__ = "offerings"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    day_of_week = Column(String)
    start_time = Column(String)
    end_time = Column(String)

    course = relationship("Course", back_populates="offerings")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    desired_courses = relationship("Course", secondary="student_desired_courses", back_populates="students")

class StudentDesiredCourse(Base):
    __tablename__ = "student_desired_courses"

    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)

class Restriction(Base):
    __tablename__ = "restrictions"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(String)
    start_time = Column(String)
    end_time = Column(String)