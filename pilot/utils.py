from rest_framework.exceptions import APIException


class ComplianceError(APIException):
    status_code = 403

    def __init__(self, message, doc_id=None, expiry_date=None):
        self.detail = {
            'error_code': 'COMPLIANCE_ERROR',
            'message': message,
            'details': {'doc_id': doc_id, 'expiry_date': expiry_date}
        }


class BlacklistError(APIException):
    status_code = 403

    def __init__(self, message, entity_type=None, entity_id=None):
        self.detail = {
            'error_code': 'BLACKLIST_ERROR',
            'message': message,
            'details': {'entity_type': entity_type, 'entity_id': entity_id}
        }


class PermissionError(APIException):
    status_code = 403

    def __init__(self, message):
        self.detail = {
            'error_code': 'PERMISSION_DENIED',
            'message': message,
            'details': {}
        }