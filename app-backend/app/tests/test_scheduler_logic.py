from datetime import time
from .. import models

def test_create_course_with_prerequisites(client, db_session):
    # 1. Create the course that will be a prerequisite
    prereq_data = {
        "code": "PR101",
        "name": "Prerequisite Course",
        "credits": 4,
        "min_credits_required": 0
    }
    resp1 = client.post("/courses/", json=prereq_data)
    prereq_id = resp1.json()["id"]

    # 2. Create the main course with the prerequisite
    course_data = {
        "code": "MAIN101",
        "name": "Main Course",
        "credits": 4,
        "min_credits_required": 0,
        "prerequisite_ids": [prereq_id]
    }
    resp2 = client.post("/courses/", json=course_data)
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["code"] == "MAIN101"
    assert len(data["prerequisites"]) == 1
    assert data["prerequisites"][0]["id"] == prereq_id

def test_scheduler_with_prerequisites(client, db_session):
    # Setup: PR101 (4 credits) and MAIN101 (requires PR101) courses
    prereq = models.Course(code="PR101", name="Prereq", credits=4, min_credits_required=0)
    db_session.add(prereq)
    db_session.commit()

    main_course = models.Course(
        code="MAIN101", 
        name="Main", 
        credits=4, 
        min_credits_required=0,
        prerequisites=[prereq]
    )
    db_session.add(main_course)
    db_session.commit()

    # Class section for MAIN101
    section = models.ClassSection(course_id=main_course.id, section_code="A", semester="2024/1", capacity=30)
    db_session.add(section)
    db_session.commit()

    schedule = models.ClassSchedule(
        class_section_id=section.id, 
        day_of_week="Monday", 
        start_time=time(8, 0), 
        end_time=time(10, 0), 
        room="101"
    )
    db_session.add(schedule)
    db_session.commit()

    # Student
    user = models.User(name="Test Student", email="test@test.com", card_number=12345, password="hash")
    db_session.add(user)
    db_session.commit()
    student = models.Student(user_id=user.id, current_semester=1, course="CS")
    db_session.add(student)
    db_session.commit()
    
    # Add MAIN101 to wishlist
    wish = models.CourseWishlist(student_id=student.user_id, course_id=main_course.id)
    db_session.add(wish)
    db_session.commit()

    # Case 1: Student does NOT have the prerequisite
    response = client.post("/generate-schedules/", json={"student_id": student.user_id})
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Case 2: Student passed PR101
    completed = models.CompletedCourse(student_id=student.user_id, course_id=prereq.id)
    db_session.add(completed)
    db_session.commit()

    response = client.post("/generate-schedules/", json={"student_id": student.user_id})
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0][0]["course_code"] == "MAIN101"

