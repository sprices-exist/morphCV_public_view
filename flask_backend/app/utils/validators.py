from marshmallow import Schema, fields, validate, validates_schema, ValidationError
import re


class LoginSchema(Schema):
    """Schema for login requests."""
    token = fields.Str(required=True, validate=validate.Length(min=1))
    user_info = fields.Dict(required=True)
    
    @validates_schema
    def validate_user_info(self, data, **kwargs):
        user_info = data.get('user_info', {})
        required_fields = ['email', 'name', 'sub']
        
        for field in required_fields:
            if not user_info.get(field):
                raise ValidationError(f'Missing required field in user_info: {field}')
        
        # Validate email format
        email = user_info.get('email')
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('Invalid email format')


class TokenRefreshSchema(Schema):
    """Schema for token refresh requests."""
    refresh_token = fields.Str(required=True, validate=validate.Length(min=1))


class CVCreateSchema(Schema):
    """Schema for CV creation requests."""
    title = fields.Str(validate=validate.Length(min=1, max=200), missing='My CV')
    template_name = fields.Str(required=True, validate=validate.OneOf([
        'template_1', 'template_2', 'template_3', 'template_4'
    ]))
    user_data = fields.Dict(required=True)
    job_description = fields.Str(required=True, validate=validate.Length(min=10, max=5000))
    
    @validates_schema
    def validate_user_data(self, data, **kwargs):
        user_data = data.get('user_data', {})
        required_fields = ['name', 'email', 'experience', 'skills']
        
        for field in required_fields:
            if not user_data.get(field):
                raise ValidationError(f'Missing required field in user_data: {field}')
        
        # Validate email in user data
        email = user_data.get('email')
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('Invalid email format in user_data')


class CVUpdateSchema(Schema):
    """Schema for CV update requests."""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    user_data = fields.Dict()
    job_description = fields.Str(validate=validate.Length(min=10, max=5000))
    edit_instructions = fields.Str(validate=validate.Length(min=1, max=1000))
    
    @validates_schema
    def validate_update_data(self, data, **kwargs):
        # At least one field should be provided for update
        if not any([
            data.get('title'),
            data.get('user_data'),
            data.get('job_description'),
            data.get('edit_instructions')
        ]):
            raise ValidationError('At least one field must be provided for update')
        
        # If user_data is provided, validate email
        user_data = data.get('user_data')
        if user_data and user_data.get('email'):
            email = user_data['email']
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValidationError('Invalid email format in user_data')


class SubscriptionCreateSchema(Schema):
    """Schema for subscription creation requests."""
    price_id = fields.Str(required=True, validate=validate.Length(min=1))
    success_url = fields.Url()
    cancel_url = fields.Url()


class UserUpdateSchema(Schema):
    """Schema for user profile update requests."""
    name = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    
    @validates_schema
    def validate_update_fields(self, data, **kwargs):
        # At least one field should be provided for update
        if not any([data.get('name'), data.get('email')]):
            raise ValidationError('At least one field must be provided for update')


class PaginationSchema(Schema):
    """Schema for pagination parameters."""
    page = fields.Int(validate=validate.Range(min=1), missing=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=100), missing=10)
    sort_by = fields.Str(validate=validate.OneOf([
        'created_at', 'updated_at', 'title', 'status'
    ]), missing='created_at')
    sort_order = fields.Str(validate=validate.OneOf(['asc', 'desc']), missing='desc')


class CVFilterSchema(PaginationSchema):
    """Schema for CV listing with filters."""
    status = fields.Str(validate=validate.OneOf([
        'pending', 'processing', 'success', 'failed'
    ]))
    template_name = fields.Str(validate=validate.OneOf([
        'template_1', 'template_2', 'template_3', 'template_4'
    ]))
    search = fields.Str(validate=validate.Length(max=100))


class FileUploadSchema(Schema):
    """Schema for file upload validation."""
    file_type = fields.Str(validate=validate.OneOf(['pdf', 'jpg', 'png']))
    max_size = fields.Int(validate=validate.Range(min=1))


