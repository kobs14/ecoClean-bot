# Summary Report Endpoint Documentation

## Endpoint: `/summary`

### Method: `GET`

### Description
Retrieves a summary report of job reports based on the provided `start_date`, `end_date`, and optional `group_by` parameter.

### Query Parameters
| Parameter   | Type   | Required | Description |
|------------|--------|----------|-------------|
| `start_date` | `string` | Yes | The start date for the report in `YYYY-MM-DD` format. |
| `end_date` | `string` | Yes | The end date for the report in `YYYY-MM-DD` format. |
| `group_by` | `string` | No | Time grouping for the report (`day`, `week`, `month`, `year`). Defaults to `day`. |

### Response

#### Success Response (200)
Returns a JSON array containing the summary report of job reports grouped by the specified time period.

**Example Response:**
```json
[
    {
        "period": "2024-02-01T00:00:00",
        "job_count": 10,
        "total_amount": 1500.00
    },
    {
        "period": "2024-02-02T00:00:00",
        "job_count": 8,
        "total_amount": 1200.50
    }
]
```

#### Error Responses
- **400 Bad Request**: Invalid input, such as missing dates or incorrect formatting.
  ```json
  { "error": "start_date and end_date are required" }
  ```
  ```json
  { "error": "Invalid date format. Use YYYY-MM-DD" }
  ```
  ```json
  { "error": "Invalid group_by. Must be one of ['day', 'week', 'month', 'year']" }
  ```

- **500 Internal Server Error**: If an unexpected error occurs while retrieving the data.
  ```json
  { "error": "Database connection failed" }
  ```

### Implementation Notes
- Logs request parameters for debugging.
- Validates the date format and required fields.
- Uses SQL `DATE_TRUNC()` for grouping job reports.
- Converts datetime fields to ISO format before returning JSON.
- Handles errors gracefully and logs them appropriately.

### Example Usage
#### Request:
```
GET /summary?start_date=2024-02-01&end_date=2024-02-07&group_by=day
```
#### Response:
```json
[
    {
        "period": "2024-02-01T00:00:00",
        "job_count": 10,
        "total_amount": 1500.00
    }
]
```

