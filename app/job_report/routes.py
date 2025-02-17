
from uuid import UUID
from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor

from app.main import global_conn as conn
from app.config import logger
from .validators import validate_field, allowed_file

from ..storage.storage_factory import get_storage
from ..config import Config

storage = get_storage(Config.STORAGE_TYPE, **Config.STORAGE_CONFIG, subdirectory='job_reports')


job_report_bp = Blueprint('/job-report', __name__)

@job_report_bp.route('/', methods=['POST'])
def create_job_report():
    """
    Create a new job report.

    Request JSON format:
    {
        "latitude": float,
        "longitude": float,
        "amount_received_dollars": float,
        "payment_method": string,
        "job_description": string,
        "client_name": string,
        "client_contact": string,
        "job_status": string,
        "notes": string
    }

    Returns:
    - 201: Job report created successfully with job report ID.
    - 400: Missing required field or invalid input.
    - 401: Unauthorized access.
    - 500: Unexpected error occurred.
    """
    data = request.json
    logger.info(f"Received request to create job report")

    required_fields = {
        'account_id': "UUID",       # The ID of the user account from the 'account' table (must be a valid UUID).
        'amount_received_dollars': float,
        'payment_method': str,
        'job_description': str,
        'client_name': str,
        'client_contact': str,
        'job_status': str
    }

    job_report_data = {}

    # Validate required fields
    for field, field_type in required_fields.items():
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
        if field == 'account_id':
            continue
        try:
            job_report_data[field] = validate_field(field, data[field], field_type)
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    try:
        account_id = str(UUID(data['account_id']))
    except ValueError:
        logger.error(f"Invalid telegram account ID format received: {data['account_id']}")
        return jsonify({"message": "Invalid telegram account ID format."}), 400

    # Validate optional fields
    optional_fields = {
        'latitude': float,
        'longitude': float,
        'job_status': str,
        'notes': str
    }

    for field, field_type in optional_fields.items():
        if field in data:
            try:
                job_report_data[field] = validate_field(field, data[field], field_type)
            except ValueError as e:
                return jsonify({"message": str(e)}), 400

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO job_report (
                    report_by_account_id, latitude, longitude, amount_received_dollars,
                    payment_method, job_description, client_name, client_contact,
                    job_status, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING job_report_id
                """,
                (
                    account_id,
                    job_report_data.get('latitude'),
                    job_report_data.get('longitude'),
                    job_report_data['amount_received_dollars'],
                    job_report_data['payment_method'],
                    job_report_data['job_description'],
                    job_report_data['client_name'],
                    job_report_data['client_contact'],
                    job_report_data.get('job_status', 'completed'),
                    job_report_data.get('notes')
                )
            )
            # job_report_id = cursor.fetchone()[0]
            conn.commit()

        # logger.info(f"Job report created successfully, ID: {job_report_id}")
        logger.info(f"Job report created successfully, ID:")
        # return jsonify({"message": "Job report created successfully", "job_report_id": job_report_id}), 201
        return jsonify({"message": "Job report created successfully", "client_name": job_report_data}), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating job report: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500



@job_report_bp.route('/<job_report_id>/photos', methods=['POST'])
def upload_job_report_photo(job_report_id):
    """
    Upload a photo for a specific job report using storage abstraction.

    Path Parameters:
    - job_report_id: UUID of the job report.

    Request format (multipart/form-data):
    - 'file': The photo file to be uploaded.

    Returns:
    - 201: Photo uploaded successfully with photo ID.
    - 400: Invalid file or missing required fields.
    - 401: Unauthorized access.
    - 404: Job report not found.
    - 500: Unexpected error occurred.
    """

    logger.info(f"Received request to upload photo for job report: {job_report_id}")

    # Check if the 'file' key is in the request.files
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request."}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No selected file."}), 400

    # Check if the file has a valid extension
    if not allowed_file(file.filename):
        return jsonify({"message": "Invalid file format. Only PNG, JPG, and JPEG are allowed."}), 400

    try:
        job_report_id = str(UUID(job_report_id))
    except ValueError:
        logger.error(f"Invalid account ID format received: {job_report_id}")
        return jsonify({"message": "Invalid account ID format."}), 400

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT job_report_id FROM job_report WHERE job_report_id = %s", (str(job_report_id),))
            if cursor.fetchone() is None:
                return jsonify({"message": "Job report not found."}), 404

    except Exception as e:
        logger.error(f"Error checking job report existence: {str(e)}")
        return jsonify({"error": "An unexpected error occurred while checking the job report."}), 500

    try:
        filename = file.filename

        file_url = storage.save_file(file, filename, subfolder=job_report_id)
        logger.info(f"Photo saved in: {file_url}")

        # Ensure the file pointer is reset to the beginning before reading the content length
        file.seek(0)

        # Get the file size from the uploaded file object
        file_size = file.content_length if file.content_length else len(file.read())

        # Reset the file pointer again to the beginning in case you need to read the file again later
        file.seek(0)

        logger.info(f"file_size: {file_size}")

        # Insert the photo into the database
        with conn.cursor() as cursor:
            cursor.execute("""
                    INSERT INTO report_photos (photo_job_report_id, file_name, file_size, photo_url, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (job_report_id, filename, file_size, file_url))

            conn.commit()

        logger.info(f"Photo uploaded and saved to {filename}")
        return jsonify({"message": "Photo uploaded successfully"}), 201

    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        return jsonify({"error": "An error occurred while uploading the photo."}), 500

@job_report_bp.route('/<account_id>/reports', methods=['GET'])
def get_reports_account_id(account_id):
    """
    Get all reports for a specific account ID.

    Path Parameters:
    - account_id: UUID of the account.

    Returns:
    - 200: Reports data retrieved successfully.
    - 400: Invalid account ID format.
    - 404: No reports found.
    - 500: Unexpected error occurred.
    """
    logger.info(f"Received request to get reports for account: {account_id}")

    try:
        # Validate account_id format
        account_id = str(UUID(account_id))
    except ValueError:
        logger.error(f"Invalid account ID format received: {account_id}")
        return jsonify({"message": "Invalid account ID format."}), 400

    try:
        # Fetch all report data from the database for the given account
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM job_report
                WHERE report_by_account_id = %s
                ORDER BY created_at DESC
            """, (account_id,))
            reports = cursor.fetchall()

        if not reports:
            return jsonify({"message": "No reports found for this account."}), 404
        # Convert report data to a list of dictionaries
        reports_data = []
        for report in reports:
            report_data = {
                "job_report_id": str(report['job_report_id']),
                "report_by_account_id": str(report['report_by_account_id']),
                "latitude": float(report['latitude']) if report['latitude'] is not None else None,
                "longitude": float(report['longitude']) if report['longitude'] is not None else None,
                "created_at": report['created_at'].isoformat() if report['created_at'] is not None else None,
                "amount_received_dollars": float(report['amount_received_dollars']),
                "payment_method": report['payment_method'],
                "job_description": report['job_description'],
                "client_name": report['client_name'],
                "client_contact": report['client_contact'],
                "job_status": report['job_status'],
                "notes": report['notes'],
                "updated_at": report['updated_at'].isoformat() if report['updated_at'] is not None else None
            }
            reports_data.append(report_data)

        return jsonify({"reports": reports_data}), 200

    except Exception as e:
        logger.error(f"Error fetching reports: {str(e)}")
        return jsonify({"error": "An error occurred while fetching the reports."}), 500


@job_report_bp.route('/all-reports', methods=['GET'])
def get_job_reports():
    """
    Get all job reports with pagination and optional status filtering.

    Query Parameters:
    - page: int, optional (default=1) - Page number for pagination
    - limit: int, optional (default=10) - Number of items per page
    - status: str, optional - Filter reports by job status

    Returns:
    - 200: List of job reports, total count, and pagination info
    - 400: Invalid query parameters
    - 500: Unexpected error occurred
    """

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    # Extract any filters from query parameters
    filters = []
    filter_values = []
    if 'status' in request.args:
        filters.append("job_status = %s")
        filter_values.append(request.args.get('status'))

    # Create the SQL query for pagination and filtering
    filter_query = " AND ".join(filters) if filters else "1=1"
    offset = (page - 1) * limit

    query = f"""
        SELECT job_report_id, report_by_account_id, latitude, longitude, 
               created_at, amount_received_dollars, payment_method, 
               job_description, client_name, client_contact, job_status, 
               notes, updated_at
        FROM job_report
        WHERE {filter_query}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (*filter_values, limit, offset))
            job_reports = cursor.fetchall()

            # Get total count of job reports
            count_query = f"SELECT COUNT(*) FROM job_report WHERE {filter_query}"
            cursor.execute(count_query, filter_values)
            total_reports = cursor.fetchone()['count']

    except Exception as e:
        logger.error(f"Error fetching job reports: {e}")
        return jsonify({'error': 'Failed to fetch job reports.'}), 500

    # Prepare response data
    response = {
        'total_reports': total_reports,
        'page': page,
        'limit': limit,
        'job_reports': [dict(report) for report in job_reports]
    }

    return jsonify(response), 200


