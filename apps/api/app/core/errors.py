from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str


class AppError(Exception):
    status_code = 400
    code = "app_error"
    message = "Application error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message


class AuthenticationError(AppError):
    status_code = 401
    code = "authentication_failed"
    message = "Authentication failed"


class AuthorizationError(AppError):
    status_code = 403
    code = "forbidden"
    message = "You do not have permission to perform this action"


class ConfigurationError(AppError):
    status_code = 500
    code = "configuration_error"
    message = "Service configuration is invalid"

