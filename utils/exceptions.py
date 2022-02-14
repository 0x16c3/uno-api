from pydantic.main import BaseModel
from fastapi import HTTPException

from typing import Any


class ErrorMessage(BaseModel):
    detail: str
    # stack_trace: str = None


"""
For some reason, the CORS middleware does not let the 
response through if it's not a 'HTTPException' instance.

Here's a workaround.
"""


class NotFoundException404(HTTPException):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(404, detail=detail)

    @staticmethod
    def new(detail: str = "Resource not found") -> None:
        return HTTPException(status_code=404, detail=detail)

    @staticmethod
    def model(detail: str = "Resource not found") -> dict:
        return {"model": ErrorMessage, "description": detail}


class ForbiddenException403(HTTPException):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(403, detail=detail)

    @staticmethod
    def new(detail: str = "Resource not found") -> None:
        return HTTPException(status_code=403, detail=detail)

    @staticmethod
    def model(detail: str = "Forbidden") -> dict:
        return {"model": ErrorMessage, "description": detail}


class UnauthorizedException401(HTTPException):
    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(401, detail=detail)

    @staticmethod
    def new(detail: str = "Resource not found") -> None:
        return HTTPException(status_code=401, detail=detail)

    @staticmethod
    def model(detail: str = "Unauthorized") -> dict:
        return {"model": ErrorMessage, "description": detail}


class BadRequestException400(HTTPException):
    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(400, detail=detail)

    @staticmethod
    def new(detail: str = "Resource not found") -> None:
        return HTTPException(status_code=400, detail=detail)

    @staticmethod
    def model(detail: str = "Bad request") -> dict:
        return {"model": ErrorMessage, "description": detail}
