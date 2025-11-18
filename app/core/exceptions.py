"""Custom exceptions for the application"""


class BaseAppException(Exception):
    """Base exception for application errors"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class DatasetNotFoundException(BaseAppException):
    """Raised when a dataset is not found"""

    def __init__(self, dataset_id: str):
        super().__init__(message=f"Dataset with ID '{dataset_id}' not found", error_code="DATASET_NOT_FOUND")


class DatasetAlreadyExistsException(BaseAppException):
    """Raised when trying to create a dataset that already exists"""

    def __init__(self, name: str):
        super().__init__(message=f"Dataset with name '{name}' already exists", error_code="DATASET_ALREADY_EXISTS")


class ValidationException(BaseAppException):
    """Raised when validation fails"""

    def __init__(self, message: str):
        super().__init__(message=message, error_code="VALIDATION_ERROR")
