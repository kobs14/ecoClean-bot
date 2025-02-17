from uuid import uuid4


import pytest
from flask import json
from unittest.mock import patch, MagicMock
from app.main import create_app

# Sample UUIDs for testing
VALID_UUID = str(uuid4())
INVALID_UUID = 'invalid-uuid'

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()


################################
# search_accounts endpoint tests#
################################

# Test for empty search term
def test_search_accounts_empty_term(client):
    response = client.get('/account/accounts/search?q=')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Search term cannot be empty."

# Test for no accounts found
@patch('app.account.routes.conn')
def test_search_accounts_not_found(mock_conn, client):
    search_term = "nonexistent"
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []  # Simulate no accounts found

    response = client.get(f'/account/accounts/search?q={search_term}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "No accounts found."

# Test for successful search
@patch('app.account.routes.conn')
def test_search_accounts_success(mock_conn, client):
    search_term = "john"
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            'account_id': '123e4567-e89b-12d3-a456-426614174000',
            'account_username': 'john_doe',
            'account_fullname': 'John Doe',
            'account_phone': '123-456-7890',
        },
        {
            'account_id': '123e4567-e89b-12d3-a456-426614174001',
            'account_username': 'john_smith',
            'account_fullname': 'John Smith',
            'account_phone': '098-765-4321',
        },
    ]  # Simulate found accounts

    response = client.get(f'/account/accounts/search?q={search_term}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert len(result) == 2  # Ensure two accounts were found
    assert result[0]['account_username'] == 'john_doe'  # Check first account details
    assert result[1]['account_username'] == 'john_smith'  # Check second account details

# Test for unexpected error during search
@patch('app.account.routes.conn')
def test_search_accounts_unexpected_error(mock_conn, client):
    search_term = "john"
    mock_cursor = MagicMock()

    # Set up the mock connection to return the mock cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Set the side effect of the execute method to raise an Exception
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    # Call the endpoint
    response = client.get(f'/account/accounts/search?q={search_term}')

    # Assert the expected response
    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected error"

