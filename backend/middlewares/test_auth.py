"""
Tests d'authentification et RBAC (Partie 14 du guide : parties à risque
à tester en priorité).
"""
def test_login_with_valid_credentials_returns_tokens(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "SuperSecret123"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "admin@test.local"


def test_login_with_wrong_password_is_rejected(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_login_with_unknown_email_gives_generic_error(client, admin_user):
    """
    Le message d'erreur doit être identique que l'email existe ou non,
    pour éviter l'énumération de comptes valides (auth_service.py).
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "inconnu@test.local", "password": "peu-importe"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Identifiants incorrects."


def test_protected_route_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_protected_route_works_with_valid_token(client, admin_user):
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@test.local", "password": "SuperSecret123"},
    )
    token = login_response.get_json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["email"] == "admin@test.local"


def test_admin_only_route_rejects_non_admin_role(client, app, db, admin_user):
    from models.user import User
    from models.role import Role
    from repositories.user_repository import UserRepository

    with app.app_context():
        UserRepository.create(
            nom="Utilisateur Standard", email="user@test.local",
            password="password123", role_nom=Role.UTILISATEUR_METIER,
        )

    login_response = client.post(
        "/api/auth/login", json={"email": "user@test.local", "password": "password123"}
    )
    token = login_response.get_json()["access_token"]

    response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403