from typing import List
from sqlalchemy.orm import Session
from .crud import OfferingService, RestrictionService, StudentService

class ScheduleGenerator:
    def __init__(self, db: Session):
        self.offering_service = OfferingService(db)
        self.restriction_service = RestrictionService(db)
        self.student_service = StudentService(db)

    def _to_minutes(self, time_string: str) -> int:
        hours, minutes = map(int, time_string.split(":"))
        return hours * 60 + minutes

    def _normalize_day_of_week(self, value: object) -> str:
        if hasattr(value, "value"):
            return value.value

        if not isinstance(value, str):
            return str(value)

        normalized = value.strip().lower()
        legacy_values = {
            "seg": "Segunda-feira",
            "segunda": "Segunda-feira",
            "segunda-feira": "Segunda-feira",
            "ter": "Terça-feira",
            "terca": "Terça-feira",
            "terça": "Terça-feira",
            "terça-feira": "Terça-feira",
            "qua": "Quarta-feira",
            "quarta": "Quarta-feira",
            "quarta-feira": "Quarta-feira",
            "qui": "Quinta-feira",
            "quinta": "Quinta-feira",
            "quinta-feira": "Quinta-feira",
            "sex": "Sexta-feira",
            "sexta": "Sexta-feira",
            "sexta-feira": "Sexta-feira",
            "sab": "Sábado",
            "sabado": "Sábado",
            "sábado": "Sábado",
            "dom": "Domingo",
            "domingo": "Domingo",
        }
        return legacy_values.get(normalized, value)

    def _time_conflict(self, a, b) -> bool:
        if self._normalize_day_of_week(a.day_of_week) != self._normalize_day_of_week(b.day_of_week):
            return False

        start_a = self._to_minutes(a.start_time)
        end_a = self._to_minutes(a.end_time)
        start_b = self._to_minutes(b.start_time)
        end_b = self._to_minutes(b.end_time)

        return start_a < end_b and start_b < end_a

    def _offering_conflicts_restrictions(self, offering, restrictions) -> bool:
        return any(self._time_conflict(offering, restriction) for restriction in restrictions)

    def _offer_to_dict(self, offering: object) -> dict:
        course = offering.course
        return {
            "offering_id": offering.id,
            "course_id": offering.course_id,
            "course_name": course.name if course else "",
            "course_code": course.code if course else "",
            "day_of_week": self._normalize_day_of_week(offering.day_of_week),
            "start_time": offering.start_time,
            "end_time": offering.end_time,
        }

    def generate_possible_schedules(self, student_id: int) -> list[list[dict]]:
        student = self.student_service.get_student(student_id)
        if student is None:
            return []

        desired_course_ids = [course.id for course in student.desired_courses]
        if not desired_course_ids:
            return []

        restrictions = self.restriction_service.get_all_restrictions()
        offerings = self.offering_service.get_all_offerings()

        filtered_offerings = [
            offering for offering in offerings
            if offering.course_id in desired_course_ids
            and not self._offering_conflicts_restrictions(offering, restrictions)
        ]

        offerings_by_course = {
            course_id: [offering for offering in filtered_offerings if offering.course_id == course_id]
            for course_id in desired_course_ids
        }

        # Debug: log which courses have no valid offerings
        courses_without_offerings = [course_id for course_id in desired_course_ids if len(offerings_by_course[course_id]) == 0]
        if courses_without_offerings:
            print(f"[DEBUG] Student {student_id}: Courses without valid offerings (due to restrictions): {courses_without_offerings}")
            print(f"[DEBUG] Available restrictions: {[(self._normalize_day_of_week(r.day_of_week), r.start_time, r.end_time) for r in restrictions]}")

        valid_course_ids = [course_id for course_id in desired_course_ids if len(offerings_by_course[course_id]) > 0]
        if not valid_course_ids:
            return []

        results: List[list[dict]] = []
        current_schedule = []

        def backtrack(index: int):
            if index == len(valid_course_ids):
                results.append([self._offer_to_dict(offering) for offering in current_schedule])
                return

            course_id = valid_course_ids[index]
            for offering in offerings_by_course[course_id]:
                if any(self._time_conflict(offering, existing) for existing in current_schedule):
                    continue

                current_schedule.append(offering)
                backtrack(index + 1)
                current_schedule.pop()

        backtrack(0)
        return results

    def generate_valid_schedules(self, student_id: int) -> list[list[dict]]:
        return self.generate_possible_schedules(student_id)
