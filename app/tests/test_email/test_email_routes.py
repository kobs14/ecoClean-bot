import psycopg2
import pytest
import json
from unittest.mock import patch, MagicMock
from uuid import uuid4

# Your Flask app instance
from app.main import create_app  # Adjust the import based on your app structure

@pytest.fixture
def client():
    app = create_app()  # Create the app instance
    with app.test_client() as client:
        yield client

@patch('app.routes.account.routes.conn')
def test_create_email_success(mock_conn, client):
    # Mock cursor behavior for successful email creation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'email_id': uuid4()}  # Mocking email ID response

    # Test data
    account_id = str(uuid4())  # Mock a valid UUID
    data = {
        'account_id': account_id,
        'email': 'test@gmail.com'
    }

    response = client.post('/account/email', json=data)

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['message'] == "Email created successfully"
    assert 'email_id' in result


@patch('app.routes.account.routes.conn')
def test_create_email_missing_fields(mock_conn, client):
    # Test missing fields
    data = {'account_id': str(uuid4())}  # Missing email

    response = client.post('/account/email', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Missing required fields: account_id or email."


@patch('app.routes.account.routes.conn')
def test_create_email_invalid_email(mock_conn, client):
    # Test invalid email format
    account_id = str(uuid4())
    data = {
        'account_id': account_id,
        'email': 'invalid-email'
    }

    response = client.post('/account/email', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid email format."


@patch('app.routes.account.routes.conn')
def test_create_email_already_exists(mock_conn, client):
    # Mock cursor behavior for unique violation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation  # Simulate unique constraint violation

    account_id = str(uuid4())
    data = {
        'account_id': account_id,
        'email': 'test@gmail.com'
    }

    response = client.post('/account/email', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "Email already exists."
