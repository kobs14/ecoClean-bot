
import uuid
from unittest.mock import patch, MagicMock
import pytest
from app.main import create_app
from werkzeug.datastructures import FileStorage


VALID_UUID = str(uuid.uuid4())
VALID_PHOTO_ID = str(uuid.uuid4())

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()


#### Test Cases for create_job_report

# Test for successful job report creation
@patch('app.routes.job_report.routes.conn')
def test_create_job_report_success(mock_conn, client):
    # Mock cursor behavior for successful job report creation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'job_report_id': 1}

    # Test data
    data = {
        'account_id': VALID_UUID,
        'latitude': 37.7749,
        'longitude': -122.4194,
        'amount_received_dollars': 150.75,
        'payment_method': 'Card',
        'job_description': 'Fixed leaky faucet and replaced bathroom tiles',
        'client_name': 'John Doe',
        'client_contact': '+1234567890',
        'job_status': 'completed',
        'notes': 'Client was very satisfied with the work'
    }

    response = client.post('/job-report/', json=data)

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['message'] == "Job report created successfully"
    assert 'client_name' in result


# Test for missing required fields
@patch('app.routes.job_report.routes.conn')
def test_create_job_report_missing_fields(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Missing the 'account_id' field
    data = {
        'latitude': 40.7128,
        'longitude': -74.0060,
        'amount_received_dollars': 100.50,
        'payment_method': 'credit_card',
        'job_description': 'Test job description',
        'client_name': 'Test Client',
        'client_contact': 'test@example.com',
        'job_status': 'completed',
        'notes': 'Test notes'
    }

    response = client.post('/job-report/', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Missing required field: account_id"


# Test for invalid account_id format\
@patch('app.routes.job_report.routes.conn')
def test_create_job_report_invalid_account_id(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Test data with invalid account_id format
    data = {
        'account_id': 'invalid-uuid',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'amount_received_dollars': 100.50,
        'payment_method': 'Card',
        'job_description': 'Test job description',
        'client_name': 'Test Client',
        'client_contact': 'test@example.com',
        'job_status': 'completed',
        'notes': 'Test notes'
    }

    response = client.post('/job-report/', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid telegram account ID format."


# Test for invalid field type (e.g., string instead of float for latitude)
@patch('app.routes.job_report.routes.conn')
def test_create_job_report_invalid_field_type(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Test data with invalid latitude type
    data = {
        'account_id': VALID_UUID,
        'latitude': 'invalid-latitude',
        'longitude': -74.0060,
        'amount_received_dollars': 100.50,
        'payment_method': 'Card',
        'job_description': 'Test job description',
        'client_name': 'Test Client',
        'client_contact': 'test@example.com',
        'job_status': 'completed',
        'notes': 'Test notes'
    }

    response = client.post('/job-report/', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert "Invalid latitude: expected float" in result['message']


# Test for handling unexpected errors
@patch('app.routes.job_report.routes.conn')
def test_create_job_report_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    # Test data
    data = {
        'account_id': VALID_UUID,
        'latitude': 40.7128,
        'longitude': -74.0060,
        'amount_received_dollars': 100.50,
        'payment_method': 'Card',
        'job_description': 'Test job description',
        'client_name': 'Test Client',
        'client_contact': 'test@example.com',
        'job_status': 'completed',
        'notes': 'Test notes'
    }

    response = client.post('/job-report/', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An unexpected error occurred."


# Test for optional fields being passed
@patch('app.routes.job_report.routes.conn')
def test_create_job_report_with_optional_fields(mock_conn, client):
    # Mock cursor behavior for successful job report creation
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'job_report_id': 1}

    # Test data with optional fields
    data = {
        'account_id': VALID_UUID,
        'amount_received_dollars': 100.50,
        'payment_method': 'Card',
        'job_description': 'Test job description',
        'client_name': 'Test Client',
        'client_contact': 'test@example.com',
        'job_status': 'completed',
        'notes': 'Test notes'  # Optional field
    }

    response = client.post('/job-report/', json=data)

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['message'] == "Job report created successfully"
    assert 'client_name' in result



### Test Cases for upload_job_report_photo

# Test for successful photo upload
@patch('app.routes.job_report.routes.conn')
@patch('app.routes.job_report.routes.storage')
def test_upload_job_report_photo_success(mock_storage, mock_conn, client):
    # Mock cursor behavior for successful photo upload
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'job_report_id': VALID_UUID}

    # Mock storage behavior
    mock_storage.save_file.return_value = "http://example.com/photo.jpg"

    # Create a mock file
    file = FileStorage(filename="test.jpg", content_type="image/jpeg")

    # Test data
    data = {
        'file': file
    }

    response = client.post(f'/job-report/{VALID_UUID}/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['message'] == "Photo uploaded successfully"


# Test for missing file in the request
@patch('app.routes.job_report.routes.conn')
def test_upload_job_report_photo_missing_file(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Test data with no file
    data = {}

    response = client.post(f'/job-report/{VALID_UUID}/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "No file part in the request."


# Test for empty filename
@patch('app.routes.job_report.routes.conn')
def test_upload_job_report_photo_empty_filename(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Create a mock file with an empty filename
    file = FileStorage(filename="", content_type="image/jpeg")

    # Test data
    data = {
        'file': file
    }

    response = client.post(f'/job-report/{VALID_UUID}/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "No selected file."


# Test for invalid file format
@patch('app.routes.job_report.routes.conn')
def test_upload_job_report_photo_invalid_file_format(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Create a mock file with an invalid format
    file = FileStorage(filename="test.txt", content_type="text/plain")

    # Test data
    data = {
        'file': file
    }

    response = client.post(f'/job-report/{VALID_UUID}/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid file format. Only PNG, JPG, and JPEG are allowed."


# Test for job report not found
@patch('app.routes.job_report.routes.conn')
def test_upload_job_report_photo_job_report_not_found(mock_conn, client):
    # Mock cursor behavior to simulate job report not found
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    # Create a mock file
    file = FileStorage(filename="test.jpg", content_type="image/jpeg")

    # Test data
    data = {
        'file': file
    }

    response = client.post(f'/job-report/{VALID_UUID}/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "Job report not found."


# Test for invalid job_report_id format
@patch('app.routes.job_report.routes.conn')
def test_upload_job_report_photo_invalid_job_report_id(mock_conn, client):
    # No need to mock cursor as this won't reach DB interaction

    # Create a mock file
    file = FileStorage(filename="test.jpg", content_type="image/jpeg")

    # Test data
    data = {
        'file': file
    }

    response = client.post('/job-report/invalid-uuid/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format."


# Test for handling unexpected errors
@patch('app.routes.job_report.routes.conn')
@patch('app.routes.job_report.routes.storage')
def test_upload_job_report_photo_unexpected_error(mock_storage, mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    # Mock storage behavior
    mock_storage.save_file.side_effect = Exception("Unexpected error")

    # Create a mock file
    file = FileStorage(filename="test.jpg", content_type="image/jpeg")

    # Test data
    data = {
        'file': file
    }

    response = client.post(f'/job-report/{VALID_UUID}/photos', data=data, content_type='multipart/form-data')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An unexpected error occurred while checking the job report."



### Test Cases for get_reports


# Test for successful retrieval of reports
@patch('app.routes.job_report.routes.conn')
def test_get_reports_account_id_success(mock_conn, client):
    # Mock cursor behavior for successful retrieval of reports
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            'job_report_id': uuid.uuid4(),
            'report_by_account_id': uuid.uuid4(),
            'latitude': 37.7749,
            'longitude': -122.4194,
            'created_at': datetime.now(),
            'amount_received_dollars': 150.75,
            'payment_method': 'Card',
            'job_description': 'Fixed leaky faucet',
            'client_name': 'John Doe',
            'client_contact': '+1234567890',
            'job_status': 'completed',
            'notes': 'Client was satisfied',
            'updated_at': datetime.now()
        }
    ]

    response = client.get(f'/job-report/{VALID_UUID}/reports')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'reports' in result
    assert len(result['reports']) == 1
    assert result['reports'][0]['client_name'] == 'John Doe'


# Test for invalid account ID format
def test_get_reports_account_id_invalid_format(client):
    # Test with an invalid account ID format
    invalid_uuid = 'invalid-uuid'

    response = client.get(f'/job-report/{invalid_uuid}/reports')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['message'] == "Invalid account ID format."


# Test for no reports found
@patch('app.routes.job_report.routes.conn')
def test_get_reports_account_id_no_reports_found(mock_conn, client):
    # Mock cursor behavior to return no reports
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    response = client.get(f'/job-report/{VALID_UUID}/reports')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['message'] == "No reports found for this account."


# Test for handling unexpected errors
@patch('app.routes.job_report.routes.conn')
def test_get_reports_account_id_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.get(f'/job-report/{VALID_UUID}/reports')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An error occurred while fetching the reports."


### Test Cases for get_report
###



# Test for successful retrieval of a job report
@patch('app.routes.job_report.routes.conn')
def test_get_job_report_success(mock_conn, client):
    # Mock cursor behavior for successful retrieval of a job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        'job_report_id': uuid.uuid4(),
        'report_by_account_id': uuid.uuid4(),
        'latitude': 37.7749,
        'longitude': -122.4194,
        'created_at': datetime.now(),
        'amount_received_dollars': 150.75,
        'payment_method': 'Card',
        'job_description': 'Fixed leaky faucet',
        'client_name': 'John Doe',
        'client_contact': '+1234567890',
        'job_status': 'completed',
        'notes': 'Client was satisfied',
        'updated_at': datetime.now()
    }

    response = client.get(f'/job-report/{VALID_UUID}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['client_name'] == 'John Doe'
    assert result['job_status'] == 'completed'


# Test for invalid job report ID format
def test_get_job_report_invalid_format(client):
    # Test with an invalid job report ID format
    invalid_uuid = 'invalid-uuid'

    response = client.get(f'/job-report/{invalid_uuid}')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "Invalid job report ID format"


# Test for job report not found
@patch('app.routes.job_report.routes.conn')
def test_get_job_report_not_found(mock_conn, client):
    # Mock cursor behavior to return no job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    response = client.get(f'/job-report/{VALID_UUID}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == "Job report not found"


# Test for handling unexpected errors
@patch('app.routes.job_report.routes.conn')
def test_get_job_report_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.get(f'/job-report/{VALID_UUID}')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An error occurred while fetching the job report"



import json
import uuid
from unittest.mock import patch, MagicMock
import pytest
from app.main import create_app
from datetime import datetime

VALID_UUID = str(uuid.uuid4())

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()


# Test for successful update of a job report
@patch('app.routes.job_report.routes.conn')
def test_update_job_report_success(mock_conn, client):
    # Mock cursor behavior for successful update of a job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        'job_report_id': uuid.uuid4(),
        'report_by_account_id': uuid.uuid4(),
        'latitude': 37.7749,
        'longitude': -122.4194,
        'created_at': datetime.now(),
        'amount_received_dollars': 150.75,
        'payment_method': 'Card',
        'job_description': 'Fixed leaky faucet and replaced tiles',
        'client_name': 'John Doe',
        'client_contact': '+1234567890',
        'job_status': 'completed',
        'notes': 'Client was satisfied',
        'updated_at': datetime.now()
    }

    # Test data
    data = {
        'latitude': 37.7749,
        'longitude': -122.4194,
        'job_description': 'Fixed leaky faucet and replaced tiles'
    }

    response = client.put(f'/job-report/{VALID_UUID}', json=data)

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['job_description'] == 'Fixed leaky faucet and replaced tiles'


# Test for invalid job report ID format
def test_update_job_report_invalid_format(client):
    # Test with an invalid job report ID format
    invalid_uuid = 'invalid-uuid'

    response = client.put(f'/job-report/{invalid_uuid}', json={})

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "Invalid job report ID format"


# Test for no update data provided
def test_update_job_report_no_data(client):
    # Test with no update data provided
    response = client.put(f'/job-report/{VALID_UUID}', json={})

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "No update data provided"


# Test for no valid fields to update
def test_update_job_report_no_valid_fields(client):
    # Test with no valid fields to update
    data = {
        'invalid_field': 'invalid_value'
    }

    response = client.put(f'/job-report/{VALID_UUID}', json=data)

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "No valid fields to update"


# Test for job report not found
@patch('app.routes.job_report.routes.conn')
def test_update_job_report_not_found(mock_conn, client):
    # Mock cursor behavior to return no job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    # Test data
    data = {
        'job_description': 'Fixed leaky faucet and replaced tiles'
    }

    response = client.put(f'/job-report/{VALID_UUID}', json=data)

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == "Job report not found"


# Test for handling unexpected errors
@patch('app.routes.job_report.routes.conn')
def test_update_job_report_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    # Test data
    data = {
        'job_description': 'Fixed leaky faucet and replaced tiles'
    }

    response = client.put(f'/job-report/{VALID_UUID}', json=data)

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An error occurred while updating the job report"


# Test for successful deletion of a job report
@patch('app.routes.job_report.routes.conn')
def test_delete_job_report_success(mock_conn, client):
    # Mock cursor behavior for successful deletion of a job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        'job_report_id': uuid.uuid4(),
        'report_by_account_id': uuid.uuid4(),
        'latitude': 37.7749,
        'longitude': -122.4194,
        'created_at': datetime.now(),
        'amount_received_dollars': 150.75,
        'payment_method': 'Card',
        'job_description': 'Fixed leaky faucet',
        'client_name': 'John Doe',
        'client_contact': '+1234567890',
        'job_status': 'completed',
        'notes': 'Client was satisfied',
        'updated_at': datetime.now()
    }

    response = client.delete(f'/job-report/{VALID_UUID}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Job report and associated photos deleted successfully"
    assert 'deleted_report' in result


# Test for invalid job report ID format
def test_delete_job_report_invalid_format(client):
    # Test with an invalid job report ID format
    invalid_uuid = 'invalid-uuid'

    response = client.delete(f'/job-report/{invalid_uuid}')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "Invalid job report ID format"


# Test for job report not found
@patch('app.routes.job_report.routes.conn')
def test_delete_job_report_not_found(mock_conn, client):
    # Mock cursor behavior to return no job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    response = client.delete(f'/job-report/{VALID_UUID}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == "Job report not found"


# Test for handling unexpected errors
@patch('app.routes.job_report.routes.conn')
def test_delete_job_report_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.delete(f'/job-report/{VALID_UUID}')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An error occurred while deleting the job report"



# Test for successful retrieval of photos for a job report
@patch('app.routes.job_report.routes.conn')
def test_list_job_report_photos_success(mock_conn, client):
    # Mock cursor behavior for successful retrieval of photos
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            'photo_id': uuid.uuid4(),
            'file_name': 'photo1.jpg',
            'file_size': 1024,
            'photo_url': 'http://example.com/photo1.jpg',
            'created_at': datetime.now()
        },
        {
            'photo_id': uuid.uuid4(),
            'file_name': 'photo2.jpg',
            'file_size': 2048,
            'photo_url': 'http://example.com/photo2.jpg',
            'created_at': datetime.now()
        }
    ]
    mock_cursor.fetchone.side_effect = [
        {'job_report_id': VALID_UUID},  # Mock job report exists
        {'count': 2}  # Mock total count of photos
    ]

    response = client.get(f'/job-report/{VALID_UUID}/photos')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['job_report_id'] == VALID_UUID
    assert result['total_photos'] == 2
    assert len(result['photos']) == 2
    assert result['photos'][0]['file_name'] == 'photo1.jpg'


# Test for invalid job report ID format
def test_list_job_report_photos_invalid_format(client):
    # Test with an invalid job report ID format
    invalid_uuid = 'invalid-uuid'

    response = client.get(f'/job-report/{invalid_uuid}/photos')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "Invalid job report ID format"


# Test for job report not found
@patch('app.routes.job_report.routes.conn')
def test_list_job_report_photos_not_found(mock_conn, client):
    # Mock cursor behavior to return no job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    response = client.get(f'/job-report/{VALID_UUID}/photos')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == "Job report not found"


# Test for pagination
@patch('app.routes.job_report.routes.conn')
def test_list_job_report_photos_pagination(mock_conn, client):
    # Mock cursor behavior for pagination
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {
            'photo_id': uuid.uuid4(),
            'file_name': 'photo1.jpg',
            'file_size': 1024,
            'photo_url': 'http://example.com/photo1.jpg',
            'created_at': datetime.now()
        }
    ]
    mock_cursor.fetchone.side_effect = [
        {'job_report_id': VALID_UUID},  # Mock job report exists
        {'count': 10}  # Mock total count of photos
    ]

    response = client.get(f'/job-report/{VALID_UUID}/photos?page=2&limit=5')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['page'] == 2
    assert result['limit'] == 5
    assert result['total_photos'] == 10
    assert len(result['photos']) == 1


# Test for handling unexpected errors
@patch('app.routes.job_report.routes.conn')
def test_list_job_report_photos_unexpected_error(mock_conn, client):
    # Mock cursor behavior to raise an unexpected exception
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Unexpected error")

    response = client.get(f'/job-report/{VALID_UUID}/photos')

    assert response.status_code == 500
    result = json.loads(response.data)
    assert result['error'] == "An error occurred while fetching photos for the job report"


# Test for successful deletion of a photo
@patch('app.routes.job_report.routes.conn')
def test_delete_job_report_photo_success(mock_conn, client):
    # Mock cursor behavior for successful deletion of a photo
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [
        {'job_report_id': VALID_UUID},  # Mock job report exists
        {'photo_id': VALID_PHOTO_ID, 'photo_job_report_id': VALID_UUID},  # Mock photo exists
        {'photo_id': VALID_PHOTO_ID, 'photo_job_report_id': VALID_UUID}  # Mock deleted photo
    ]

    response = client.delete(f'/job-report/{VALID_UUID}/photos/{VALID_PHOTO_ID}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['message'] == "Photo deleted successfully"
    assert result['deleted_photo']['photo_id'] == VALID_PHOTO_ID


# Test for invalid job report ID format
def test_delete_job_report_photo_invalid_job_report_id_format(client):
    # Test with an invalid job report ID format
    invalid_uuid = 'invalid-uuid'

    response = client.delete(f'/job-report/{invalid_uuid}/photos/{VALID_PHOTO_ID}')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "Invalid job report ID or photo ID format"


# Test for invalid photo ID format
def test_delete_job_report_photo_invalid_photo_id_format(client):
    # Test with an invalid photo ID format
    invalid_uuid = 'invalid-uuid'

    response = client.delete(f'/job-report/{VALID_UUID}/photos/{invalid_uuid}')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['error'] == "Invalid job report ID or photo ID format"


# Test for job report not found
@patch('app.routes.job_report.routes.conn')
def test_delete_job_report_photo_job_report_not_found(mock_conn, client):
    # Mock cursor behavior to return no job report
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    response = client.delete(f'/job-report/{VALID_UUID}/photos/{VALID_PHOTO_ID}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == "Job report not found"


# Test for photo not found or does not belong to the job report
@patch('app.routes.job_report.routes.conn')
def test_delete_job_report_photo_photo_not_found(mock_conn, client):
    # Mock cursor behavior to return job report but no photo
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [
        {'job_report_id': VALID_UUID},  # Mock job report exists
        None  # Mock photo does not exist
    ]

    response = client.delete(f'/job-report/{VALID_UUID}/photos/{VALID_PHOTO_ID}')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == "Photo not found or does not belong to the specified job report"