class WebhookSchema(Schema):
    """Schema for Stripe webhook validation."""
    type = fields.Str(required=True)
    data = fields.Dict(required=True)
    id = fields.Str(required=True)
    created = fields.Int(required=True)


class PasswordResetSchema(Schema):
    """Schema for password reset requests."""
    email = fields.Email(required=True)


class PasswordChangeSchema(Schema):
    """Schema for password change requests."""
    current_password = fields.Str(required=True, validate=validate.Length(min=8))
    new_password = fields.Str(required=True, validate=validate.Length(min=8))
    confirm_password = fields.Str(required=True)
    
    @validates_schema
    def validate_passwords(self, data, **kwargs):
        if data.get('new_password') != data.get('confirm_password'):
            raise ValidationError('New password and confirmation do not match')
        
        if data.get('current_password') == data.get('new_password'):
            raise ValidationError('New password must be different from current password')


class ContactSchema(Schema):
    """Schema for contact form submissions."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    subject = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    message = fields.Str(required=True, validate=validate.Length(min=10, max=1000))


class FeedbackSchema(Schema):
    """Schema for user feedback submissions."""
    rating = fields.Int(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.Str(validate=validate.Length(max=1000))
    category = fields.Str(validate=validate.OneOf([
        'general', 'bug_report', 'feature_request', 'performance', 'ui_ux'
    ]), missing='general')


class BulkOperationSchema(Schema):
    """Schema for bulk operations on CVs."""
    cv_ids = fields.List(fields.Int(), required=True, validate=validate.Length(min=1, max=50))
    operation = fields.Str(required=True, validate=validate.OneOf([
        'delete', 'export', 'archive'
    ]))


class SearchSchema(Schema):
    """Schema for search requests."""
    query = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    filters = fields.Dict()
    limit = fields.Int(validate=validate.Range(min=1, max=50), missing=10)


class EmailSchema(Schema):
    """Schema for email validation."""
    email = fields.Email(required=True)


class PhoneSchema(Schema):
    """Schema for phone number validation."""
    phone = fields.Str(required=True, validate=validate.Regexp(
        r'^\+?1?\d{9,15}$',
        error='Invalid phone number format'
    ))


class DateRangeSchema(Schema):
    """Schema for date range queries."""
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    
    @validates_schema
    def validate_date_range(self, data, **kwargs):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError('start_date must be before end_date')


# Custom validation functions
def validate_template_name(template_name):
    """Validate template name format."""
    valid_templates = ['template_1', 'template_2', 'template_3', 'template_4']
    if template_name not in valid_templates:
        raise ValidationError(f'Invalid template name. Must be one of: {", ".join(valid_templates)}')


def validate_cv_uuid(cv_uuid):
    """Validate CV UUID format."""
    import uuid
    try:
        uuid.UUID(cv_uuid)
    except ValueError:
        raise ValidationError('Invalid CV UUID format')


def validate_file_extension(filename, allowed_extensions):
    """Validate file extension."""
    if '.' not in filename:
        raise ValidationError('File must have an extension')
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'File extension must be one of: {", ".join(allowed_extensions)}')


def validate_image_file(file_data):
    """Validate image file data."""
    try:
        from PIL import Image
        import io
        
        # Try to open the image
        image = Image.open(io.BytesIO(file_data))
        image.verify()
        
        # Check dimensions
        if image.size[0] > 4096 or image.size[1] > 4096:
            raise ValidationError('Image dimensions too large (max 4096x4096)')
        
    except Exception:
        raise ValidationError('Invalid image file')


def validate_json_structure(data, required_keys):
    """Validate JSON structure has required keys."""
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValidationError(f'Missing required keys: {", ".join(missing_keys)}')


# Error formatting helper
def format_validation_errors(errors):
    """Format marshmallow validation errors for API response."""
    formatted_errors = {}
    
    for field, messages in errors.items():
        if isinstance(messages, list):
            formatted_errors[field] = messages[0]  # Take first error message
        else:
            formatted_errors[field] = str(messages)
    
    return {
        'error': 'Validation failed',
        'message': 'Please check your input and try again',
        'validation_errors': formatted_errors
    }
