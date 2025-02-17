# Update Telegram Verified Endpoint

Updates the `telegram_verified` field of an existing Telegram entry.

## Endpoint

PUT /<telegram_id>/verified

## Description

This endpoint updates the `telegram_verified` field for a specific Telegram entry in the database. It allows the user to change the verification status of a Telegram account. The request must contain the `telegram_verified` field, and the provided `telegram_id` will be validated.

## Request

### Headers

- Content-Type: application/json

### URL Parameters

| Parameter    | Type   | Required | Description                    |
|--------------|--------|----------|--------------------------------|
| telegram_id  | UUID   | Yes      | Unique identifier for the Telegram entry |

### Body

```json
{
  "telegram_verified": boolean
}