"""Common enums used across models"""

from enum import Enum


class DatasetStatus(str, Enum):
    """Dataset status enumeration"""

    ACTIVE = "active"
    DELETED = "deleted"
