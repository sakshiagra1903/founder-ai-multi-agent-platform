def test_signup_successful(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password_hash" not in data

def test_signup_duplicate_email(client):
    # First signup
    client.post(
        "/api/auth/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "securepassword123"
        }
    )
    # Second signup with same email
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Duplicate User",
            "email": "test@example.com",
            "password": "differentpassword"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "A user with this email address already exists."

def test_login_successful(client):
    # Setup user
    client.post(
        "/api/auth/signup",
        json={
            "name": "Login User",
            "email": "login@example.com",
            "password": "mysecretpassword"
        }
    )
    # Execute login
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "mysecretpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failed_wrong_password(client):
    # Setup user
    client.post(
        "/api/auth/signup",
        json={
            "name": "Login User",
            "email": "login@example.com",
            "password": "mysecretpassword"
        }
    )
    # Login with wrong password
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password."
