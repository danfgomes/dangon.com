import pytest
from http import HTTPStatus
from routers import users, posts
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c

def test_get_token(client, user):
    response = client.post(
        '/users/login',
        data={'username': user.email, 'password': user.password}
    )

    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert token['token_type'] == 'bearer'
    assert 'access_token' in token