from fastapi import HTTPException

ERROR_CODES = {
    "PRODUCT_NOT_FOUND": 404,
    "PRODUCT_INACTIVE": 409,
    "ORDER_NOT_FOUND": 404,
    "ORDER_LIMIT_EXCEEDED": 429,
    "ORDER_HAS_ACTIVE": 409,
    "INVALID_STATE_TRANSITION": 409,
    "INSUFFICIENT_STOCK": 409,
    "PROMO_CODE_INVALID": 422,
    "PROMO_CODE_MIN_AMOUNT": 422,
    "ORDER_OWNERSHIP_VIOLATION": 403,
    "VALIDATION_ERROR": 400,
    "TOKEN_EXPIRED": 401,
    "TOKEN_INVALID": 401,
    "REFRESH_TOKEN_INVALID": 401,
    "ACCESS_DENIED": 403,
}

class AppException(HTTPException):
    def __init__(self, error_code: str, message: str = None, status_code: int = None, details: dict = None):
        code = status_code or ERROR_CODES.get(error_code, 400)
        super().__init__(
            status_code=code,
            detail={
                "error_code": error_code,
                "message": message or error_code.replace("_", " ").title(),
                "details": details
            }
        )

def create_error(error_code: str, details: dict = None, message: str = None) -> AppException:
    return AppException(error_code=error_code, message=message, details=details)
