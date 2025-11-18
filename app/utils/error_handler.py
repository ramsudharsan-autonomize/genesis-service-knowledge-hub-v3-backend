"""HTTP error handling utilities"""

from typing import Type
from fastapi import HTTPException, status as http_status
from app.core.exceptions import (
    DatasetNotFoundException,
    DatasetAlreadyExistsException,
    ValidationException,
    BaseAppException,
)


# Exception to HTTP status code mapping
EXCEPTION_STATUS_MAP: dict[Type[BaseAppException], int] = {
    DatasetNotFoundException: http_status.HTTP_404_NOT_FOUND,
    DatasetAlreadyExistsException: http_status.HTTP_409_CONFLICT,
    ValidationException: http_status.HTTP_400_BAD_REQUEST,
}


def handle_exception(e: Exception, context: str = "operation") -> None:
    """
    Handle service layer exceptions and convert to HTTP exceptions

    Args:
        e: The exception to handle
        context: Context string for generic error messages (e.g., "creating dataset")

    Raises:
        HTTPException: Converted HTTP exception with appropriate status code
    """
    # Handle known application exceptions
    if isinstance(e, BaseAppException):
        status_code = EXCEPTION_STATUS_MAP.get(type(e), http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(status_code=status_code, detail=e.message)

    # Handle unexpected exceptions
    raise HTTPException(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"An error occurred while {context}: {str(e)}",
    )
