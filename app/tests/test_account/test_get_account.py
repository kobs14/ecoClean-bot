
import pytest
from flask import json
from unittest.mock import patch, MagicMock
from app.main import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

#############################
# get_account endpoint tests#
#############################



@patch('app.routes.account.routes.conn')
def test_get_account_success(mock_conn, client):
    # Mock the database cursor and its return values
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    account_id = "123e4567-e89b-12d3-a456-426614174000"
    account_data = {
        "account_id": account_id,
        "account_username": "testuser",
        "account_fullname": "Test User",
        "account_phone": "1234567890",
        "account_is_admin": False,
        "account_commission_rate": 0.1,
        "account_status": "active"
    }
    email_data = [
        {"email_id": 1, "email_address": "test@example.com"}
    ]
    telegram_data = {
        "telegram_id": 1,
        "telegram_username": "testuser",
        "telegram_chat_id": "12345"
    }

    # Set up the mock cursor to return appropriate data for each query
    mock_cursor.fetchone.side_effect = [account_data, telegram_data]
    mock_cursor.fetchall.return_value = email_data

    response = client.get(f'/account/{account_id}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["account_id"] == account_id
    assert "emails" in result
    assert "telegram" in result


@patch('app.routes.account.routes.conn')
def test_get_account_invalid_uuid(mock_conn, client):
    response = client.get('/account/invalid-uuid')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format"


@patch('app.routes.account.routes.conn')
def test_get_account_not_found(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Simulate account not found

    response = client.get('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Account not found"


@patch('app.routes.account.routes.conn')
def test_get_account_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.get('/account/123e4567-e89b-12d3-a456-426614174000')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"