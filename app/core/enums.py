from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"


class SecurityEventResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"