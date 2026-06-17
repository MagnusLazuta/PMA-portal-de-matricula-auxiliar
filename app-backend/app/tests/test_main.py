def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Schedule Generator API"}

def test_swagger_docs_enabled_by_default(client):
    response = client.get("/docs")
    assert response.status_code == 200

def test_swagger_docs_disabled(monkeypatch):
    import importlib
    import app.config
    import app.main
    monkeypatch.setenv("DEBUG", "false")
    importlib.reload(app.config)
    importlib.reload(app.main)
    from fastapi.testclient import TestClient
    with TestClient(app.main.app) as test_client:
        response = test_client.get("/docs")
        assert response.status_code == 404
    monkeypatch.delenv("DEBUG", raising=False)
    importlib.reload(app.config)
    importlib.reload(app.main)
