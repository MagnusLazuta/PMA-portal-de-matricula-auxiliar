import pytest
from .. import models

def test_curriculum_endpoints(client, db_session):
    # 1. Create curricula and courses
    cc = models.Curriculum(name="Ciência da Computação")
    ec = models.Curriculum(name="Engenharia de Computação")
    db_session.add_all([cc, ec])
    db_session.commit()

    course1 = models.Course(code="INF01", name="Algoritmos", credits=4, min_credits_required=0)
    course2 = models.Course(code="INF02", name="Circuitos Digitais", credits=4, min_credits_required=0)
    db_session.add_all([course1, course2])
    db_session.commit()

    # Associate courses
    cc_c1 = models.CurriculumCourse(curriculum_id=cc.id, course_id=course1.id, semester=1, mandatory=True)
    ec_c2 = models.CurriculumCourse(curriculum_id=ec.id, course_id=course2.id, semester=2, mandatory=True)
    db_session.add_all([cc_c1, ec_c2])
    db_session.commit()

    # 2. Test GET /courses/curricula
    response = client.get("/courses/curricula")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {c["name"] for c in data} == {"Ciência da Computação", "Engenharia de Computação"}

    # 3. Test GET /courses/?curriculum_id={id}
    response = client.get(f"/courses/?curriculum_id={cc.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "INF01"
    assert data[0]["semester"] == 1
    assert data[0]["mandatory"] is True

    # 4. Create test student associated with CC curriculum
    user = models.User(name="Estudante CC", email="cc@test.com", card_number=12345678, password="pwd")
    db_session.add(user)
    db_session.commit()

    student = models.Student(user_id=user.id, current_semester=1, course="Ciência da Computação", curriculum_id=cc.id)
    db_session.add(student)
    db_session.commit()

    # 5. Test GET /students/{student_id}/curriculum
    response = client.get(f"/students/{student.user_id}/curriculum")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "INF01"

    # 6. Test GET /students/{student_id}/eligible-courses
    # The CC student should only have INF01 eligible (which is in their curriculum)
    response = client.get(f"/students/{student.user_id}/eligible-courses")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "INF01"
