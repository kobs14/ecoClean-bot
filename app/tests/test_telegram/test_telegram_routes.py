import json
import uuid
from unittest.mock import patch, MagicMock
import psycopg2.errors as psycopg2_errors
import pytest
from app.main import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()



# Test for successful creation of a Telegram entry
@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_success(mock_conn, client):
    """
    Test successful linking of a Telegram account.
    """
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock database response for verification token
    mock_cursor.fetchone.return_value = {
        'telegram_id': '123e4567-e89b-12d3-a456-426614174000',
        'telegram_account_id': 'abcde12345'
    }

    request_data = {
        "telegram_user_id": "telegram_123",
        "telegram_username": "test_user",
        "verification_token": "valid-token-uuid"
    }

    response = client.post('/telegram/link', json=request_data)

    assert response.status_code == 201
    assert json.loads(response.data)['message'] == "Telegram account linked and verified successfully"

    mock_cursor.execute.assert_called()  # Ensure the DB was updated
    mock_conn.commit.assert_called()  # Ensure the transaction was committed


@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_missing_fields(mock_conn, client):
    """
    Test linking a Telegram account with missing required fields.
    """
    response = client.post('/telegram/link', json={})  # Empty request

    assert response.status_code == 400
    assert "Missing required fields" in json.loads(response.data)['message']


@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_invalid_token(mock_conn, client):
    """
    Test linking a Telegram account with an invalid or expired verification token.
    """
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Simulate token not found in the database
    mock_cursor.fetchone.return_value = None

    request_data = {
        "telegram_user_id": "telegram_123",
        "telegram_username": "test_user",
        "verification_token": "invalid-token"
    }

    response = client.post('/telegram/link', json=request_data)

    assert response.status_code == 404
    assert json.loads(response.data)['message'] == "Verification token not found or expired."


@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_db_error(mock_conn, client):
    """
    Test linking a Telegram account when a database error occurs.
    """
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Simulate a DB exception
    mock_cursor.fetchone.side_effect = Exception("Database error")

    request_data = {
        "telegram_user_id": "telegram_123",
        "telegram_username": "test_user",
        "verification_token": "valid-token-uuid"
    }

    response = client.post('/telegram/link', json=request_data)

    assert response.status_code == 500
    assert "An unexpected error occurred." in json.loads(response.data)['error']

    mock_conn.rollback.assert_called()  # Ensure rollback is called on error

