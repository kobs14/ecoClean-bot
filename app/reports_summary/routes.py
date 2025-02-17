
from typing import Union, Optional, Tuple

from app.reports_summary.validators import validate_account
from app.main import global_conn as conn
from app.config import logger

from flask import Blueprint, request, jsonify, send_file
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from calendar import monthrange
import io



reports_bp = Blueprint('reports', __name__)


# 1. GET /api/reports/summary
@reports_bp.route('/summary', methods=['GET'])
def get_summary_report():
    """
    Retrieve a summary report of job reports based on the provided start_date, end_date, and grouping.

    Args:
        start_date (str): The starting date in the format 'YYYY-MM-DD'.
        end_date (str): The ending date in the format 'YYYY-MM-DD'.
        group_by (str, optional): The time grouping for the report ('day', 'week', 'month', 'year'). Defaults to 'day'.

    Returns:
        - 200: Summary report of job reports.
        - 400: Invalid input (e.g., missing or incorrect date format, invalid group_by value).
        - 500: Internal server error.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'day')

    logger.info(f"Fetching summary report with start_date: {start_date}, end_date: {end_date}, group_by: {group_by}")

    # Validate start_date and end_date
    if not start_date or not end_date:
        logger.error("start_date and end_date are required.")
        return jsonify({"error": "start_date and end_date are required"}), 400

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD.")
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Validate group_by value
    valid_group_by = ['day', 'week', 'month', 'year']
    if group_by not in valid_group_by:
        logger.error(f"Invalid group_by value: {group_by}. Must be one of {valid_group_by}.")
        return jsonify({"error": f"Invalid group_by. Must be one of {valid_group_by}"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            logger.info("Executing SQL query for summary report.")
            cursor.execute("""
                SELECT
                    DATE_TRUNC(%s, created_at) as period,
                    COUNT(*) as job_count,
                    SUM(amount_received_dollars) as total_amount
                FROM job_report
                WHERE created_at BETWEEN %s AND %s
                GROUP BY period
                ORDER BY period
            """, (group_by, start_date, end_date))

            results = cursor.fetchall()

            # Convert datetime to string for JSON serialization
            for row in results:
                row['period'] = row['period'].isoformat()

            logger.info(f"Summary report successfully retrieved. {len(results)} entries found.")
            return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error fetching summary report: {str(e)}")
        return jsonify({"error": str(e)}), 500



# 2. GET /reports/employee-performance
@reports_bp.route('/employee-performance', methods=['GET'])
def get_employee_performance():
    """
    Get Employee performance endpoint.
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        employee_id = request.args.get('employee_id')

        # Validate required parameters
        if not start_date or not end_date:
            return jsonify({"error": "start_date and end_date are required"}), 400

        results = get_employee_performance_data(start_date, end_date, employee_id)
        return jsonify(results), 200

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Server error: %s", str(e))
        return jsonify({"error": str(e)}), 500



# 3. GET /reports/top-clients

