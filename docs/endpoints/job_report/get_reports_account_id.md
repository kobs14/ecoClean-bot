## GET /<account_id>/reports

### Description
Retrieve all job reports associated with a specific account.

### Path Parameters
- `account_id` (UUID, required): The unique identifier of the account.

### Responses
#### Success (200)
- **Description:** Reports data retrieved successfully.
- **Response Body:**
  ```json
  {
    "reports": [
      {
        "job_report_id": "550e8400-e29b-41d4-a716-446655440000",
        "report_by_account_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "created_at": "2024-02-12T15:04:05Z",
        "amount_received_dollars": 150.0,
        "payment_method": "Cash",
        "job_description": "Deep cleaning service",
        "client_name": "John Doe",
        "client_contact": "johndoe@example.com",
        "job_status": "Completed",
        "notes": "Client requested extra window cleaning.",
        "updated_at": "2024-02-12T16:30:00Z"
      }
    ]
  }
  ```

#### Client Errors
- **400 Bad Request:** Invalid account ID format.
  ```json
  {
    "message": "Invalid account ID format."
  }
  ```
- **404 Not Found:** No reports found for this account.
  ```json
  {
    "message": "No reports found for this account."
  }
  ```

#### Server Errors
- **500 Internal Server Error:** Unexpected error occurred.
  ```json
  {
    "error": "An error occurred while fetching the reports."
  }
  ```

### Notes
- The reports are returned in descending order of `created_at`.
- If no reports exist for the given account, a `404 Not Found` response is returned.

