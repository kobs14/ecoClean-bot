# Summary Report Endpoint Documentation



## Endpoint: `/employee-performance`

### Method: `GET`

### Description
Retrieves employee performance data based on the provided `start_date`, `end_date`, and optional `employee_id` parameter.

### Query Parameters
| Parameter   | Type   | Required | Description |
|------------|--------|----------|-------------|
| `start_date` | `string` | Yes | The start date for the performance report in `YYYY-MM-DD` format. |
| `end_date` | `string` | Yes | The end date for the performance report in `YYYY-MM-DD` format. |
| `employee_id` | `string` | No | The unique identifier of the employee to filter results. |

### Response

#### Success Response (200)
Returns a JSON object containing employee performance data.

**Example Response:**
```json
[
    {
        "employee_id": "1234",
        "total_jobs": 15,
        "total_earnings": 2500.00
    }
]
```

#### Error Responses
- **400 Bad Request**: Invalid input, such as missing dates.
  ```json
  { "error": "start_date and end_date are required" }
  ```

- **500 Internal Server Error**: If an unexpected error occurs while retrieving the data.
  ```json
  { "error": "Server error" }
  ```

### Implementation Notes
- Logs request parameters for debugging.
- Validates required fields.
- Calls `get_employee_performance_data` to retrieve performance metrics.
- Handles errors gracefully and logs them appropriately.

### Example Usage
#### Request:
```
GET /employee-performance?start_date=2024-02-01&end_date=2024-02-07&employee_id=1234
```
#### Response:
```json
[
    {
        "employee_id": "1234",
        "total_jobs": 15,
        "total_earnings": 2500.00
    }
]
```

