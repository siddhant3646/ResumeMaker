"""
Centralized Error Handling for ResumeMaker API
"""

import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Error codes for client reference"""
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_EXPIRED_TOKEN = "AUTH_EXPIRED_TOKEN"
    AUTH_MISSING_TOKEN = "AUTH_MISSING_TOKEN"
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    AI_GENERATION_FAILED = "AI_GENERATION_FAILED"
    AI_TIMEOUT = "AI_TIMEOUT"
    RESUME_INVALID_FORMAT = "RESUME_INVALID_FORMAT"
    RESUME_PARSE_ERROR = "RESUME_PARSE_ERROR"
    RESUME_TOO_LARGE = "RESUME_TOO_LARGE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ResumeMakerError(Exception):
    """Base exception for ResumeMaker errors"""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.recoverable = recoverable
        self.error_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary response"""
        return {
            "success": False,
            "error": self.message,
            "error_code": self.code.value,
            "error_id": self.error_id,
            "details": self.details,
            "recoverable": self.recoverable
        }
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )


class AuthenticationError(ResumeMakerError):
    """Authentication-related errors"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )


class AIServiceError(ResumeMakerError):
    """AI service-related errors"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            **kwargs
        )


class ResumeProcessingError(ResumeMakerError):
    """Resume processing errors"""
    
    def __init__(self, message: str, code: ErrorCode, **kwargs):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            **kwargs
        )


def handle_exception(exc: Exception, context: Optional[Dict] = None) -> ResumeMakerError:
    """
    Convert generic exception to ResumeMakerError
    
    Args:
        exc: Original exception
        context: Additional context for logging
        
    Returns:
        ResumeMakerError with appropriate error details
    """
    error_id = str(uuid.uuid4())[:8]
    
    # Log the original error with context
    log_context = f" [Context: {context}]" if context else ""
    logger.exception(f"Error {error_id}: {exc}{log_context}")
    
    # If already a ResumeMakerError, return as-is
    if isinstance(exc, ResumeMakerError):
        return exc
    
    # Handle specific exception types
    if isinstance(exc, HTTPException):
        return ResumeMakerError(
            message=str(exc.detail),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=exc.status_code,
            recoverable=exc.status_code < 500
        )
    
    # Default to internal error
    return ResumeMakerError(
        message="An unexpected error occurred",
        code=ErrorCode.INTERNAL_ERROR,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"original_error": str(exc)},
        recoverable=False
    )


# Convenience functions for common errors
def auth_invalid_token() -> AuthenticationError:
    return AuthenticationError(
        message="Invalid authentication token",
        code=ErrorCode.AUTH_INVALID_TOKEN
    )


def auth_expired_token() -> AuthenticationError:
    return AuthenticationError(
        message="Authentication token has expired",
        code=ErrorCode.AUTH_EXPIRED_TOKEN
    )


def ai_service_unavailable() -> AIServiceError:
    return AIServiceError(
        message="AI service temporarily unavailable",
        code=ErrorCode.AI_SERVICE_UNAVAILABLE,
        recoverable=True
    )


def resume_parse_error(details: Dict) -> ResumeProcessingError:
    return ResumeProcessingError(
        message="Failed to parse resume",
        code=ErrorCode.RESUME_PARSE_ERROR,
        details=details,
        recoverable=False
    )


def validation_error(message: str, details: Optional[Dict] = None) -> ResumeMakerError:
    return ResumeMakerError(
        message=message,
        code=ErrorCode.VALIDATION_ERROR,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        recoverable=True
    )
