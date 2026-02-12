"""Email validation with security checks.

This module provides comprehensive email validation including:
- Syntax validation (RFC 5322)
- DNS verification (MX records)
- Disposable email detection
- Role-based email detection
- Internationalized domain support
"""

import logging
import re
from typing import Tuple, Optional
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email

logger = logging.getLogger(__name__)


class EmailValidator:
    """Comprehensive email validator with security checks.

    Validates email addresses for syntax, DNS records, disposable domains,
    and role-based addresses. Configurable to balance security vs usability.

    Configuration (settings.py):
        SYNTEK_SECURITY_INPUT = {
            'EMAIL_VALIDATION': {
                'CHECK_DNS': True,
                'CHECK_DISPOSABLE': True,
                'CHECK_ROLE_BASED': True,
                'ALLOW_INTERNATIONALIZED': True,
                'CUSTOM_DISPOSABLE_DOMAINS': [],
                'CUSTOM_ALLOWED_DOMAINS': [],
                'ROLE_BASED_PREFIXES': ['admin', 'info', 'support', 'noreply'],
            }
        }

    Example:
        >>> validator = EmailValidator()
        >>> is_valid, email, error = validator.validate('user@example.com')
        >>> if not is_valid:
        ...     raise ValidationError(error)
    """

    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        "tempmail.com",
        "guerrillamail.com",
        "mailinator.com",
        "10minutemail.com",
        "throwaway.email",
        "temp-mail.org",
        "fakeinbox.com",
        "yopmail.com",
        "maildrop.cc",
        "getnada.com",
        "trashmail.com",
        "sharklasers.com",
    }

    # Common role-based email prefixes
    ROLE_BASED_PREFIXES = {
        "admin",
        "administrator",
        "info",
        "support",
        "help",
        "sales",
        "marketing",
        "noreply",
        "no-reply",
        "postmaster",
        "webmaster",
        "hostmaster",
        "abuse",
        "security",
    }

    # Email regex pattern (simplified RFC 5322)
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __init__(self):
        """Initialize validator with configuration."""
        self.config = self._get_config()

    def _get_config(self) -> dict:
        """Get email validation configuration from settings.

        Returns:
            dict: Configuration dictionary
        """
        security_config = getattr(settings, "SYNTEK_SECURITY_INPUT", {})
        email_config = security_config.get("EMAIL_VALIDATION", {})

        # Default configuration
        defaults = {
            "CHECK_DNS": True,
            "CHECK_DISPOSABLE": True,
            "CHECK_ROLE_BASED": False,  # Allow role-based by default
            "ALLOW_INTERNATIONALIZED": True,
            "CUSTOM_DISPOSABLE_DOMAINS": [],
            "CUSTOM_ALLOWED_DOMAINS": [],
            "ROLE_BASED_PREFIXES": list(self.ROLE_BASED_PREFIXES),
        }

        # Merge with user configuration
        defaults.update(email_config)
        return defaults

    def validate(
        self,
        email: str,
        check_dns: Optional[bool] = None,
        check_disposable: Optional[bool] = None,
        check_role_based: Optional[bool] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate an email address comprehensively.

        Args:
            email: Email address to validate
            check_dns: Override config for DNS check
            check_disposable: Override config for disposable check
            check_role_based: Override config for role-based check

        Returns:
            Tuple of (is_valid, normalized_email, error_message)

        Examples:
            >>> validator = EmailValidator()
            >>> is_valid, email, error = validator.validate('user@example.com')
            >>> assert is_valid is True

            >>> is_valid, email, error = validator.validate('invalid-email')
            >>> assert is_valid is False
            >>> assert 'Invalid email syntax' in error

            >>> is_valid, email, error = validator.validate('user@tempmail.com')
            >>> assert is_valid is False
            >>> assert 'disposable' in error.lower()
        """
        if not email:
            return False, None, "Email address is required"

        # Normalize email
        email = email.strip().lower()

        # Check syntax
        is_valid, error = self._check_syntax(email)
        if not is_valid:
            return False, None, error

        # Extract domain
        domain = email.split("@")[1]

        # Check if domain is in allowed list (skip other checks)
        if self._is_allowed_domain(domain):
            return True, email, None

        # Check disposable domains
        if check_disposable is None:
            check_disposable = self.config.get("CHECK_DISPOSABLE", True)

        if check_disposable and self._is_disposable(domain):
            logger.warning(f"Disposable email domain detected: {domain}")
            return False, None, "Disposable email addresses are not allowed"

        # Check DNS records
        if check_dns is None:
            check_dns = self.config.get("CHECK_DNS", True)

        if check_dns:
            has_mx, error = self._check_dns_records(domain)
            if not has_mx:
                return False, None, error

        # Check role-based addresses
        if check_role_based is None:
            check_role_based = self.config.get("CHECK_ROLE_BASED", False)

        if check_role_based and self._is_role_based(email):
            logger.warning(f"Role-based email detected: {email}")
            return False, None, "Role-based email addresses are not allowed"

        # All checks passed
        return True, email, None

    def _check_syntax(self, email: str) -> Tuple[bool, Optional[str]]:
        """Check email syntax validity.

        Args:
            email: Email address to check

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Use Django's built-in validator first
        try:
            django_validate_email(email)
        except ValidationError as e:
            return False, f"Invalid email syntax: {e.message}"

        # Additional pattern check
        if not self.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"

        # Check for internationalized domain names
        if not self.config.get("ALLOW_INTERNATIONALIZED", True):
            if any(ord(char) > 127 for char in email):
                return False, "Internationalized email addresses are not allowed"

        return True, None

    def _is_allowed_domain(self, domain: str) -> bool:
        """Check if domain is in the allowed list.

        Args:
            domain: Email domain to check

        Returns:
            bool: True if domain is explicitly allowed
        """
        allowed_domains = self.config.get("CUSTOM_ALLOWED_DOMAINS", [])
        return domain in allowed_domains

    def _is_disposable(self, domain: str) -> bool:
        """Check if domain is a disposable email provider.

        Args:
            domain: Email domain to check

        Returns:
            bool: True if domain is disposable
        """
        # Check built-in list
        if domain in self.DISPOSABLE_DOMAINS:
            return True

        # Check custom list
        custom_disposable = self.config.get("CUSTOM_DISPOSABLE_DOMAINS", [])
        if domain in custom_disposable:
            return True

        return False

    def _check_dns_records(self, domain: str) -> Tuple[bool, Optional[str]]:
        """Check if domain has valid MX records.

        Args:
            domain: Email domain to check

        Returns:
            Tuple of (has_mx_records, error_message)
        """
        try:
            # Query MX records
            import dns.resolver  # type: ignore[import]

            mx_records = dns.resolver.resolve(domain, "MX")

            if not mx_records:
                logger.warning(f"No MX records found for domain: {domain}")
                return False, f"Domain '{domain}' has no mail servers configured"

            return True, None

        except ImportError:
            # dnspython not installed - skip DNS check
            logger.warning("dnspython not installed, skipping DNS verification")
            return True, None

        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain does not exist: {domain}")
            return False, f"Domain '{domain}' does not exist"

        except dns.resolver.NoAnswer:
            logger.warning(f"No MX records for domain: {domain}")
            return False, f"Domain '{domain}' has no mail servers"

        except dns.resolver.Timeout:
            logger.warning(f"DNS timeout for domain: {domain}")
            # Allow on timeout (fail-open)
            return True, None

        except Exception as e:
            logger.error(f"DNS check failed for {domain}: {e}")
            # Allow on error (fail-open)
            return True, None

    def _is_role_based(self, email: str) -> bool:
        """Check if email is a role-based address.

        Args:
            email: Email address to check

        Returns:
            bool: True if email is role-based
        """
        local_part = email.split("@")[0]
        role_prefixes = self.config.get("ROLE_BASED_PREFIXES", [])

        return local_part.lower() in role_prefixes

    @classmethod
    def get_domain(cls, email: str) -> Optional[str]:
        """Extract domain from email address.

        Args:
            email: Email address

        Returns:
            str: Domain part of email, or None if invalid
        """
        try:
            return email.split("@")[1].lower()
        except (IndexError, AttributeError):
            return None

    @classmethod
    def normalize(cls, email: str) -> str:
        """Normalize email address to lowercase.

        Args:
            email: Email address to normalize

        Returns:
            str: Normalized email address
        """
        return email.strip().lower()