@reports_bp.route('/top-clients', methods=['GET'])
def get_top_clients():
    """
    Retrieve the top clients based on total amount spent within a specified date range.

    Query Parameters:
    - start_date: The start of the date range (YYYY-MM-DD).
    - end_date: The end of the date range (YYYY-MM-DD).
    - limit: The number of top clients to return (default is 10).

    Returns:
    - A JSON list of clients with their total amount spent, ordered by total amount spent.
    """
    # Get and validate query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', default=10, type=int)  # Default to 10 clients

    # Validate required date parameters
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    # Parse and validate the date format
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Ensure limit is a positive integer
    if limit <= 0:
        return jsonify({"error": "Limit must be a positive integer"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # SQL query to fetch top clients based on total amount spent
            query = """
                SELECT 
                    jr.client_name,
                    jr.client_contact,
                    COALESCE(SUM(jr.amount_received_dollars), 0) AS total_spent
                FROM 
                    job_report jr
                WHERE 
                    jr.created_at BETWEEN %s AND %s
                GROUP BY 
                    jr.client_name, jr.client_contact
                ORDER BY 
                    total_spent DESC
                LIMIT %s
            """

            # Execute the query with the parameters
            cursor.execute(query, (start_date, end_date, limit))
            results = cursor.fetchall()

            return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 5. GET /reports/revenue-by-payment-method
@reports_bp.route('/revenue-by-payment-method', methods=['GET'])
def get_revenue_by_payment_method():
    """
    Retrieve revenue breakdown by payment methods within a specified date range.

    Query Parameters:
    - start_date: The start of the date range (YYYY-MM-DD).
    - end_date: The end of the date range (YYYY-MM-DD).

    Returns:
    - A JSON object with payment methods and their corresponding total revenues.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Validate required date parameters
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    # Parse and validate the date format
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT 
                    jr.payment_method,
                    COALESCE(SUM(jr.amount_received_dollars), 0) AS total_revenue
                FROM 
                    job_report jr
                WHERE 
                    jr.created_at BETWEEN %s AND %s
                    AND jr.job_status = 'completed'
                GROUP BY 
                    jr.payment_method
                ORDER BY 
                    total_revenue DESC
            """

            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 10. GET /reports/custom
@reports_bp.route('/custom', methods=['GET'])
def get_custom_report():
    """
    Retrieve a customizable report based on user-specified criteria.

    Query Parameters:
    - start_date: (optional) The start of the date range (YYYY-MM-DD).
    - end_date: (optional) The end of the date range (YYYY-MM-DD).
    - payment_method: (optional) Filter by payment method (e.g., 'Cash', 'Card', etc.).
    - job_status: (optional) Filter by job status (e.g., 'completed', 'cancelled').
    - group_by: (optional) Specify a field to group results by (e.g., 'payment_method', 'job_status').
    - limit: (optional) Limit the number of returned results.

    Returns:
    - A JSON object containing the customizable report data.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    payment_method = request.args.get('payment_method')
    job_status = request.args.get('job_status')
    group_by = request.args.get('group_by', default='payment_method')  # Default group by payment method
    limit = request.args.get('limit', default=100, type=int)

    base_query = """
        SELECT 
            jr.job_status,
            jr.payment_method,
            COUNT(jr.job_report_id) AS job_count,
            COALESCE(SUM(jr.amount_received_dollars), 0) AS total_revenue
        FROM 
            job_report jr
        WHERE 
            1=1
    """

    # Add filters
    filters = []
    if start_date:
        filters.append("jr.created_at >= %s")
    if end_date:
        filters.append("jr.created_at <= %s")
    if payment_method:
        filters.append("jr.payment_method = %s")
    if job_status:
        filters.append("jr.job_status = %s")

    # Combine filters with the base query
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Group by clause
    group_by_clause = f"GROUP BY {group_by}, jr.job_status" if group_by else ""
    order_by_clause = f"ORDER BY total_revenue DESC LIMIT {limit}"

    # Complete query
    query = f"{base_query} {group_by_clause} {order_by_clause}"

    # Prepare parameters for the query
    params = []
    if start_date:
        params.append(start_date)
    if end_date:
        params.append(end_date)
    if payment_method:
        params.append(payment_method)
    if job_status:
        params.append(job_status)

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500




# 7. GET /reports/excel/monthly-summary
@reports_bp.route('/excel/monthly-summary', methods=['GET'])
def get_monthly_summary_excel():
    # Get and validate query parameters
    year = request.args.get('year')
    month = request.args.get('month')

    if not year or not month:
        return jsonify({"error": "Year and month are required"}), 400

    try:
        year = int(year)
        month = int(month)
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
    except ValueError:
        return jsonify({"error": "Invalid year or month format. Use YYYY for year and MM for month"}), 400

    try:
        # Create a new workbook and select the active sheet
        wb = Workbook()

        # Create Overview Sheet
        overview_sheet = wb.active
        overview_sheet.title = "Overview"
        setup_overview_sheet(overview_sheet, start_date, end_date)

        # Create Daily Breakdown Sheet
        daily_sheet = wb.create_sheet("Daily Breakdown")
        setup_daily_sheet(daily_sheet, start_date, end_date)

        # Create Payment Methods Sheet
        payment_sheet = wb.create_sheet("Payment Methods")
        setup_payment_methods_sheet(payment_sheet, start_date, end_date)

        # Create Employee Performance Sheet
        employee_sheet = wb.create_sheet("Employee Performance")
        setup_employee_sheet(employee_sheet, start_date, end_date)

        # Save to BytesIO object
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'monthly_summary_{year}_{month:02d}.xlsx'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@reports_bp.route('/excel/weekly-summary', methods=['GET'])
def get_weekly_summary_excel():
    """
    Generate an Excel file with a detailed weekly summary.

    Query Parameters:
    - year: (required) The year for the summary (YYYY).
    - week: (required) The ISO week number for the summary (1-53).

    Returns:
    - An Excel file with the weekly summary.
    """
    # Get and validate query parameters
    year = request.args.get('year')
    week = request.args.get('week')

    if not year or not week:
        return jsonify({"error": "Year and week are required"}), 400

    try:
        year = int(year)
        week = int(week)
        # Calculate the start and end dates of the week
        start_date = date.fromisocalendar(year, week, 1)  # Monday of the week
        end_date = start_date + timedelta(days=6)  # Sunday of the week
    except ValueError:
        return jsonify({"error": "Invalid year or week format. Use YYYY for year and WW for week"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    try:
        # Create a new workbook and select the active sheet
        wb = Workbook()

        # Create Overview Sheet
        overview_sheet = wb.active
        overview_sheet.title = "Overview"
        setup_overview_sheet(overview_sheet, start_date, end_date)

        # Create Daily Breakdown Sheet
        daily_sheet = wb.create_sheet("Daily Breakdown")
        setup_daily_sheet(daily_sheet, start_date, end_date)

        # Create Payment Methods Sheet
        payment_sheet = wb.create_sheet("Payment Methods")
        setup_payment_methods_sheet(payment_sheet, start_date, end_date)

        # Create Employee Performance Sheet
        employee_sheet = wb.create_sheet("Employee Performance")
        setup_employee_sheet(employee_sheet, start_date, end_date)

        # Save to BytesIO object
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'weekly_summary_{year}_{week:02d}.xlsx'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 8. GET /reports/excel/employee-performance
@reports_bp.route('/excel/employee-performance', methods=['GET'])
def get_employee_performance_excel():
    """
    Generate Excel report for employee performance data.
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        employee_id = request.args.get('employee_id')

        # Validate required parameters
        if not start_date or not end_date:
            return jsonify({"error": "start_date and end_date are required"}), 400

        try:
            results = get_employee_performance_data(start_date, end_date, employee_id)

            # Create Excel workbook
            wb = Workbook()
            performance_sheet = wb.active
            performance_sheet.title = "Employee Performance"

            # Modify the results to match the expected structure for setup_employee_performance_sheet
            modified_results = []
            for row in results:
                modified_row = row.copy()  # Create a copy to avoid modifying the original
                modified_row['avg_amount'] = row['avg_job_amount']  # Map the new field name to the old one
                modified_results.append(modified_row)

            # Set up the sheet with our modified data
            setup_employee_performance_sheet(performance_sheet, modified_results)

            # Save to BytesIO object
            excel_file = io.BytesIO()
            wb.save(excel_file)
            excel_file.seek(0)

            # Generate filename
            filename = f'employee_performance_{start_date}_to_{end_date}.xlsx'

            return send_file(
                excel_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            logger.error("Error generating Excel: %s", str(e))
            raise e

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error in Excel endpoint: %s", str(e))
        return jsonify({"error": str(e)}), 500



def setup_job_reports_sheet(sheet, data):
    """Set up the Excel sheet with job reports data"""
    logger.info(f"Setting up Excel sheet with {len(data)} records")

    # Headers
    headers = [
        "Report ID",
        "Date",
        "Amount ($)",
        "Payment Method",
        "Job Description",
        "Client Name",
        "Client Contact",
        "Status",
        "Notes",
        "Employee Name",
        "Employee ID",
        "Employee Phone"
    ]

    # Style headers
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    header_font = Font(bold=True)

    for col, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Add data
    try:
        for row, record in enumerate(data, 2):
            logger.info(f"Processing row {row - 1}: {record}")
            if len(record) != 12:
                raise ValueError(f"Unexpected number of columns in record {row - 1}: {len(record)} columns found")

            sheet.cell(row=row, column=1).value = str(record['job_report_id'])  # job_report_id
            sheet.cell(row=row, column=2).value = record['created_at'].strftime("%Y-%m-%d %H:%M")  # created_at
            sheet.cell(row=row, column=3).value = float(record['amount_received_dollars'])  # Convert Decimal to float
            sheet.cell(row=row, column=4).value = record['payment_method']  # payment_method
            sheet.cell(row=row, column=5).value = record['job_description']  # job_description
            sheet.cell(row=row, column=6).value = record['client_name']  # client_name
            sheet.cell(row=row, column=7).value = record['client_contact']  # client_contact
            sheet.cell(row=row, column=8).value = record['job_status']  # status
            sheet.cell(row=row, column=9).value = record['notes']  # notes
            sheet.cell(row=row, column=10).value = record['employee_name']  # employee_name
            sheet.cell(row=row, column=11).value = str(record['account_id'])  # employee_id
            sheet.cell(row=row, column=12).value = record['account_phone']  # employee_phone

    except Exception as e:
        logger.error(f"Error processing Excel data: {e}")
        raise e

    # Adjust column widths
    for col in range(1, len(headers) + 1):
        sheet.column_dimensions[chr(64 + col)].width = 15

    # Format amount column as currency
    for row in range(2, sheet.max_row + 1):
        cell = sheet.cell(row=row, column=3)
        cell.number_format = '$#,##0.00'



def get_filtered_job_reports(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[str] = None,
        account_fullname: Optional[str] = None
) -> Tuple[list, Optional[str]]:
    """
    Fetch job reports based on the provided filters.
    Returns tuple of (results, error_message)
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor):
            # First validate account parameters
            is_valid, error_msg = validate_account(
                account_id=account_id,
                account_fullname=account_fullname,
                db_connection=conn
            )

            if not is_valid:
                return [], error_msg

            query = """
                SELECT 
                    jr.job_report_id,
                    jr.created_at,
                    jr.amount_received_dollars,
                    jr.payment_method,
                    jr.job_description,
                    jr.client_name,
                    jr.client_contact,
                    jr.job_status,
                    jr.notes,
                    a.account_fullname as employee_name,
                    a.account_id,
                    a.account_phone
                FROM job_report jr
                JOIN account a ON jr.report_by_account_id = a.account_id
                WHERE 1=1
                AND a.account_status = 'active'
            """
            params = []

            if start_date:
                query += " AND DATE(jr.created_at) >= %s"
                params.append(start_date)

            if end_date:
                query += " AND DATE(jr.created_at) <= %s"
                params.append(end_date)

            if account_id:
                query += " AND a.account_id = %s"
                params.append(account_id)

            if account_fullname:
                query += " AND LOWER(a.account_fullname) LIKE LOWER(%s)"
                params.append(f"%{account_fullname}%")

            query += " ORDER BY jr.created_at DESC"

            with conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()

                if not results and (account_id or account_fullname):
                    return [], "No reports found for the specified account and date range."

            return results, None

    except Exception as e:
        return [], str(e)


@reports_bp.route('/excel/job-reports', methods=['GET'])
def get_job_reports_excel():
    """
    Generate an Excel file with job reports, filtered by date and employee.

    Query Parameters:
    - start_date: (optional) Start date for filtering (YYYY-MM-DD)
    - end_date: (optional) End date for filtering (YYYY-MM-DD)
    - account_id: (optional) Employee's account ID (must be valid UUID)
    - account_fullname: (optional) Employee's full name (partial match)

    Returns:
    - An Excel file with the job reports
    """
    # Get and validate query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    account_id = request.args.get('account_id')
    account_fullname = request.args.get('account_fullname')

    # Convert date strings to date objects if provided
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    if start_date and end_date and start_date > end_date:
        return jsonify({"error": "Start date cannot be after end date"}), 400

    # Get the data
    results, error = get_filtered_job_reports(
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        account_fullname=account_fullname
    )

    if error:
        return jsonify({"error": error}), 400 if "not found" in error.lower() else 500

    if not results:
        return jsonify({"error": "No data found for the given filters"}), 404

    try:
        # Create workbook and sheet
        wb = Workbook()
        sheet = wb.active
        sheet.title = "Job Reports"

        # Set up the sheet with data
        setup_job_reports_sheet(sheet, results)

        # Save to BytesIO object
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        # Generate filename based on filters
        filename_parts = ['job_reports']
        if start_date:
            filename_parts.append(f"from_{start_date}")
        if end_date:
            filename_parts.append(f"to_{end_date}")
        if account_fullname:
            # Clean filename by removing spaces and special characters
            clean_name = ''.join(c for c in account_fullname if c.isalnum())
            filename_parts.append(f"emp_{clean_name}")
        elif account_id:
            filename_parts.append(f"emp_{account_id}")

        filename = f"{'-'.join(filename_parts)}.xlsx"

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ################################################
# Set upt Sheets for xl files
# ################################################

def setup_overview_sheet(sheet, start_date, end_date):
    """Se tup the overview sheet with monthly summary"""
    # Apply styles
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")

    # Set column widths
    for col in range(1, 6):
        sheet.column_dimensions[get_column_letter(col)].width = 15

    # Add title
    sheet['A1'] = f"Monthly Summary - {start_date.strftime('%B %Y')}"
    sheet['A1'].font = Font(bold=True, size=14)
    sheet.merge_cells('A1:E1')

    # Add headers
    headers = [
        "Metric", "Total", "Daily Average", "% Change from Last Month", "YTD Total"
    ]
    for col, header in enumerate(headers, 1):
        cell = sheet.cell(row=3, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill

    # Fetch and add data
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get current month metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN job_status = 'completed' THEN 1 END) as completed_jobs,
                COUNT(CASE WHEN job_status = 'cancelled' THEN 1 END) as cancelled_jobs,
                COALESCE(SUM(CASE WHEN job_status = 'completed' THEN amount_received_dollars END), 0) as total_revenue,
                COUNT(DISTINCT report_by_account_id) as active_employees
            FROM job_report
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        current_metrics = cursor.fetchone()

        # Add metrics rows
        metrics = [
            ("Total Jobs", current_metrics['total_jobs']),
            ("Completed Jobs", current_metrics['completed_jobs']),
            ("Cancelled Jobs", current_metrics['cancelled_jobs']),
            ("Total Revenue", f"${current_metrics['total_revenue']:,.2f}"),
            ("Active Employees", current_metrics['active_employees']),
            ("Average Revenue per Job",
             f"${current_metrics['total_revenue'] / current_metrics['completed_jobs']:,.2f}" if current_metrics[
                                                                                                    'completed_jobs'] > 0 else "$0.00")
        ]

        for row, (metric, value) in enumerate(metrics, 4):
            sheet.cell(row=row, column=1, value=metric).font = Font(bold=True)
            sheet.cell(row=row, column=2, value=value)


def setup_daily_sheet(sheet, start_date, end_date):
    """Set up the daily breakdown sheet"""
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")

    headers = [
        "Date", "Total Jobs", "Completed Jobs", "Revenue",
        "Active Employees", "Avg Revenue per Job"
    ]

    for col, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        sheet.column_dimensions[get_column_letter(col)].width = 15

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT 
                DATE(created_at) as job_date,
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN job_status = 'completed' THEN 1 END) as completed_jobs,
                COALESCE(SUM(CASE WHEN job_status = 'completed' THEN amount_received_dollars END), 0) as daily_revenue,
                COUNT(DISTINCT report_by_account_id) as active_employees
            FROM job_report
            WHERE created_at BETWEEN %s AND %s
            GROUP BY DATE(created_at)
            ORDER BY job_date
        """, (start_date, end_date))

        for row, record in enumerate(cursor.fetchall(), 2):
            sheet.cell(row=row, column=1, value=record['job_date'].strftime('%Y-%m-%d'))
            sheet.cell(row=row, column=2, value=record['total_jobs'])
            sheet.cell(row=row, column=3, value=record['completed_jobs'])
            sheet.cell(row=row, column=4, value=f"${record['daily_revenue']:,.2f}")
            sheet.cell(row=row, column=5, value=record['active_employees'])
            avg_revenue = record['daily_revenue'] / record['completed_jobs'] if record['completed_jobs'] > 0 else 0
            sheet.cell(row=row, column=6, value=f"${avg_revenue:,.2f}")


def setup_payment_methods_sheet(sheet, start_date, end_date):
    """Se tup the payment methods breakdown sheet"""
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")

    headers = [
        "Payment Method", "Number of Jobs", "Total Revenue",
        "Average Amount", "% of Total Jobs"
    ]

    for col, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        sheet.column_dimensions[get_column_letter(col)].width = 15

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            WITH payment_stats AS (
                SELECT 
                    payment_method,
                    COUNT(*) as job_count,
                    COALESCE(SUM(amount_received_dollars), 0) as total_revenue,
                    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_report 
                                      WHERE created_at BETWEEN %s AND %s) as percentage
                FROM job_report
                WHERE created_at BETWEEN %s AND %s
                GROUP BY payment_method
            )
            SELECT *,
                   CASE WHEN job_count > 0 
                        THEN total_revenue / job_count 
                        ELSE 0 
                   END as avg_amount
            FROM payment_stats
            ORDER BY job_count DESC
        """, (start_date, end_date, start_date, end_date))

        for row, record in enumerate(cursor.fetchall(), 2):
            sheet.cell(row=row, column=1, value=record['payment_method'])
            sheet.cell(row=row, column=2, value=record['job_count'])
            sheet.cell(row=row, column=3, value=f"${record['total_revenue']:,.2f}")
            sheet.cell(row=row, column=4, value=f"${record['avg_amount']:,.2f}")
            sheet.cell(row=row, column=5, value=f"{record['percentage']:.1f}%")



def setup_employee_sheet(sheet, start_date, end_date):
    """Set up the employee performance sheet"""
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")

    headers = [
        "Employee Name", "Total Jobs", "Completed Jobs", "Cancelled Jobs",
        "Total Revenue", "Average Job Amount", "Completion Rate"
    ]

    for col, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        sheet.column_dimensions[get_column_letter(col)].width = 20

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT 
                a.account_fullname as employee_name,
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN jr.job_status = 'completed' THEN 1 END) as completed_jobs,
                COUNT(CASE WHEN jr.job_status = 'cancelled' THEN 1 END) as cancelled_jobs,
                COALESCE(SUM(CASE WHEN jr.job_status = 'completed' 
                                THEN jr.amount_received_dollars END), 0) as total_revenue,
                 COALESCE(AVG(CASE WHEN jr.job_status = 'completed' 
                                THEN jr.amount_received_dollars END), 0) as avg_amount,
                CASE WHEN COUNT(*) > 0 
                    THEN COUNT(CASE WHEN jr.job_status = 'completed' THEN 1 END) * 100.0 / COUNT(*)
                    ELSE 0 
                END as completion_rate
            FROM account a
            JOIN job_report jr ON a.account_id = jr.report_by_account_id
            WHERE jr.created_at BETWEEN %s AND %s
            GROUP BY a.account_id, a.account_fullname
            ORDER BY total_jobs DESC;
        """, (start_date, end_date))

        for row, record in enumerate(cursor.fetchall(), 2):
            sheet.cell(row=row, column=1, value=record['employee_name'])
            sheet.cell(row=row, column=2, value=record['total_jobs'])
            sheet.cell(row=row, column=3, value=record['completed_jobs'])
            sheet.cell(row=row, column=4, value=record['cancelled_jobs'])
            sheet.cell(row=row, column=5, value=f"${record['total_revenue']:,.2f}")
            sheet.cell(row=row, column=6, value=f"${record['avg_amount']:,.2f}")
            sheet.cell(row=row, column=7, value=f"{record['completion_rate']:.1f}%")



