# Update Account Status Endpoint

Updates the status of a specific account.

## Endpoint

`PUT /<id>/status`

## Description

This endpoint allows updating the status of an account identified by its UUID. The status can only be set to either 'active' or 'disabled'.

## Request

### Parameters

- `id` (path parameter): The UUID of the account to be updated.

### Headers

- Content-Type: application/json

### Body

A JSON object containing the new status:

```json
{
  "status": "string"
}
```

The `status` field must be either "active" or "disabled".

## Response

### Success Response

- **Code:** 200 OK
- **Content:** 
```json
{
  "message": "Account status updated to [new_status] successfully"
}
```

### Error Responses

- **Code:** 400 Bad Request
  - **Content:** `{ "message": "Invalid status. Allowed values are 'active' or 'disabled'." }`
  - **Description:** When the provided status is not 'active' or 'disabled'.

- **Code:** 404 Not Found
  - **Content:** `{ "message": "Account not found" }`
  - **Description:** When no account matches the provided ID.

- **Code:** 500 Internal Server Error
  - **Content:** `{ "error": "Error message description" }`
  - **Description:** When an unexpected error occurs during the update process.

## Notes

- The account ID must be in a valid UUID format.
- Only two status values are accepted: 'active' and 'disabled'.
- If the account doesn't exist, a 404 error is returned.

## Example

### Request

```http
PUT /69b107b2-3ec2-4b21-be4e-4e4e85b28421/status HTTP/1.1
Host: your-api-domain.com
Content-Type: application/json

{
  "status": "active"
}
```

### Success Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Account status updated to active successfully"
}
```

### Error Response (Invalid Status)

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "message": "Invalid status. Allowed values are 'active' or 'disabled'."
}
```

### Error Response (Not Found)

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "message": "Account not found"
}
```