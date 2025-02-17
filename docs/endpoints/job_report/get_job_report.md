## Get Job Report

### Endpoint
`GET /<job_report_id>`

### Description
Retrieve details of a specific job report by its unique identifier.

### Path Parameters
| Parameter      | Type   | Required | Description                 |
|--------------|--------|----------|-----------------------------|
| job_report_id | UUID  | Yes      | Unique ID of the job report |

### Responses

#### 200 - Job report details retrieved successfully
```json
{
  "job_report_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_by_account_id": "123e4567-e89b-12d3-a456-426614174000",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "created_at": "2024-02-12T10:00:00Z",
  "amount_received_dollars": 150.0,
  "payment_method": "Credit Card",
  "job_description": "Office cleaning service",
  "client_name": "John Doe",
  "client_contact": "johndoe@example.com",
  "job_status": "Completed",
  "notes": "Customer requested extra vacuuming",
  "updated_at": "2024-02-12T12:00:00Z"
}
```

#### 400 - Invalid job report ID format
```json
{
  "error": "Invalid job report ID format"
}
```

#### 404 - Job report not found
```json
{
  "error": "Job report not found"
}
```

#### 500 - Unexpected error occurred
```json
{
  "error": "An error occurred while fetching the job report"
}
```