def setup_employee_performance_sheet(sheet, data):
    # Add headers to the Excel sheet
    headers = [
        "Employee Name", "Total Jobs", "Completed Jobs", "Cancelled Jobs",
        "Total Revenue", "Average Amount", "Completion Rate (%)"
    ]
    sheet.append(headers)

    # Add data rows
    for row in data:
        sheet.append([
            row['employee_name'],
            row['total_jobs'],
            row['completed_jobs'],
            row['cancelled_jobs'],
            row['total_revenue'],
            row['avg_amount'],
            row['completion_rate']
        ])

    # Optionally, you can adjust column widths or apply formatting
    for col in sheet.columns:
        max_length = max(len(str(cell.value)) for cell in col)
        sheet.column_dimensions[col[0].column_letter].width = max_length + 2


def get_employee_performance_data(start_date: Union[str, datetime],
                                  end_date: Union[str, datetime],
                                  employee_id: Optional[str] = None):
    """
    Get employee performance data for a given date range and optional employee ID.

    Args:
        start_date: Start date (either datetime object or string in YYYY-MM-DD format)
        end_date: End date (either datetime object or string in YYYY-MM-DD format)
        employee_id: Optional UUID of specific employee to query

    Returns:
        List of dictionaries containing performance metrics
    """
    # Convert string dates to datetime if necessary
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build the SQL query with proper parameter placeholders
            query = """
                WITH employee_metrics AS (
                    SELECT 
                        a.account_id,
                        a.account_fullname as employee_name,
                        COUNT(jr.job_report_id) as total_jobs,
                        COUNT(CASE WHEN jr.job_status = 'completed' THEN 1 END) as completed_jobs,
                        COUNT(CASE WHEN jr.job_status = 'cancelled' THEN 1 END) as cancelled_jobs,
                        COALESCE(SUM(CASE WHEN jr.job_status = 'completed' THEN jr.amount_received_dollars END), 0) as total_revenue,
                        COALESCE(
                            ROUND(AVG(CASE WHEN jr.job_status = 'completed' THEN jr.amount_received_dollars END)::numeric, 2),
                            0
                        ) as avg_job_amount,
                        COUNT(DISTINCT DATE(jr.created_at)) as days_worked
                    FROM 
                        account a
                    LEFT JOIN 
                        job_report jr ON a.account_id = jr.report_by_account_id
                        AND jr.created_at BETWEEN %s AND %s
                    {where_clause}
                    GROUP BY 
                        a.account_id, a.account_fullname
                )
                SELECT 
                    em.*,
                    ROUND(CASE 
                        WHEN days_worked > 0 THEN completed_jobs::numeric / days_worked 
                        ELSE 0 
                    END, 2) as jobs_per_day,
                    ROUND(CASE 
                        WHEN total_jobs > 0 THEN (completed_jobs::numeric / total_jobs * 100) 
                        ELSE 0 
                    END, 2) as completion_rate,
                    COALESCE(
                        (
                            SELECT json_agg(json_build_object(
                                'payment_method', payment_method,
                                'count', count
                            ))
                            FROM (
                                SELECT jr.payment_method, COUNT(*) as count
                                FROM job_report jr
                                WHERE jr.report_by_account_id = em.account_id
                                AND jr.created_at BETWEEN %s AND %s
                                GROUP BY jr.payment_method
                            ) as payment_data
                        ),
                        '[]'::json
                    ) as payment_methods
                FROM 
                    employee_metrics em
                ORDER BY 
                    total_jobs DESC, total_revenue DESC
            """

            # Prepare parameters list
            params = [start_date, end_date]  # First pair of dates

            # Add where clause if employee_id is provided
            where_clause = ""
            if employee_id:
                where_clause = "WHERE a.account_id = %s"
                params.append(employee_id)

            # Format query with where clause
            query = query.format(where_clause=where_clause)

            # Add second pair of dates for payment methods subquery
            params.extend([start_date, end_date])

            # Log the query and parameters for debugging
            logger.debug("Executing query with params: %s", params)

            # Execute query
            cursor.execute(query, params)
            results = cursor.fetchall()

            return results

    except Exception as e:
        logger.error("Database error: %s", str(e))
        raise Exception(f"Database error: {str(e)}")


# 6. GET /reports/geographical-distribution
#    - Query params: start_date, end_date
#    - Returns: Job report distribution by geographical areas (using latitude/longitude)
#
# 9. GET /reports/trends
#    - Query params: start_date, end_date, metric (e.g., revenue, job_count)
#    - Returns: Trend analysis of the specified metric over time