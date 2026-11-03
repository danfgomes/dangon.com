from fastapi.testclient import TestClient

from main import app
from src.auth import verify_access_token

client = TestClient(app)


def test_login_sets_a_valid_access_token_cookie():
    username = "login_user"
    email = "login_user@example.com"
    password = "senha1234"

    create_response = client.post(
        "/users/create",
        json={"username": username, "email": email, "password": password},
    )
    assert create_response.status_code == 200

    login_response = client.post(
        "/users/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )

    assert login_response.status_code == 302
    access_token_cookie = login_response.cookies.get("access_token")
    assert access_token_cookie is not None
    assert not access_token_cookie.startswith("Bearer ")
    payload = verify_access_token(access_token_cookie)
    assert payload is not None
    assert payload["sub"] == str(create_response.json()["id"])
    assert payload["role"] == "user"


def test_post_creation_page_is_available():
    response = client.get("/posts/new")

    assert response.status_code == 200
    assert "Criar publicação" in response.text


def test_post_creation_form_accepts_data():
    response = client.post(
        "/posts/new",
        data={
            "title": "Como criar posts com FastAPI",
            "category": "Backend",
            "reading_time_min": "7",
            "content": "Este conteúdo foi enviado pelo formulário de criação de publicações.",
        },
        follow_redirects=False,
    )

    assert response.status_code in {200, 302, 303}
