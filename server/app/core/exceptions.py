import logging
from enum import StrEnum

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.envelope import ErrorBody, ErrorEnvelope


logger = logging.getLogger(__name__)


class ErrorCode(StrEnum):
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION = "VALIDATION"
    CONFLICT = "CONFLICT"
    WECHAT_LOGIN_FAILED = "WECHAT_LOGIN_FAILED"
    POINTS_NOT_ENOUGH = "POINTS_NOT_ENOUGH"
    INTERNAL = "INTERNAL"


class AppError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _error_response(status_code: int, code: ErrorCode, message: str) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorBody(code=code, message=message))
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(400, ErrorCode.VALIDATION, "Request validation failed")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        mapping = {
            400: (ErrorCode.VALIDATION, "Invalid request"),
            401: (ErrorCode.UNAUTHORIZED, "Authentication required"),
            403: (ErrorCode.FORBIDDEN, "Access forbidden"),
            404: (ErrorCode.NOT_FOUND, "Resource not found"),
            409: (ErrorCode.CONFLICT, "Resource conflict"),
            422: (ErrorCode.VALIDATION, "Request validation failed"),
        }
        code, message = mapping.get(
            exc.status_code,
            (ErrorCode.VALIDATION, "Invalid request")
            if exc.status_code < 500
            else (ErrorCode.INTERNAL, "Internal server error"),
        )
        return _error_response(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled request error",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return _error_response(500, ErrorCode.INTERNAL, "Internal server error")
