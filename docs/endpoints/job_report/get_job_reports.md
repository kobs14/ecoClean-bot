## Get All Job Reports

### Endpoint
`GET /all-reports`

### Description
Retrieve a paginated list of job reports with optional filtering by job status.

### Query Parameters
- `page` (int, optional, default=1): The page number for pagination.
- `limit` (int, optional, default=10): The number of job reports per page.
- `status` (string, optional): Filter job reports by job status.

### Responses
#### Success Response (200 OK)
**Response Body:**
```json
{
  "total_reports": 45,
  "page": 1,
  "limit": 10,
  "job_reports": [
    {
      "job_report_id": "550e8400-e29b-41d4-a716-446655440000",
      "report_by_account_id": "550e8400-e29b-41d4-a716-446655440001",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "created_at": "2024-02-12T10:00:00Z",
      "amount_received_dollars": 150.00,
      "payment_method": "Cash",
      "job_description": "Window cleaning service",
      "client_name": "John Doe",
      "client_contact": "+1234567890",
      "job_status": "Completed",
      "notes": "Client was satisfied",
      "updated_at": "2024-02-12T12:00:00Z"
    }
  ]
}
```

#### Error Responses
**400 Bad Request**
- Invalid query parameters.
```json
{
  "error": "Invalid query parameters."
}
```

**500 Internal Server Error**
- Unexpected error occurred while fetching job reports.
```json
{
  "error": "Failed to fetch job reports."
}
```

### Example Request
```
GET /all-reports?page=1&limit=5&status=Completed
```

### Notes
- The results are ordered by `created_at` in descending order.
- If no `status` is provided, all job reports are retrieved.
- Default pagination is set to 10 reports per page.

