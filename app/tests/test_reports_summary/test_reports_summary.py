import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import json
from psycopg2.extras import RealDictCursor

from app.main import create_app


@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# Test successful report generation
@patch('app.reports_summary.routes.conn')
def test_get_summary_report_success(mock_conn, client):
    # Mock cursor and query results
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Sample query results
    mock_results = [
        {
            'period': datetime(2024, 1, 1),
            'job_count': 5,
            'total_amount': 750.50
        },
        {
            'period': datetime(2024, 1, 2),
            'job_count': 3,
            'total_amount': 450.25
        }
    ]
    mock_cursor.fetchall.return_value = mock_results

    # Make request
    response = client.get('/reports/summary?start_date=2024-01-01&end_date=2024-01-31&group_by=day')

    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['job_count'] == 5
    assert data[0]['total_amount'] == 750.50

    # Verify correct SQL parameters
    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args[0]
    assert 'DATE_TRUNC' in call_args[0]  # SQL query
    assert call_args[1] == ('day', datetime(2024, 1, 1), datetime(2024, 1, 31))  # Parameters


# Test missing dates
def test_get_summary_report_missing_dates(client):
    # Test missing start_date
    response = client.get('/reports/summary?end_date=2024-01-31')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data

    # Test missing end_date
    response = client.get('/reports/summary?start_date=2024-01-01')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data


# Test invalid date format
def test_get_summary_report_invalid_date_format(client):
    # Test invalid start_date format
    response = client.get('/reports/summary?start_date=2024/01/01&end_date=2024-01-31')
    assert response.status_code == 400
    assert b"Invalid date format" in response.data

    # Test invalid end_date format
    response = client.get('/reports/summary?start_date=2024-01-01&end_date=01-31-2024')
    assert response.status_code == 400
    assert b"Invalid date format" in response.data


# Test invalid group_by parameter
def test_get_summary_report_invalid_group_by(client):
    response = client.get('/reports/summary?start_date=2024-01-01&end_date=2024-01-31&group_by=invalid')
    assert response.status_code == 400
    assert b"Invalid group_by" in response.data

    # Verify error message includes valid options
    data = json.loads(response.data)
    assert all(group in data['error'] for group in ['day', 'week', 'month', 'year'])


# Test database error handling
@patch('app.reports_summary.routes.conn')
def test_get_summary_report_database_error(mock_conn, client):
    # Mock database error
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database connection error")

    response = client.get('/reports/summary?start_date=2024-01-01&end_date=2024-01-31')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "Database connection error" in data['error']


# Test different group_by values
@patch('app.reports_summary.routes.conn')
def test_get_summary_report_group_by_options(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    group_by_options = ['day', 'week', 'month', 'year']

    for group_by in group_by_options:
        response = client.get(f'/reports/summary?start_date=2024-01-01&end_date=2024-01-31&group_by={group_by}')
        assert response.status_code == 200

        # Verify correct group_by parameter was passed to query
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1][0] == group_by



###

# Test successful performance report retrieval
@patch('app.reports_summary.routes.get_employee_performance_data')
def test_get_employee_performance_success(mock_get_data, client):
    # Mock performance data
    mock_data = {
        'total_jobs': 15,
        'completed_jobs': 12,
        'average_rating': 4.8,
        'total_revenue': 2500.50,
        'performance_metrics': {
            'efficiency_score': 0.85,
            'customer_satisfaction': 0.92
        }
    }
    mock_get_data.return_value = mock_data

    # Test with all parameters
    response = client.get('/reports/employee-performance?start_date=2024-01-01&end_date=2024-01-31&employee_id=12345')

    assert response.status_code == 200
    data = json.loads(response.data)

    # Verify response content
    assert data['total_jobs'] == 15
    assert data['completed_jobs'] == 12
    assert data['average_rating'] == 4.8
    assert data['total_revenue'] == 2500.50
    assert 'performance_metrics' in data

    # Verify function call
    mock_get_data.assert_called_once_with('2024-01-01', '2024-01-31', '12345')