@job_report_bp.route('/<job_report_id>', methods=['GET'])
def get_job_report(job_report_id):
    """
    Get details of a specific job report.

    Path Parameters:
    - job_report_id: UUID of the job report

    Returns:
    - 200: Job report details retrieved successfully
    - 400: Invalid job report ID format
    - 404: Job report not found
    - 500: Unexpected error occurred
    """
    try:
        # Validate job_report_id format
        job_report_id = str(UUID(job_report_id))
    except ValueError:
        return jsonify({"error": "Invalid job report ID format"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM job_report
                WHERE job_report_id = %s
            """, (job_report_id,))

            job_report = cursor.fetchone()

            if not job_report:
                return jsonify({"error": "Job report not found"}), 404

            return jsonify(job_report), 200

    except Exception as e:
        logger.error(f"Error fetching job report: {e}")
        return jsonify({"error": "An error occurred while fetching the job report"}), 500


@job_report_bp.route('/<job_report_id>', methods=['PUT'])
def update_job_report(job_report_id):
    """
    Update a job report.

    Path Parameters:
    - job_report_id: UUID of the job report to update

    Request Body:
    - JSON object containing the fields to update

    Returns:
    - 200: Job report updated successfully
    - 400: Invalid job report ID format or invalid request body
    - 404: Job report not found
    - 500: Unexpected error occurred
    """
    try:
        # Validate job_report_id format
        job_report_id = str(UUID(job_report_id))
    except ValueError:
        return jsonify({"error": "Invalid job report ID format"}), 400

    # Get the request data
    data = request.json
    if not data:
        return jsonify({"error": "No update data provided"}), 400

    # Define allowed fields for update
    allowed_fields = [
        'latitude', 'longitude', 'amount_received_dollars', 'payment_method',
        'job_description', 'client_name', 'client_contact', 'job_status', 'notes'
    ]

    # Filter out any fields that are not allowed to be updated
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Construct the UPDATE query dynamically
            set_clause = ', '.join([f"{k} = %s" for k in update_data.keys()])
            query = f"""
                UPDATE job_report
                SET {set_clause}
                WHERE job_report_id = %s
                RETURNING *
            """

            # Execute the query with the update values and the job_report_id
            cursor.execute(query, (*update_data.values(), job_report_id))

            updated_report = cursor.fetchone()

            if not updated_report:
                return jsonify({"error": "Job report not found"}), 404

            conn.commit()
            return jsonify(updated_report), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating job report: {e}")
        return jsonify({"error": "An error occurred while updating the job report"}), 500



# 6. DELETE /api/job-reports/{job_report_id}
#    - Delete a job report (and associated photos due to CASCADE)
#
@job_report_bp.route('/<job_report_id>', methods=['DELETE'])
def delete_job_report(job_report_id):
    """
    Delete a job report and its associated photos.

    Path Parameters:
    - job_report_id: UUID of the job report to delete

    Returns:
    - 200: Job report and associated photos deleted successfully
    - 400: Invalid job report ID format
    - 404: Job report not found
    - 500: Unexpected error occurred
    """
    try:
        # Validate job_report_id format
        job_report_id = str(UUID(job_report_id))
    except ValueError:
        return jsonify({"error": "Invalid job report ID format"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # First, check if the job report exists
            cursor.execute("SELECT * FROM job_report WHERE job_report_id = %s", (job_report_id,))
            if cursor.fetchone() is None:
                return jsonify({"error": "Job report not found"}), 404

            # Delete the job report (CASCADE will handle associated photos)
            cursor.execute("DELETE FROM job_report WHERE job_report_id = %s RETURNING *", (job_report_id,))
            deleted_report = cursor.fetchone()

            # ~TODO: handle the logic to delete the actual file from your storage system
            #   # For example: storage.delete_file(deleted_photo['photo_url'])

            conn.commit()
            return jsonify({
                "message": "Job report and associated photos deleted successfully",
                "deleted_report": deleted_report
            }), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting job report: {e}")
        return jsonify({"error": "An error occurred while deleting the job report"}), 500

# 7. GET /api/job-reports/{job_report_id}/photos
#    - List all photos for a specific job report
#
@job_report_bp.route('/<job_report_id>/photos', methods=['GET'])
def list_job_report_photos(job_report_id):
    """
    List all photos for a specific job report.

    Path Parameters:
    - job_report_id: UUID of the job report

    Query Parameters:
    - page: int, optional (default=1) - Page number for pagination
    - limit: int, optional (default=10) - Number of items per page

    Returns:
    - 200: List of photos for the job report
    - 400: Invalid job report ID format
    - 404: Job report not found
    - 500: Unexpected error occurred
    """
    try:
        # Validate job_report_id format
        job_report_id = str(UUID(job_report_id))
    except ValueError:
        return jsonify({"error": "Invalid job report ID format"}), 400

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    offset = (page - 1) * limit

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # First, check if the job report exists
            cursor.execute("SELECT * FROM job_report WHERE job_report_id = %s", (job_report_id,))
            if cursor.fetchone() is None:
                return jsonify({"error": "Job report not found"}), 404

            # Fetch photos for the job report
            cursor.execute("""
                SELECT photo_id, file_name, file_size, photo_url, created_at
                FROM report_photos
                WHERE photo_job_report_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (job_report_id, limit, offset))
            photos = cursor.fetchall()

            # Get total count of photos
            cursor.execute("SELECT COUNT(*) FROM report_photos WHERE photo_job_report_id = %s", (job_report_id,))
            total_photos = cursor.fetchone()['count']

            response = {
                "job_report_id": job_report_id,
                "total_photos": total_photos,
                "page": page,
                "limit": limit,
                "photos": photos
            }

            return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error fetching photos for job report: {e}")
        return jsonify({"error": "An error occurred while fetching photos for the job report"}), 500

# 8. DELETE /api/job-reports/{job_report_id}/photos/{photo_id}
#    - Delete a specific photo from a job report

@job_report_bp.route('/<job_report_id>/photos/<photo_id>', methods=['DELETE'])
def delete_job_report_photo(job_report_id, photo_id):
    """
    Delete a specific photo from a job report.

    Path Parameters:
    - job_report_id: UUID of the job report
    - photo_id: UUID of the photo to delete

    Returns:
    - 200: Photo deleted successfully
    - 400: Invalid job report ID or photo ID format
    - 404: Job report or photo not found
    - 500: Unexpected error occurred
    """
    try:
        # Validate job_report_id and photo_id format
        job_report_id = str(UUID(job_report_id))
        photo_id = str(UUID(photo_id))
    except ValueError:
        return jsonify({"error": "Invalid job report ID or photo ID format"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # First, check if the job report exists
            cursor.execute("SELECT * FROM job_report WHERE job_report_id = %s", (job_report_id,))
            if cursor.fetchone() is None:
                return jsonify({"error": "Job report not found"}), 404

            # Then, check if the photo exists and belongs to the specified job report
            cursor.execute("""
                SELECT * FROM report_photos 
                WHERE photo_id = %s AND photo_job_report_id = %s
            """, (photo_id, job_report_id))
            photo = cursor.fetchone()
            if photo is None:
                return jsonify({"error": "Photo not found or does not belong to the specified job report"}), 404

            # Delete the photo
            cursor.execute("DELETE FROM report_photos WHERE photo_id = %s RETURNING *", (photo_id,))
            deleted_photo = cursor.fetchone()

            conn.commit()

            # Here you might want to add logic to delete the actual file from your storage system
            # For example: storage.delete_file(deleted_photo['photo_url'])

            return jsonify({
                "message": "Photo deleted successfully",
                "deleted_photo": deleted_photo
            }), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting photo from job report: {e}")
