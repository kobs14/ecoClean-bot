# Register Endpoint

Creates a new user account in the system.

## Endpoint

`POST /register`

## Description

This endpoint receives account information, validates the input, and creates a new account in the database. It handles required and optional fields, performs data validation, and manages potential conflicts such as duplicate usernames or phone numbers.

## Request

### Headers

- Content-Type: application/json

### Body

```json
{
  "username": "string",
  "fullname": "string",
  "phone": "string",
  "password": "string",
  "is_admin": boolean,           (optional)
  "commission_rate": number,     (optional)
  "status": "string"             (optional, defaults to "active")
}
```

### Fields

| Field           | Type    | Required | Description                                    |
|-----------------|---------|----------|------------------------------------------------|
| username        | string  | Yes      | Unique username for the account                |
| fullname        | string  | Yes      | Full name of the user                          |
| phone           | string  | Yes      | Phone number (must be unique)                  |
| password        | string  | Yes      | Password for the account (will be hashed)      |
| is_admin        | boolean | No       | Whether the account has admin privileges       |
| commission_rate | number  | No       | Commission rate for the account                |
| status          | string  | No       | Account status (defaults to "active")          |

## Response

### Success Response

- **Code:** 201 Created
- **Content:**
  ```json
  {
    "message": "Account created successfully"
  }
  ```

### Error Responses

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Missing required field: [field_name]" }`
  - **Content:** `{ "message": "[Validation error message]" }`

- **Code:** 409 Conflict
  - **Content:** `{ "message": "Username already exists." }`
  - **Content:** `{ "message": "Phone number already exists." }`

- **Code:** 500 Internal Server Error
  - **Content:** `{ "error": "An unexpected error occurred." }`

## Notes

- The password is hashed before storing in the database.
- The endpoint checks for unique constraints on username and phone number.
- Optional fields (is_admin, commission_rate, status) are only processed if provided in the request.
- The default status for a new account is "active" if not specified.

## Example

### Request

```http
POST /register HTTP/1.1
Content-Type: application/json

{
  "username": "johndoe",
  "fullname": "John Doe",
  "phone": "+1234567890",
  "password": "securepassword123",
  "is_admin": false,
  "commission_rate": 0.05
}
```

### Success Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "message": "Account created successfully"
}
```

### Error Response (Duplicate Username)

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "message": "Username already exists."
}
```