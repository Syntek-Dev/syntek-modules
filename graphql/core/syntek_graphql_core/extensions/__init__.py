"""GraphQL security and performance extensions.

This module provides security extensions beyond query depth/complexity limiting:
- Granular rate limiting per GraphQL operation
- Global SMS cost attack prevention
- Constant-time response middleware
- CAPTCHA validation
- Input sanitisation (XSS/SQL injection prevention)
- Session fingerprinting
- Suspicious activity detection

Performance monitoring extensions:
- Query profiling and slow query detection
- N+1 query pattern detection
"""

from syntek_graphql_core.extensions.captcha import CaptchaValidationExtension
from syntek_graphql_core.extensions.constant_time import ConstantTimeResponseExtension
from syntek_graphql_core.extensions.fingerprint import SessionFingerprintExtension
from syntek_graphql_core.extensions.n_plus_one_detection import (
    NPlusOneDetectionExtension,
    NPlusOneQueryError,
)
from syntek_graphql_core.extensions.profiling import QueryProfilingExtension
from syntek_graphql_core.extensions.rate_limit import (
    GlobalSMSRateLimitExtension,
    OperationRateLimitExtension,
)
from syntek_graphql_core.extensions.sanitisation import InputSanitisationExtension
from syntek_graphql_core.extensions.suspicious import SuspiciousActivityExtension

__all__ = [
    # Security extensions
    "OperationRateLimitExtension",
    "GlobalSMSRateLimitExtension",
    "ConstantTimeResponseExtension",
    "CaptchaValidationExtension",
    "InputSanitisationExtension",
    "SessionFingerprintExtension",
    "SuspiciousActivityExtension",
    # Performance extensions
    "QueryProfilingExtension",
    "NPlusOneDetectionExtension",
    "NPlusOneQueryError",
]
