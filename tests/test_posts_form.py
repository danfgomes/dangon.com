from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


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
