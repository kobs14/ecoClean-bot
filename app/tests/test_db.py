import pytest
from unittest.mock import patch, MagicMock

from psycopg2.extras import RealDictCursor
from app.config import get_db_connection
from app.main import create_app

@pytest.fixture
def app():
    with patch('app.main.get_db_connection') as mock_db:
        mock_db.return_value = MagicMock()
        app = create_app('testing')
        yield app


@patch('app.config.psycopg2.connect')
def test_db_connection(mock_connect, app):
    mock_connect.return_value = MagicMock()
    with app.app_context():
        conn = get_db_connection(app.config['DATABASE_URL'])
    assert conn is not None
    mock_connect.assert_called_once_with(app.config['DATABASE_URL'], cursor_factory=RealDictCursor)

def test_db_connection_retry(monkeypatch):
    import psycopg2
    call_count = 0

    def mock_connect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise psycopg2.OperationalError("Mock connection error")
        return MagicMock()

    with patch('app.config.psycopg2.connect', side_effect=mock_connect):
        with create_app('testing').app_context():
            conn = get_db_connection()
            assert conn is not None
            assert call_count == 3