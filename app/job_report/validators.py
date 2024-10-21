


def validate_field(field_name, value, expected_type):
    """
    Validate a field based on its name and expected type.
    """
    if not isinstance(value, expected_type):
        raise ValueError(f"Invalid {field_name}: expected {expected_type.__name__}")

    if field_name == 'payment_method':
        valid_methods = ['Cash', 'Check', 'Card', 'Venmo', 'PayPal', 'CashApp', 'Bank Transfer', 'Other']
        if value not in valid_methods:
            raise ValueError(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")

    if field_name == 'job_status':
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if value not in valid_statuses:
            raise ValueError(f"Invalid job status. Must be one of: {', '.join(valid_statuses)}")

    if field_name in ['latitude', 'longitude']:
        if not (-90 <= value <= 90 if field_name == 'latitude' else -180 <= value <= 180):
            raise ValueError(f"Invalid {field_name}")

    if field_name == 'amount_received_dollars':
        if value < 0:
            raise ValueError("Amount received must be non-negative")

    return value

# Define allowed extensions for photos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS