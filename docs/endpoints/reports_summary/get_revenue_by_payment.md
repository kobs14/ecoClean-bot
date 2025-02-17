# Revenue by Payment Method

## Endpoint: `/revenue-by-payment-method`

### Method: `GET`

### Description
Retrieve revenue breakdown by payment methods within a specified date range.

### Query Parameters
- `start_date` (string, required): The start of the date range in `YYYY-MM-DD` format.
- `end_date` (string, required): The end of the date range in `YYYY-MM-DD` format.

### Responses
#### Success (200)
Returns a JSON object containing payment methods and their corresponding total revenues.

```json
[
  {
    "payment_method": "Cash",
    "total_revenue": 1500.00
  },
  {
    "payment_method": "Credit Card",
    "total_revenue": 1200.50
  }
]
```

#### Client Error (400)
Occurs when required parameters are missing or have an invalid format.

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

#### Server Error (500)
Occurs when an unexpected error happens on the server.

```json
{
  "error": "Internal server error message"
}
```

