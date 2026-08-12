from rest_framework.exceptions import ValidationError


class ConflictError(ValidationError):
    status_code = 409
    default_detail = "Request already in progress."
    default_code = "conflict"
