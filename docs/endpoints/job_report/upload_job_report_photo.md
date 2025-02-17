# Upload Job Report Photo

## Endpoint
`POST /job_report/{job_report_id}/photos`

## Description
This endpoint allows users to upload a photo for a specific job report. The uploaded file is stored using a storage abstraction.

## Path Parameters
| Parameter       | Type  | Required | Description                  |
|----------------|-------|----------|------------------------------|
| `job_report_id` | UUID  | Yes      | The ID of the job report. |

## Request Format
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: The photo file to be uploaded (PNG, JPG, JPEG formats only).

## Response

### Success Response
**201 Created**
```json
{
    "message": "Photo uploaded successfully"
}
```

### Error Responses
| Status Code | Message |
|-------------|---------|
| 400 Bad Request | `{ "message": "No file part in the request." }` |
| 400 Bad Request | `{ "message": "No selected file." }` |
| 400 Bad Request | `{ "message": "Invalid file format. Only PNG, JPG, and JPEG are allowed." }` |
| 400 Bad Request | `{ "message": "Invalid account ID format." }` |
| 404 Not Found | `{ "message": "Job report not found." }` |
| 500 Internal Server Error | `{ "error": "An error occurred while uploading the photo." }` |

## Notes
- The file name and size are stored in the database along with the generated photo URL.
- The file is uploaded to a specific storage location using a storage abstraction.
- The job report ID is validated before the upload is processed.
- Only files with `.png`, `.jpg`, and `.jpeg` extensions are allowed.

