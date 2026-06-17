import pytest
from app import models
from app.utils.security import hash_password

def test_get_and_update_profile_student(client, db_session):
    # 1. Create a Curriculum
    curriculum = models.Curriculum(name="Ciência da Computação")
    db_session.add(curriculum)
    db_session.flush()

    # 2. Create User and Student
    user = models.User(
        name="John Doe",
        email="john.doe@ufrgs.br",
        card_number=12345678,
        password=hash_password("testpassword")
    )
    db_session.add(user)
    db_session.flush()

    student = models.Student(
        user_id=user.id,
        current_semester=3,
        course="Ciência da Computação",
        curriculum_id=curriculum.id
    )
    db_session.add(student)
    db_session.commit()

    # 3. Get profile
    response = client.get(f"/auth/profile/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["name"] == "John Doe"
    assert data["email"] == "john.doe@ufrgs.br"
    assert data["card_number"] == 12345678
    assert data["role"] == "student"
    assert data["course"] == "Ciência da Computação"
    assert data["current_semester"] == 3
    assert data["curriculum_name"] == "Ciência da Computação"
    assert data["comgrad_role"] is None

    # 4. Update email successfully
    update_res = client.put(f"/auth/profile/{user.id}/email", json={"email": "new.email@ufrgs.br"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "success"

    # 5. Verify email updated in profile
    get_res = client.get(f"/auth/profile/{user.id}")
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "new.email@ufrgs.br"

def test_get_profile_comgrad(client, db_session):
    # 1. Create COMGRAD user
    user = models.User(
        name="Jane Smith",
        email="jane.smith@ufrgs.br",
        card_number=87654321,
        password=hash_password("testpassword")
    )
    db_session.add(user)
    db_session.flush()

    comgrad = models.COMGRAD(
        user_id=user.id,
        role="Membro da Comissão"
    )
    db_session.add(comgrad)
    db_session.commit()

    # 2. Get Profile
    response = client.get(f"/auth/profile/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["name"] == "Jane Smith"
    assert data["role"] == "comgrad"
    assert data["comgrad_role"] == "Membro da Comissão"
    assert data["course"] is None

def test_update_email_validation(client, db_session):
    # 1. Create two users
    u1 = models.User(
        name="User One",
        email="u1@ufrgs.br",
        card_number=11112222,
        password=hash_password("pass123")
    )
    u2 = models.User(
        name="User Two",
        email="u2@ufrgs.br",
        card_number=33334444,
        password=hash_password("pass123")
    )
    db_session.add_all([u1, u2])
    db_session.commit()

    # 2. Attempt to update u1's email to u2's email (duplicate error)
    response = client.put(f"/auth/profile/{u1.id}/email", json={"email": "u2@ufrgs.br"})
    assert response.status_code == 400
    assert "já está sendo utilizado" in response.json()["detail"]

    # 3. Attempt to update u1's email to an invalid format
    response_invalid = client.put(f"/auth/profile/{u1.id}/email", json={"email": "invalid_email_format"})
    assert response_invalid.status_code == 400
    assert "Formato de e-mail inválido" in response_invalid.json()["detail"]

    # 4. Attempt to update u1's email to empty string
    response_empty = client.put(f"/auth/profile/{u1.id}/email", json={"email": "   "})
    assert response_empty.status_code == 400
    assert "E-mail não pode ser vazio" in response_empty.json()["detail"]
