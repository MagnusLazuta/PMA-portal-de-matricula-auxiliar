def test_create_course(client):
    course_data = {
        "code": "CS101",
        "name": "Introduction to Computer Science",
        "credits": 4,
        "min_credits_required": 0
    }
    response = client.post("/courses/", json=course_data)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "CS101"
    assert "id" in data

def test_read_courses(client):
    # Primeiro cria um curso
    client.post("/courses/", json={
        "code": "CS101",
        "name": "Intro CS",
        "credits": 4,
        "min_credits_required": 0
    })
    
    response = client.get("/courses/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["code"] == "CS101"

def test_create_courses_bulk(client):
    courses_data = [
        {"code": "MATH101", "name": "Calculus I", "credits": 4, "min_credits_required": 0},
        {"code": "PHYS101", "name": "Physics I", "credits": 4, "min_credits_required": 0}
    ]
    response = client.post("/courses/bulk", json=courses_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["code"] == "MATH101"
    assert data[1]["code"] == "PHYS101"
