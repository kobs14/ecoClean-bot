
# Top Clients

## Endpoint: `/top-clients`

### Method: `GET`

### Description
Retrieve the top clients based on total amount spent within a specified date range.

### Query Parameters
- `start_date` (string, required): The start of the date range in `YYYY-MM-DD` format.
- `end_date` (string, required): The end of the date range in `YYYY-MM-DD` format.
- `limit` (integer, optional, default: 10): The number of top clients to return.

### Responses
#### Success (200)
Returns a JSON list of clients with their total amount spent, ordered by total amount spent.

```json
[
  {
    "client_name": "John Doe",
    "client_contact": "john@example.com",
    "total_spent": 5000.00
  },
  {
    "client_name": "Jane Smith",
    "client_contact": "jane@example.com",
    "total_spent": 4200.75
  }
]
```

#### Client Error (400)
Occurs when required parameters are missing, have an invalid format, or when the limit is not a positive integer.

```json
{
  "error": "start_date and end_date are required"
}
```

```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

```json
{
  "error": "Limit must be a positive integer"
}
```

#### Server Error (500)
Occurs when an unexpected error happens on the server.

```json
{
  "error": "Internal server error message"
}
```

