# Search Accounts Endpoint

Searches for accounts based on a provided search term.

## Endpoint

`GET /accounts/search`

## Description

This endpoint allows searching for accounts based on a provided search term. The search is performed on the username, full name, and phone number fields of the accounts.

## Request

### Query Parameters

- `q` (string, required): The search term to use for finding accounts.

### Headers

No specific headers required.

## Response

### Success Response

- **Code:** 200 OK
- **Content:** An array of account objects matching the search criteria. Each account object contains all fields from the account table.

Example:
```json
[
  {
    "account_id": "uuid",
    "account_username": "string",
    "account_fullname": "string",
    "account_phone": "string",
    "account_is_admin": boolean,
    "account_commission_rate": number,
    "account_status": "string"
    // ... other account fields
  },
  // ... more account objects
]
```

### Error Responses

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Search term cannot be empty." }`
  - **Description:** When no search term is provided.

- **Code:** 404 Not Found
  - **Content:** `{ "message": "No accounts found." }`
  - **Description:** When no accounts match the provided search term.

- **Code:** 500 Internal Server Error
  - **Content:** `{ "error": "Error message description" }`
  - **Description:** When an unexpected error occurs during the search process.

## Notes

- The search is case-insensitive.
- The search term is matched against the username, full name, and phone number fields.
- Results are ordered alphabetically by the account's full name.
- The search uses partial matching, so a search term can match any part of the username, full name, or phone number.

## Example

### Request

```http
GET /accounts/search?q=john HTTP/1.1
Host: your-api-domain.com
```

### Success Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "account_id": "123e4567-e89b-12d3-a456-426614174000",
    "account_username": "johndoe",
    "account_fullname": "John Doe",
    "account_phone": "+1234567890",
    "account_is_admin": false,
    "account_commission_rate": 0.05,
    "account_status": "active"
  },
  {
    "account_id": "223e4567-e89b-12d3-a456-426614174001",
    "account_username": "johnsmith",
    "account_fullname": "John Smith",
    "account_phone": "+1987654321",
    "account_is_admin": true,
    "account_commission_rate": 0.1,
    "account_status": "active"
  }
]
```

### Error Response (Empty Search Term)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "message": "Search term cannot be empty."
}
```

### Error Response (No Results)

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "message": "No accounts found."
}
```