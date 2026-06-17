import pytest
from app import models

def test_setup_flow(client, db_session):
    # 1. Verify that setup is required initially
    response = client.get("/auth/setup-status")
    assert response.status_code == 200
    assert response.json() == {"setup_required": True}
    
    # 2. Register first admin
    setup_payload = {
        "name": "Administrador Principal",
        "email": "admin.principal@ufrgs.br",
        "card_number": "99999999",
        "password": "securepassword123"
    }
    setup_res = client.post("/auth/setup-admin", json=setup_payload)
    assert setup_res.status_code == 200
    assert setup_res.json()["status"] == "success"
    
    # 3. Verify that setup is no longer required
    status_res = client.get("/auth/setup-status")
    assert status_res.status_code == 200
    assert status_res.json() == {"setup_required": False}
    
    # 4. Attempt to run setup again (should fail with HTTP 400)
    setup_again_res = client.post("/auth/setup-admin", json=setup_payload)
    assert setup_again_res.status_code == 400
    assert "já foi cadastrado" in setup_again_res.json()["detail"]

def test_setup_validations(client, db_session):
    # 1. Invalid email format
    payload = {
        "name": "Admin Test",
        "email": "invalidemail",
        "card_number": "99999999",
        "password": "password123"
    }
    res = client.post("/auth/setup-admin", json=payload)
    assert res.status_code == 400
    assert "Formato de e-mail inválido" in res.json()["detail"]
    
    # 2. Invalid card number length
    payload["email"] = "valid@ufrgs.br"
    payload["card_number"] = "12345"
    res = client.post("/auth/setup-admin", json=payload)
    assert res.status_code == 400
    assert "A matrícula deve conter exatamente 8 dígitos" in res.json()["detail"]

def test_setup_leading_zeros(client, db_session):
    # Register admin with leading zeros
    setup_payload = {
        "name": "Admin Com Zeros",
        "email": "zeros@ufrgs.br",
        "card_number": "00000001",
        "password": "securepassword123"
    }
    setup_res = client.post("/auth/setup-admin", json=setup_payload)
    assert setup_res.status_code == 200
    assert setup_res.json()["status"] == "success"
    
    # Verify that it is stored as integer 1 in DB
    user = db_session.query(models.User).filter(models.User.email == "zeros@ufrgs.br").first()
    assert user.card_number == 1
