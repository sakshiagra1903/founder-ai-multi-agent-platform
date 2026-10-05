def test_signup(client):
    res = client.post("/auth/signup", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_signup_duplicate_email(client):
    client.post("/auth/signup", json={"name": "A", "email": "dup@example.com", "password": "pass"})
    res = client.post("/auth/signup", json={"name": "B", "email": "dup@example.com", "password": "pass"})
    assert res.status_code == 400


def test_login_success(client):
    client.post("/auth/signup", json={"name": "Login User", "email": "login@example.com", "password": "secret"})
    res = client.post("/auth/login", json={"email": "login@example.com", "password": "secret"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    client.post("/auth/signup", json={"name": "U", "email": "u@example.com", "password": "correct"})
    res = client.post("/auth/login", json={"email": "u@example.com", "password": "wrong"})
    assert res.status_code == 401


def test_me_authenticated(client):
    client.post("/auth/signup", json={"name": "Me User", "email": "me@example.com", "password": "pass"})
    login = client.post("/auth/login", json={"email": "me@example.com", "password": "pass"})
    token = login.json()["access_token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"
