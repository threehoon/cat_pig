from app.core.exceptions import AppError, ErrorCode


def validation(message: str) -> AppError:
    return AppError(ErrorCode.VALIDATION, message, 400)


def not_found(message: str) -> AppError:
    return AppError(ErrorCode.NOT_FOUND, message, 404)


def forbidden(message: str) -> AppError:
    return AppError(ErrorCode.FORBIDDEN, message, 403)


def conflict(message: str) -> AppError:
    return AppError(ErrorCode.CONFLICT, message, 409)