def test_scheduler_with_min_credits(client, db_session):
    # Setup: ADV101 course requires 10 credits
    adv_course = models.Course(code="ADV101", name="Advanced", credits=4, min_credits_required=10)
    db_session.add(adv_course)
    db_session.commit()
    
    # Class section for ADV101
    section = models.ClassSection(course_id=adv_course.id, section_code="A", semester="2024/1")
    db_session.add(section)
    db_session.commit()
    schedule = models.ClassSchedule(class_section_id=section.id, day_of_week="Tuesday", start_time=time(8, 0), end_time=time(10, 0))
    db_session.add(schedule)
    db_session.commit()

    # Student
    user = models.User(name="Student2", email="s2@test.com", card_number=54321, password="hash")
    db_session.add(user)
    db_session.commit()
    student = models.Student(user_id=user.id, current_semester=2, course="CS")
    db_session.add(student)
    db_session.commit()
    
    other_course = models.Course(code="OTH101", name="Other", credits=4, min_credits_required=0)
    db_session.add(other_course)
    db_session.commit()
    completed = models.CompletedCourse(student_id=student.user_id, course_id=other_course.id)
    db_session.add(completed)
    db_session.commit()
    
    # Wishlist has ADV101
    wish = models.CourseWishlist(student_id=student.user_id, course_id=adv_course.id)
    db_session.add(wish)
    db_session.commit()

    # Student has 4 credits, but needs 10
    response = client.post("/generate-schedules/", json={"student_id": student.user_id})
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Add more credits to reach 12
    c3 = models.Course(code="C3", name="C3", credits=8, min_credits_required=0)
    db_session.add(c3)
    db_session.commit()
    e3 = models.CompletedCourse(student_id=student.user_id, course_id=c3.id)
    db_session.add(e3)
    db_session.commit()

    # Now has 4 + 8 = 12 credits, should be able to take ADV101
    response = client.post("/generate-schedules/", json={"student_id": student.user_id})
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_scheduler_returns_top_five_schedules(client, db_session):
    courses = []
    for index in range(3):
        course = models.Course(
            code=f"C{index}",
            name=f"Course {index}",
            credits=4,
            min_credits_required=0,
        )
        db_session.add(course)
        courses.append(course)
    db_session.commit()

    for index, course in enumerate(courses):
        for section_suffix, start_hour in [("A", 8 + (index * 2)), ("B", 14 + (index * 2))]:
            section = models.ClassSection(
                course_id=course.id,
                section_code=section_suffix,
                semester="2026/1",
                capacity=30,
                professor_name=f"Professor {section_suffix}",
            )
            db_session.add(section)
            db_session.commit()

            db_session.add(
                models.ClassSchedule(
                    class_section_id=section.id,
                    day_of_week=["Monday", "Tuesday", "Wednesday"][index],
                    start_time=time(start_hour, 0),
                    end_time=time(start_hour + 1, 30),
                    room="101",
                )
            )
            db_session.commit()

    user = models.User(name="Top Five", email="top5@test.com", card_number=11111, password="hash")
    db_session.add(user)
    db_session.commit()
    student = models.Student(user_id=user.id, current_semester=1, course="CS")
    db_session.add(student)
    db_session.commit()

    for course in courses:
        db_session.add(models.CourseWishlist(student_id=student.user_id, course_id=course.id))
    db_session.commit()

    response = client.post("/generate-schedules/", json={"student_id": student.user_id, "limit": 5})
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_scheduler_prioritizes_more_important_course_when_there_is_a_conflict(client, db_session):
    important_course = models.Course(code="IMP101", name="Important", credits=4, min_credits_required=0)
    optional_course = models.Course(code="OPT101", name="Optional", credits=4, min_credits_required=0)
    db_session.add_all([important_course, optional_course])
    db_session.commit()

    important_section = models.ClassSection(
        course_id=important_course.id,
        section_code="A",
        semester="2026/1",
        capacity=30,
        professor_name="Prof Important",
    )
    optional_section = models.ClassSection(
        course_id=optional_course.id,
        section_code="A",
        semester="2026/1",
        capacity=30,
        professor_name="Prof Optional",
    )
    db_session.add_all([important_section, optional_section])
    db_session.commit()

    db_session.add_all([
        models.ClassSchedule(
            class_section_id=important_section.id,
            day_of_week="Monday",
            start_time=time(8, 30),
            end_time=time(10, 30),
            room="201",
        ),
        models.ClassSchedule(
            class_section_id=optional_section.id,
            day_of_week="Monday",
            start_time=time(8, 30),
            end_time=time(10, 30),
            room="202",
        ),
    ])
    db_session.commit()

    user = models.User(name="Priority Student", email="priority@test.com", card_number=22222, password="hash")
    db_session.add(user)
    db_session.commit()
    student = models.Student(user_id=user.id, current_semester=1, course="CS")
    db_session.add(student)
    db_session.commit()

    db_session.add_all([
        models.CourseWishlist(student_id=student.user_id, course_id=important_course.id),
        models.CourseWishlist(student_id=student.user_id, course_id=optional_course.id),
        models.TimeRestriction(
            student_id=student.user_id,
            restriction_type="course_importance",
            course_id=important_course.id,
            importance_level="high",
            score_weight=6,
            is_mandatory=False,
        ),
        models.TimeRestriction(
            student_id=student.user_id,
            restriction_type="course_importance",
            course_id=optional_course.id,
            importance_level="low",
            score_weight=1,
            is_mandatory=False,
        ),
    ])
    db_session.commit()

    response = client.post("/generate-schedules/ranked", json={"student_id": student.user_id, "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data[0]["selected_course_count"] == 1
    assert data[0]["schedule"][0]["course_code"] == "IMP101"


def test_scheduler_prefers_the_selected_professor_and_time_window(client, db_session):
    course = models.Course(code="PRF101", name="Professor Choice", credits=4, min_credits_required=0)
    db_session.add(course)
    db_session.commit()

    preferred_section = models.ClassSection(
        course_id=course.id,
        section_code="A",
        semester="2026/1",
        capacity=30,
        professor_name="Ada Lovelace",
    )
    fallback_section = models.ClassSection(
        course_id=course.id,
        section_code="B",
        semester="2026/1",
        capacity=30,
        professor_name="Grace Hopper",
    )
    db_session.add_all([preferred_section, fallback_section])
    db_session.commit()

    db_session.add_all([
        models.ClassSchedule(
            class_section_id=preferred_section.id,
            day_of_week="Monday",
            start_time=time(9, 0),
            end_time=time(11, 0),
            room="301",
        ),
        models.ClassSchedule(
            class_section_id=fallback_section.id,
            day_of_week="Monday",
            start_time=time(15, 0),
            end_time=time(17, 0),
            room="302",
        ),
    ])
    db_session.commit()

    user = models.User(name="Professor Student", email="prof@test.com", card_number=33333, password="hash")
    db_session.add(user)
    db_session.commit()
    student = models.Student(user_id=user.id, current_semester=1, course="CS")
    db_session.add(student)
    db_session.commit()

    db_session.add(models.CourseWishlist(student_id=student.user_id, course_id=course.id))
    db_session.add_all([
        models.TimeRestriction(
            student_id=student.user_id,
            restriction_type="professor_preference",
            course_id=course.id,
            preferred_professor="Ada Lovelace",
            preference_order=1,
            score_weight=3,
            is_mandatory=False,
        ),
        models.TimeRestriction(
            student_id=student.user_id,
            restriction_type="preferred_window",
            day_of_week="Monday",
            start_time=time(8, 30),
            end_time=time(13, 30),
            score_weight=2,
            is_mandatory=False,
        ),
    ])
    db_session.commit()

    response = client.post("/generate-schedules/ranked", json={"student_id": student.user_id})
    assert response.status_code == 200
    data = response.json()
    assert data[0]["schedule"][0]["professor_name"] == "Ada Lovelace"
    assert data[0]["matched_preference_count"] >= 2