# Test for missing required fields
@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_missing_fields(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Missing 'telegram_user_id'
    data = {
        'verification_token': str(uuid.uuid4())
    }

    response = client.post('/telegram/link', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert "Missing required fields" in result['message']


# Test for invalid verification token (not found)
@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_invalid_token(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Simulate token not found

    data = {
        'telegram_user_id': '123456789',
        'telegram_username': 'test12',
        'verification_token': str(uuid.uuid4())
    }

    response = client.post('/telegram/link', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Verification token not found or expired."


# Test for successful account linking
@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_success(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'telegram_id': str(uuid.uuid4()), 'telegram_account_id': str(uuid.uuid4())}

    data = {
        'telegram_user_id': '123456789',
        'telegram_username': 'newuser',
        'verification_token': str(uuid.uuid4())
    }

    response = client.post('/telegram/link', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Telegram account linked and verified successfully"


# Test for unique violation on telegram_user_id
@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_user_id_exists(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2_errors.UniqueViolation(
        "duplicate key value violates unique constraint \"telegram_user_id_key\""
    )

    data = {
        'telegram_user_id': '123456789',
        'telegram_username': 'test12',
        'verification_token': str(uuid.uuid4())
    }

    response = client.post('/telegram/link', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "A Telegram entry with this user ID already exists."


# Test for unique violation on telegram_username
@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_username_exists(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2_errors.UniqueViolation(
        "duplicate key value violates unique constraint \"telegram_username_key\""
    )

    data = {
        'telegram_user_id': '123456789',
        'telegram_username': 'existinguser',
        'verification_token': str(uuid.uuid4())
    }

    response = client.post('/telegram/link', json=data)

    assert response.status_code == 409
    result = json.loads(response.data)
    assert result['message'] == "A Telegram entry with this username already exists."


# Test for unexpected database error
@patch('app.routes.telegram.routes.conn')
def test_link_telegram_account_unexpected_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected database error")

    data = {
        'telegram_user_id': '123456789',
        'telegram_username': 'test12',
        'verification_token': str(uuid.uuid4())
    }

    response = client.post('/telegram/link', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An unexpected error occurred."


###

# Test for successfully retrieving a Telegram entry
@patch('app.routes.telegram.routes.conn')
def test_get_telegram_success(mock_conn, client):
    # Mock cursor behavior for successful retrieval
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        'telegram_id': str(uuid.uuid4()),
        'telegram_account_id': str(uuid.uuid4()),
        'telegram_user_id': '123456789',
        'telegram_username': 'testuser',
        'telegram_verified': True,
        'telegram_is_admin': False,
        'telegram_created': '2023-10-01T12:00:00Z'
    }

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    response = client.get(f'/telegram/{telegram_id}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'telegram_id' in result
    assert 'telegram_account_id' in result
    assert 'telegram_user_id' in result
    assert 'telegram_username' in result
    assert 'telegram_verified' in result
    assert 'telegram_is_admin' in result
    assert 'telegram_created' in result


# Test for invalid UUID format
def test_get_telegram_invalid_uuid(client):
    # Invalid UUID format
    telegram_id = 'invalid-uuid'

    response = client.get(f'/telegram/{telegram_id}')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid telegram_id format."


# Test for Telegram entry not found
@patch('app.routes.telegram.routes.conn')
def test_get_telegram_not_found(mock_conn, client):
    # Mock cursor behavior to simulate no entry found
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    response = client.get(f'/telegram/{telegram_id}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Telegram entry not found."


# Test for unexpected database error
@patch('app.routes.telegram.routes.conn')
def test_get_telegram_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected database error")

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    response = client.get(f'/telegram/{telegram_id}')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected database error"



###

# Test for successfully retrieving a Telegram entry by account_id
@patch('app.routes.telegram.routes.conn')
def test_get_telegram_by_account_success(mock_conn, client):
    # Mock cursor behavior for successful retrieval
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        'telegram_id': str(uuid.uuid4()),
        'telegram_account_id': str(uuid.uuid4()),
        'telegram_user_id': '123456789',
        'telegram_username': 'testuser',
        'telegram_verified': True,
        'telegram_is_admin': False,
        'telegram_created': '2023-10-01T12:00:00Z'
    }

    # Valid UUID for testing
    account_id = str(uuid.uuid4())

    response = client.get(f'/telegram/account/{account_id}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'telegram_id' in result
    assert 'telegram_account_id' in result
    assert 'telegram_user_id' in result
    assert 'telegram_username' in result
    assert 'telegram_verified' in result
    assert 'telegram_is_admin' in result
    assert 'telegram_created' in result


# Test for invalid UUID format
def test_get_telegram_by_account_invalid_uuid(client):
    # Invalid UUID format
    account_id = 'invalid-uuid'

    response = client.get(f'/telegram/account/{account_id}')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account_id format."


# Test for Telegram entry not found for the given account_id
@patch('app.routes.telegram.routes.conn')
def test_get_telegram_by_account_not_found(mock_conn, client):
    # Mock cursor behavior to simulate no entry found
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    # Valid UUID for testing
    account_id = str(uuid.uuid4())

    response = client.get(f'/telegram/account/{account_id}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Telegram entry not found for the given account."


# Test for unexpected database error
@patch('app.routes.telegram.routes.conn')
def test_get_telegram_by_account_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected database error")

    # Valid UUID for testing
    account_id = str(uuid.uuid4())

    response = client.get(f'/telegram/account/{account_id}')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected database error"



###

# Test for successfully updating the telegram_is_admin field
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_and_admin_success(mock_conn, client):
    # Mock cursor behavior for successful update
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'telegram_id': str(uuid.uuid4())}

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Test data
    data = {
        'telegram_is_admin': True
    }

    response = client.put(f'/telegram/{telegram_id}/admin', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Telegram entry updated successfully"
    assert result['telegram_id'] == telegram_id


# Test for invalid UUID format
def test_update_telegram_verified_and_admin_invalid_uuid(client):
    # Invalid UUID format
    telegram_id = 'invalid-uuid'

    # Test data
    data = {
        'telegram_is_admin': True
    }

    response = client.put(f'/telegram/{telegram_id}/admin', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid telegram_id format."


# Test for missing required fields
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_and_admin_missing_fields(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Missing 'telegram_is_admin' field
    data = {}

    response = client.put(f'/telegram/{telegram_id}/admin', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "No fields to update. Provide 'telegram_is_admin'."


# Test for Telegram entry not found
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_and_admin_not_found(mock_conn, client):
    # Mock cursor behavior to simulate no entry found
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Test data
    data = {
        'telegram_is_admin': True
    }

    response = client.put(f'/telegram/{telegram_id}/admin', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == "Telegram entry not found."


# Test for unexpected database error
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_and_admin_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected database error")

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Test data
    data = {
        'telegram_is_admin': True
    }

    response = client.put(f'/telegram/{telegram_id}/admin', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected database error"


###

# Test for successfully updating the telegram_verified field
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_success(mock_conn, client):
    # Mock cursor behavior for successful update
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'telegram_id': str(uuid.uuid4())}

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Test data
    data = {
        'telegram_verified': True
    }

    response = client.put(f'/telegram/{telegram_id}/verified', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "'telegram_verified' updated successfully"
    assert result['telegram_id'] == telegram_id


# Test for invalid UUID format
def test_update_telegram_verified_invalid_uuid(client):
    # Invalid UUID format
    telegram_id = 'invalid-uuid'

    # Test data
    data = {
        'telegram_verified': True
    }

    response = client.put(f'/telegram/{telegram_id}/verified', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid telegram_id format."


# Test for missing required fields
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_missing_fields(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Missing 'telegram_verified' field
    data = {}

    response = client.put(f'/telegram/{telegram_id}/verified', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Missing 'telegram_verified' field."


# Test for Telegram entry not found
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_not_found(mock_conn, client):
    # Mock cursor behavior to simulate no entry found
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Test data
    data = {
        'telegram_verified': True
    }

    response = client.put(f'/telegram/{telegram_id}/verified', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Telegram entry not found."


# Test for unexpected database error
@patch('app.routes.telegram.routes.conn')
def test_update_telegram_verified_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected database error")

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    # Test data
    data = {
        'telegram_verified': True
    }

    response = client.put(f'/telegram/{telegram_id}/verified', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected database error"


###

# Test for successfully deleting a Telegram entry
@patch('app.routes.telegram.routes.conn')
def test_delete_telegram_success(mock_conn, client):
    # Mock cursor behavior for successful deletion
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.rowcount = 1  # Simulate one row being deleted

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    response = client.delete(f'/telegram/{telegram_id}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Successfully deleted Telegram entry."


# Test for Telegram entry not found
@patch('app.routes.telegram.routes.conn')
def test_delete_telegram_not_found(mock_conn, client):
    # Mock cursor behavior to simulate no entry found
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.rowcount = 0  # Simulate no rows being deleted

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    response = client.delete(f'/telegram/{telegram_id}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Telegram entry not found."


# Test for unexpected database error
@patch('app.routes.telegram.routes.conn')
def test_delete_telegram_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected database error")

    # Valid UUID for testing
    telegram_id = str(uuid.uuid4())

    response = client.delete(f'/telegram/{telegram_id}')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected database error"


###

# Test for successfully searching Telegram entries with valid query parameters
@patch('app.routes.telegram.routes.conn')
def test_search_telegram_entries_success(mock_conn, client):
    # Mock cursor behavior for successful search
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            "telegram_id": "e5845f2a-a5c2-4126-93eb-6625114a2b42",
            "telegram_account_id": "58ad78c4-b13f-4cca-978e-cea672879a15",
            "telegram_user_id": "tssss2e1",
            "telegram_username": "Monster14",
            "telegram_verified": True,
            "telegram_created": "2024-10-17T16:44:05Z",
            "telegram_is_admin": False
        }
    ]

    # Test query parameters
    query_params = {
        'username': 'Monster',
        'verified': 'true',
        'is_admin': 'false'
    }

    response = client.get('/telegram/search', query_string=query_params)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]['telegram_username'] == "Monster14"


# Test for invalid verified parameter format
def test_search_telegram_entries_invalid_verified_format(client):
    # Invalid verified parameter (not 'true' or 'false')
    query_params = {
        'telegram_verified': 'invalid_value'
    }

    response = client.get('/telegram/search', query_string=query_params)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid verified parameter format. Expected 'true' or 'false'."


# Test for invalid is_admin parameter format
def test_search_telegram_entries_invalid_is_admin_format(client):
    # Invalid is_admin parameter (not 'true' or 'false')
    query_params = {
        'telegram_is_admin': 'invalid_value'
    }

    response = client.get('/telegram/search', query_string=query_params)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid is_admin parameter format. Expected 'true' or 'false'."


# Test for searching without any filters (should return all entries)
@patch('app.routes.telegram.routes.conn')
def test_search_telegram_entries_no_filters(mock_conn, client):
    # Mock cursor behavior for successful search
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            "telegram_id": "e5845f2a-a5c2-4126-93eb-6625114a2b42",
            "telegram_account_id": "58ad78c4-b13f-4cca-978e-cea672879a15",
            "telegram_user_id": "tssss2e1",
            "telegram_username": "Monster14",
            "telegram_verified": True,
            "telegram_created": "2024-10-17T16:44:05Z",
            "telegram_is_admin": False
        },
        {
            "telegram_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "telegram_account_id": "12345678-1234-5678-1234-567890abcdef",
            "telegram_user_id": "user123",
            "telegram_username": "TestUser",
            "telegram_verified": False,
            "telegram_created": "2024-10-18T12:00:00Z",
            "telegram_is_admin": True
        }
    ]

    # No query parameters
    response = client.get('/telegram/search')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert isinstance(result, list)
    assert len(result) == 2


# Test for unexpected database error
@patch('app.routes.telegram.routes.conn')
def test_search_telegram_entries_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected database error")

    # Test query parameters
    query_params = {
        'username': 'Monster'
    }

    response = client.get('/telegram/search', query_string=query_params)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "Unexpected database error"