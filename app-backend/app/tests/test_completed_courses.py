from app import models

def test_get_completed_courses(client, db_session):
    # 1. Create a student user in the database via the API
    student_payload = {
        "current_semester": 2,
        "course": "Engenharia de Software",
        "user": {
            "name": "Maria Teste",
            "email": "maria@teste.com",
            "card_number": 999999,
            "password": "senha"
        }
    }
    student_res = client.post("/students/", json=student_payload)
    assert student_res.status_code == 200
    student_data = student_res.json()
    student_id = student_data["user_id"]

    # 2. Create a course
    course_payload = {
        "code": "INF01202",
        "name": "Algoritmos e Programação",
        "credits": 6,
        "min_credits_required": 0
    }
    course_res = client.post("/courses/", json=course_payload)
    assert course_res.status_code == 200
    course_data = course_res.json()
    course_id = course_data["id"]

    # 3. Validate that initially the student has no completed courses
    get_res = client.get(f"/students/{student_id}/completed-courses")
    assert get_res.status_code == 200
    assert len(get_res.json()) == 0

    # 4. Insert completion directly in the database
    completed_course = models.CompletedCourse(student_id=student_id, course_id=course_id)
    db_session.add(completed_course)
    db_session.commit()

    # 5. Validate that the completed course is now returned
    get_res = client.get(f"/students/{student_id}/completed-courses")
    assert get_res.status_code == 200
    res_data = get_res.json()
    assert len(res_data) == 1
    assert res_data[0]["code"] == "INF01202"

def test_update_completed_courses(client, db_session):
    # 1. Create a student
    student_payload = {
        "current_semester": 1,
        "course": "Engenharia de Software",
        "user": {
            "name": "João Teste",
            "email": "joao@teste.com",
            "card_number": 888888,
            "password": "senha"
        }
    }
    student_res = client.post("/students/", json=student_payload)
    assert student_res.status_code == 200
    student_data = student_res.json()
    student_id = student_data["user_id"]

    # 2. Create two courses
    c1 = client.post("/courses/", json={"code": "MAT01353", "name": "Cálculo I", "credits": 4, "min_credits_required": 0}).json()
    c2 = client.post("/courses/", json={"code": "INF01202", "name": "Algoritmos", "credits": 6, "min_credits_required": 0}).json()

    # 3. Update completed courses via the API
    update_res = client.post(f"/students/{student_id}/completed-courses", json=[c1["id"], c2["id"]])
    assert update_res.status_code == 200

    # 4. Validate if they were saved correctly
    get_res = client.get(f"/students/{student_id}/completed-courses")
    assert get_res.status_code == 200
    res_data = get_res.json()
    assert len(res_data) == 2
    codes = {c["code"] for c in res_data}
    assert "MAT01353" in codes
    assert "INF01202" in codes

    # 5. Update again removing one and adding no other
    update_res2 = client.post(f"/students/{student_id}/completed-courses", json=[c2["id"]])
    assert update_res2.status_code == 200

    # 6. Validate the update
    get_res2 = client.get(f"/students/{student_id}/completed-courses")
    assert get_res2.status_code == 200
    res_data2 = get_res2.json()
    assert len(res_data2) == 1
    assert res_data2[0]["code"] == "INF01202"


def test_upload_completed_courses_pdf(client, db_session):
    # 1. Create a student
    student_payload = {
        "current_semester": 1,
        "course": "Ciência da Computação",
        "user": {
            "name": "Eduardo Teste",
            "email": "eduardo@teste.com",
            "card_number": 325091,
            "password": "senha"
        }
    }
    student_res = client.post("/students/", json=student_payload)
    assert student_res.status_code == 200
    student_id = student_res.json()["user_id"]

    # 2. Create some courses we know are in the PDF
    courses_to_create = [
        {"code": "INF05027", "name": "Projeto e Análise de Algoritmos I", "credits": 4, "min_credits_required": 0},
        {"code": "INF01087", "name": "Introdução à Ciência da Computação", "credits": 4, "min_credits_required": 0},
        {"code": "MAT01353", "name": "Cálculo I", "credits": 6, "min_credits_required": 0},
        {"code": "INF01202", "name": "Algoritmos e Programação", "credits": 6, "min_credits_required": 0},
    ]
    for c in courses_to_create:
        res = client.post("/courses/", json=c)
        assert res.status_code == 200

    # 3. Read the actual PDF file
    import os
    pdf_path = "/home/edulazuta/eng_software_TP/Aluno - Histórico do Curso.pdf"
    assert os.path.exists(pdf_path)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 4. Upload the PDF via the API
    response = client.post(
        f"/students/{student_id}/completed-courses/upload-pdf",
        files={"file": ("Aluno - Histórico do Curso.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 200
    res_data = response.json()

    # 5. Validate that courses from the database present as completed in the PDF were marked
    completed_codes = {c["code"] for c in res_data}
    assert "INF05027" in completed_codes
    assert "INF01087" in completed_codes
    assert "MAT01353" in completed_codes
    assert "INF01202" in completed_codes
    assert len(completed_codes) == 4


def test_upload_completed_courses_pdf_wrong_course(client, db_session):
    # 1. Create a student of another course (Engenharia de Computação)
    student_payload = {
        "current_semester": 1,
        "course": "Engenharia de Computação",
        "user": {
            "name": "Eduardo Mismatch",
            "email": "mismatch@teste.com",
            "card_number": 44445555,
            "password": "senha"
        }
    }
    student_res = client.post("/students/", json=student_payload)
    assert student_res.status_code == 200
    student_id = student_res.json()["user_id"]

    # 2. Read the actual PDF file (which is for the Ciência da Computação course)
    import os
    pdf_path = "/home/edulazuta/eng_software_TP/Aluno - Histórico do Curso.pdf"
    assert os.path.exists(pdf_path)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 3. Upload the PDF via the API (should return a 400 error)
    response = client.post(
        f"/students/{student_id}/completed-courses/upload-pdf",
        files={"file": ("Aluno - Histórico do Curso.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 400
    assert "Por favor, envie o histórico correto" in response.json()["detail"]


