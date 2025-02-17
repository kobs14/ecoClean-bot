import pytest
from unittest.mock import patch
from app.main import create_app

@pytest.fixture
def app():
    with patch('app.main.get_db_connection') as mock_db:
        mock_db.return_value = "Mocked DB Connection"
        app = create_app('testing')
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_app_creation(app):
    assert app is not None
    assert app.config['TESTING'] == True

def test_app_database_url(app):
    assert 'DATABASE_URL' in app.config, "DATABASE_URL not in app config"
    assert app.config['DATABASE_URL'] is not None, f"DATABASE_URL is None. Config: {app.config}"

def test_blueprint_registration(app):
    assert 'account' in app.blueprints
    # assert app.blueprints['account'].url_prefix == '/account'

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 404  # Assuming no root route is defined