# Test without employee_id (should return all employees)
@patch('app.reports_summary.routes.get_employee_performance_data')
def test_get_employee_performance_no_employee_id(mock_get_data, client):
    mock_data = [
        {'employee_id': '12345', 'total_jobs': 15},
        {'employee_id': '67890', 'total_jobs': 20}
    ]
    mock_get_data.return_value = mock_data

    response = client.get('/reports/employee-performance?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2

    # Verify function call with None employee_id
    mock_get_data.assert_called_once_with('2024-01-01', '2024-01-31', None)


# Test missing required parameters
def test_get_employee_performance_missing_params(client):
    # Missing start_date
    response = client.get('/reports/employee-performance?end_date=2024-01-31')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data

    # Missing end_date
    response = client.get('/reports/employee-performance?start_date=2024-01-01')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data


# Test validation error handling
@patch('app.reports_summary.routes.get_employee_performance_data')
def test_get_employee_performance_validation_error(mock_get_data, client):
    # Mock validation error
    mock_get_data.side_effect = ValueError("Invalid date format")

    response = client.get('/reports/employee-performance?start_date=2024-01-01&end_date=2024-01-31&employee_id=12345')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Invalid date format" in data['error']


# Test server error handling
@patch('app.reports_summary.routes.get_employee_performance_data')
def test_get_employee_performance_server_error(mock_get_data, client):
    # Mock server error
    mock_get_data.side_effect = Exception("Database connection error")

    response = client.get('/reports/employee-performance?start_date=2024-01-01&end_date=2024-01-31&employee_id=12345')

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "Database connection error" in data['error']


# Test with invalid employee_id format
@patch('app.reports_summary.routes.get_employee_performance_data')
def test_get_employee_performance_invalid_employee_id(mock_get_data, client):
    mock_get_data.side_effect = ValueError("Invalid employee ID format")

    response = client.get('/reports/employee-performance?start_date=2024-01-01&end_date=2024-01-31&employee_id=invalid')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Invalid employee ID format" in data['error']


# Test date range validation
@patch('app.reports_summary.routes.get_employee_performance_data')
def test_get_employee_performance_invalid_date_range(mock_get_data, client):
    mock_get_data.side_effect = ValueError("End date must be after start date")

    response = client.get('/reports/employee-performance?start_date=2024-01-31&end_date=2024-01-01&employee_id=12345')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "End date must be after start date" in data['error']


###


# Test successful retrieval of top clients
@patch('app.reports_summary.routes.conn')
def test_get_top_clients_success(mock_conn, client):
    # Mock cursor and query results
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_results = [
        {
            'client_name': 'John Doe',
            'client_contact': '+1234567890',
            'total_spent': 5000.50
        },
        {
            'client_name': 'Jane Smith',
            'client_contact': '+0987654321',
            'total_spent': 3500.75
        }
    ]
    mock_cursor.fetchall.return_value = mock_results

    # Test with default limit
    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['client_name'] == 'John Doe'
    assert data[0]['total_spent'] == 5000.50

    # Verify SQL query parameters
    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args[0]
    sql_query = call_args[0].lower().replace('\n', ' ').replace(' ', '')
    assert 'orderbytotal_spentdesc' in sql_query
    assert 'limit%s' in sql_query
    assert 'groupbyjr.client_name,jr.client_contact' in sql_query

    # Verify parameters
    query_params = call_args[1]
    assert len(query_params) == 3
    assert isinstance(query_params[0], datetime)  # start_date
    assert isinstance(query_params[1], datetime)  # end_date
    assert query_params[2] == 10  # default limit


# Test with custom limit
@patch('app.reports_summary.routes.conn')
def test_get_top_clients_custom_limit(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=2024-01-31&limit=5')

    assert response.status_code == 200
    call_args = mock_cursor.execute.call_args[0]
    assert call_args[1][2] == 5  # Custom limit


# Test invalid limit values
def test_get_top_clients_invalid_limit(client):
    # Test negative limit
    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=2024-01-31&limit=-1')
    assert response.status_code == 400
    assert b"Limit must be a positive integer" in response.data

    # Test zero limit
    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=2024-01-31&limit=0')
    assert response.status_code == 400
    assert b"Limit must be a positive integer" in response.data


# Test missing required parameters
def test_get_top_clients_missing_params(client):
    # Missing start_date
    response = client.get('/reports/top-clients?end_date=2024-01-31')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data

    # Missing end_date
    response = client.get('/reports/top-clients?start_date=2024-01-01')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data


# Test invalid date format
def test_get_top_clients_invalid_date_format(client):
    # Invalid start_date format
    response = client.get('/reports/top-clients?start_date=2024/01/01&end_date=2024-01-31')
    assert response.status_code == 400
    assert b"Invalid date format" in response.data

    # Invalid end_date format
    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=01-31-2024')
    assert response.status_code == 400
    assert b"Invalid date format" in response.data


# Test database error handling
@patch('app.reports_summary.routes.conn')
def test_get_top_clients_database_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database connection error")

    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "Database connection error" in data['error']


# Test empty results
@patch('app.reports_summary.routes.conn')
def test_get_top_clients_empty_results(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 0


# Test result ordering
@patch('app.reports_summary.routes.conn')
def test_get_top_clients_ordering(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_results = [
        {'client_name': 'Client A', 'total_spent': 1000.00},
        {'client_name': 'Client B', 'total_spent': 500.00},
        {'client_name': 'Client C', 'total_spent': 250.00}
    ]
    mock_cursor.fetchall.return_value = mock_results

    response = client.get('/reports/top-clients?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3
    assert data[0]['total_spent'] > data[1]['total_spent']
    assert data[1]['total_spent'] > data[2]['total_spent']


###

# Test successful retrieval of revenue by payment method
@patch('app.reports_summary.routes.conn')
def test_get_revenue_by_payment_method_success(mock_conn, client):
    # Mock cursor and query results
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_results = [
        {
            'payment_method': 'Credit Card',
            'total_revenue': 10000.50
        },
        {
            'payment_method': 'Cash',
            'total_revenue': 5500.75
        },
        {
            'payment_method': 'Bank Transfer',
            'total_revenue': 3000.25
        }
    ]
    mock_cursor.fetchall.return_value = mock_results

    response = client.get('/reports/revenue-by-payment-method?start_date=2024-01-01&end_date=2024-01-31')

    # Verify response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3

    # Verify data structure and ordering
    assert data[0]['payment_method'] == 'Credit Card'
    assert data[0]['total_revenue'] == 10000.50
    assert data[1]['payment_method'] == 'Cash'
    assert data[2]['payment_method'] == 'Bank Transfer'

    # Verify SQL query
    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args[0]
    sql_query = call_args[0].lower().replace('\n', ' ').replace(' ', '')

    # Check essential query components
    assert 'groupbyjr.payment_method' in sql_query
    assert 'orderbytotal_revenuedesc' in sql_query
    assert "jr.job_status='completed'" in sql_query.replace(' ', '')

    # Verify parameters
    query_params = call_args[1]
    assert len(query_params) == 2
    assert isinstance(query_params[0], datetime)  # start_date
    assert isinstance(query_params[1], datetime)  # end_date


# Test missing required parameters
def test_get_revenue_by_payment_method_missing_params(client):
    # Missing start_date
    response = client.get('/reports/revenue-by-payment-method?end_date=2024-01-31')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data

    # Missing end_date
    response = client.get('/reports/revenue-by-payment-method?start_date=2024-01-01')
    assert response.status_code == 400
    assert b"start_date and end_date are required" in response.data


# Test invalid date format
def test_get_revenue_by_payment_method_invalid_date_format(client):
    # Invalid start_date format
    response = client.get('/reports/revenue-by-payment-method?start_date=2024/01/01&end_date=2024-01-31')
    assert response.status_code == 400
    assert b"Invalid date format" in response.data

    # Invalid end_date format
    response = client.get('/reports/revenue-by-payment-method?start_date=2024-01-01&end_date=01-31-2024')
    assert response.status_code == 400
    assert b"Invalid date format" in response.data


# Test database error handling
@patch('app.reports_summary.routes.conn')
def test_get_revenue_by_payment_method_database_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database connection error")

    response = client.get('/reports/revenue-by-payment-method?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "Database connection error" in data['error']


# Test empty results
@patch('app.reports_summary.routes.conn')
def test_get_revenue_by_payment_method_empty_results(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    response = client.get('/reports/revenue-by-payment-method?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 0


# Test result totals calculation
@patch('app.reports_summary.routes.conn')
def test_get_revenue_by_payment_method_totals(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_results = [
        {'payment_method': 'Credit Card', 'total_revenue': 1000.00},
        {'payment_method': 'Cash', 'total_revenue': 500.00},
        {'payment_method': 'Bank Transfer', 'total_revenue': 250.00}
    ]
    mock_cursor.fetchall.return_value = mock_results

    response = client.get('/reports/revenue-by-payment-method?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 200
    data = json.loads(response.data)

    # Verify totals and ordering
    total_revenue = sum(item['total_revenue'] for item in data)
    assert total_revenue == 1750.00
    assert all(data[i]['total_revenue'] >= data[i + 1]['total_revenue']
               for i in range(len(data) - 1))


# Test zero revenue cases
@patch('app.reports_summary.routes.conn')
def test_get_revenue_by_payment_method_zero_revenue(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_results = [
        {'payment_method': 'Credit Card', 'total_revenue': 0.00},
        {'payment_method': 'Cash', 'total_revenue': 0.00}
    ]
    mock_cursor.fetchall.return_value = mock_results

    response = client.get('/reports/revenue-by-payment-method?start_date=2024-01-01&end_date=2024-01-31')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(item['total_revenue'] == 0.00 for item in data)



###

# Test basic report with default parameters
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_defaults(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_results = [
        {
            'payment_method': 'Credit Card',
            'job_status': 'completed',
            'job_count': 10,
            'total_revenue': 5000.50
        }
    ]
    mock_cursor.fetchall.return_value = mock_results

    response = client.get('/reports/custom')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1

    # Verify default parameters in SQL query
    mock_cursor.execute.assert_called_once()
    call_args = mock_cursor.execute.call_args[0]
    sql_query = call_args[0].lower()

    assert 'group by payment_method' in sql_query
    assert 'limit 100' in sql_query
    assert len(call_args[1]) == 0  # No parameters with defaults only


# Test with all parameters specified
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_all_params(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    url = ('/reports/custom?'
           'start_date=2024-01-01&'
           'end_date=2024-01-31&'
           'payment_method=Cash&'
           'job_status=completed&'
           'group_by=job_status&'
           'limit=10')

    response = client.get(url)

    assert response.status_code == 200

    # Verify query parameters
    call_args = mock_cursor.execute.call_args[0]
    sql_query = call_args[0].lower()
    params = call_args[1]

    assert 'where' in sql_query
    assert 'created_at >=' in sql_query
    assert 'created_at <=' in sql_query
    assert 'payment_method =' in sql_query
    assert 'job_status =' in sql_query
    assert 'group by job_status' in sql_query
    assert 'limit 10' in sql_query

    assert len(params) == 4  # All filter parameters present


# Test different group by options
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_group_by_options(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    group_by_options = ['payment_method', 'job_status']

    for group_by in group_by_options:
        response = client.get(f'/reports/custom?group_by={group_by}')
        assert response.status_code == 200

        call_args = mock_cursor.execute.call_args[0]
        sql_query = call_args[0].lower()
        assert f'group by {group_by}' in sql_query


# Test different limit values
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_limit_values(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    test_limits = [1, 50, 200]

    for limit in test_limits:
        response = client.get(f'/reports/custom?limit={limit}')
        assert response.status_code == 200

        call_args = mock_cursor.execute.call_args[0]
        sql_query = call_args[0].lower()
        assert f'limit {limit}' in sql_query


# Test date range filters
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_date_filters(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    url = '/reports/custom?start_date=2024-01-01&end_date=2024-01-31'
    response = client.get(url)

    assert response.status_code == 200
    call_args = mock_cursor.execute.call_args[0]
    sql_query = call_args[0].lower()
    params = call_args[1]

    assert 'created_at >=' in sql_query
    assert 'created_at <=' in sql_query
    assert len(params) == 2
    assert params[0] == '2024-01-01'
    assert params[1] == '2024-01-31'


# Test payment method filter
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_payment_method_filter(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    payment_methods = ['Cash', 'Card', 'Bank Transfer']

    for method in payment_methods:
        response = client.get(f'/reports/custom?payment_method={method}')
        assert response.status_code == 200

        call_args = mock_cursor.execute.call_args[0]
        sql_query = call_args[0].lower()
        params = call_args[1]

        assert 'payment_method =' in sql_query
        assert params[0] == method


# Test job status filter
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_job_status_filter(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    statuses = ['completed', 'cancelled', 'pending']

    for status in statuses:
        response = client.get(f'/reports/custom?job_status={status}')
        assert response.status_code == 200

        call_args = mock_cursor.execute.call_args[0]
        sql_query = call_args[0].lower()
        params = call_args[1]

        assert 'job_status =' in sql_query
        assert params[0] == status


# Test database error handling
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_database_error(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("Database connection error")

    response = client.get('/reports/custom')

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "Database connection error" in data['error']


# Test revenue calculations
@patch('app.reports_summary.routes.conn')
def test_get_custom_report_revenue_calculations(mock_conn, client):
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_results = [
        {'payment_method': 'Cash', 'job_count': 5, 'total_revenue': 1000.00},
        {'payment_method': 'Card', 'job_count': 3, 'total_revenue': 750.50}
    ]
    mock_cursor.fetchall.return_value = mock_results

    response = client.get('/reports/custom')

    assert response.status_code == 200
    data = json.loads(response.data)

    total_jobs = sum(item['job_count'] for item in data)
    total_revenue = sum(item['total_revenue'] for item in data)

    assert total_jobs == 8
    assert total_revenue == 1750.50