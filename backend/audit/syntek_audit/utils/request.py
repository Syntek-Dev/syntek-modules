"""Request utilities for IP extraction and validation.

This module provides centralised request handling utilities including
IP address extraction, validation, and anonymisation. All middleware
and services should use these utilities instead of implementing their own.

SECURITY NOTE:
- IP extraction handles X-Forwarded-For headers from reverse proxies
- Anonymisation follows GDPR-compliant Google Analytics approach
- Validation supports both IPv4 and IPv6 addresses

GDPR Compliance:
- Security audit logs may retain full IP addresses (legitimate interest)
- Non-security logs should use anonymise_ip() for GDPR compliance
- Recommended retention: 90 days for security logs, 30 days for general logs

Example:
    >>> from syntek_audit.utils.request import get_client_ip, anonymise_ip
    >>> ip = get_client_ip(request)
    >>> anonymised_ip = anonymise_ip(ip)
"""

import ipaddress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest


def _get_request_header(request: "HttpRequest", header_name: str, default: str = "") -> str:
    """Safely get a header value from the request.

    Args:
        request: The HTTP request object.
        header_name: The header name to retrieve.
        default: Default value if header is not present.

    Returns:
        The header value or default.
    """
    # Use getattr to safely access headers which may not be recognized by type checker
    return getattr(request.headers, "get", lambda k, d: d)(header_name, default)


def get_client_ip(request: "HttpRequest", anonymise: bool = False) -> str:
    """Extract the client IP address from an HTTP request.

    Handles X-Forwarded-For header from reverse proxies (nginx, load balancers).
    Takes the first IP in the X-Forwarded-For chain as the client's real IP.

    Args:
        request: The Django HTTP request object.
        anonymise: If True, return GDPR-compliant anonymised IP.

    Returns:
        The client's IP address (full or anonymised based on parameter).
        Returns 'unknown' if IP cannot be determined.

    Example:
        >>> ip = get_client_ip(request)
        '192.168.1.45'
        >>> ip = get_client_ip(request, anonymise=True)
        '192.168.1.0'

    Note:
        For security logging, use full IP (legitimate interest under GDPR).
        For analytics/non-security logging, use anonymise=True.
    """
    x_forwarded_for = _get_request_header(request, "x-forwarded-for")
    if x_forwarded_for:
        # Take the first IP in the chain (client's real IP)
        ip = str(x_forwarded_for).split(",")[0].strip()
    else:
        ip = str(request.META.get("REMOTE_ADDR", "unknown"))

    if anonymise:
        return anonymise_ip(ip)
    return ip


def anonymise_ip(ip_address: str) -> str:
    """Anonymise an IP address for GDPR-compliant non-security logging.

    For IPv4: Zeros the last octet (e.g., 192.168.1.45 -> 192.168.1.0)
    For IPv6: Zeros the last 80 bits (keeps /48 prefix)

    This follows Google Analytics' IP anonymisation approach and is
    accepted as GDPR-compliant by most EU DPAs.

    Args:
        ip_address: The IP address to anonymise.

    Returns:
        The anonymised IP address, or 'unknown' if parsing fails.

    Example:
        >>> anonymise_ip("192.168.1.45")
        '192.168.1.0'
        >>> anonymise_ip("2001:db8:85a3::8a2e:370:7334")
        '2001:db8:85a3::'
    """
    if not ip_address or ip_address == "unknown":
        return "unknown"

    try:
        ip = ipaddress.ip_address(ip_address)
        if isinstance(ip, ipaddress.IPv4Address):
            # Zero the last octet for IPv4
            ipv4_network = ipaddress.IPv4Network(f"{ip_address}/24", strict=False)
            return str(ipv4_network.network_address)
        else:
            # Zero the last 80 bits for IPv6 (keep /48 prefix)
            ipv6_network = ipaddress.IPv6Network(f"{ip_address}/48", strict=False)
            return str(ipv6_network.network_address)
    except ValueError:
        # Invalid IP address format
        return "unknown"


def validate_ip_address(ip_address: str) -> bool:
    """Validate IP address format (IPv4 or IPv6).

    Args:
        ip_address: IP address string to validate.

    Returns:
        True if valid IPv4 or IPv6 address, False otherwise.

    Example:
        >>> validate_ip_address("192.168.1.1")
        True
        >>> validate_ip_address("invalid-ip")
        False
    """
    if not ip_address or ip_address == "unknown":
        return False

    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False
