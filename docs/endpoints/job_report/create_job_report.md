# Create Job Report API

## Endpoint

`POST /job_report/`

## Description
Creates a new job report with details about the completed job, payment, and client information.

## Request Format

### Headers
- `Content-Type: application/json`

### JSON Body Parameters
| Parameter                | Type    | Required | Description |
|--------------------------|---------|----------|-------------|
| `account_id`            | UUID    | Yes      | The ID of the user account from the `account` table. |
| `latitude`              | float   | No       | Latitude of the job location. |
| `longitude`             | float   | No       | Longitude of the job location. |
| `amount_received_dollars` | float   | Yes      | The amount received for the job in dollars. |
| `payment_method`        | string  | Yes      | The payment method used (e.g., Cash, Card, PayPal). |
| `job_description`       | string  | Yes      | Description of the completed job. |
| `client_name`           | string  | Yes      | Name of the client. |
| `client_contact`        | string  | Yes      | Contact information of the client. |
| `job_status`            | string  | Yes      | Status of the job (e.g., completed, pending). Defaults to `completed` if not provided. |
| `notes`                 | string  | No       | Additional notes about the job. |

## Response Format

### Success Response (201 Created)
```json
{
    "message": "Job report created successfully",
    "job_report_id": "<UUID>"
}
```

### Error Responses
#### 400 Bad Request (Missing or Invalid Data)
```json
{
    "message": "Missing required field: amount_received_dollars"
}
```
```json
{
    "message": "Invalid account ID format."
}
```

#### 401 Unauthorized
```json
{
    "message": "Unauthorized access."
}
```

#### 500 Internal Server Error
```json
{
    "error": "An unexpected error occurred."
}
```

## Example Request
```bash
curl -X POST "http://localhost:5000/job_report/" \
     -H "Content-Type: application/json" \
     -d '{
        "account_id": "550e8400-e29b-41d4-a716-446655440000",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "amount_received_dollars": 150.00,
        "payment_method": "Cash",
        "job_description": "Deep cleaning of a 2-bedroom apartment.",
        "client_name": "John Doe",
        "client_contact": "john.doe@example.com",
        "job_status": "completed",
        "notes": "Client was very satisfied with the service."
     }'
```

## Notes
- The `account_id` must be a valid UUID.
- The `job_status` field defaults to `completed` if not provided.
- Ensure all required fields are included in the request to avoid validation errors.

