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


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limit_exceeded"
    message = "Too many AI requests. Please wait and try again"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Resource was not found"


class ConfigurationError(AppError):
    status_code = 500
    code = "configuration_error"
    message = "Service configuration is invalid"


class InsufficientCreditsError(AppError):
    status_code = 402
    code = "insufficient_credits"
    message = "You do not have enough credits. Please top up or upgrade your plan"


class WebhookVerificationError(AppError):
    status_code = 400
    code = "webhook_verification_failed"
    message = "Could not verify the incoming webhook signature"


class PaymentProviderError(AppError):
    status_code = 502
    code = "payment_provider_error"
    message = "The payment provider could not process this request"
