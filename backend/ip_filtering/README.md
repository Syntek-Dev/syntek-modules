# Syntek IP Filtering - IP Allowlist/Blocklist Middleware

## Overview

Syntek IP Filtering provides Django middleware for IP-based access control. It supports allowlist (whitelist) and blocklist (blacklist) modes, CIDR notation, and path-specific rules.

## Features

- **Allowlist Mode**: Only specified IPs allowed
- **Blocklist Mode**: All IPs allowed except specified
- **CIDR Support**: Define ranges (e.g., `192.168.1.0/24`)
- **Path-Specific**: Apply rules to specific paths (e.g., `/admin/`)
- **Caching**: Performance optimization with Redis/memory cache
- **IPv4/IPv6**: Support for both IP versions
- **Proxy-Aware**: Correctly extracts IP behind proxies/load balancers

## Installation

```bash
uv pip install syntek-ip-filtering
```

## Configuration

Add to `INSTALLED_APPS` (optional, middleware works standalone):

```python
INSTALLED_APPS = [
    ...
    'syntek_ip_filtering',
]
```

Add middleware:

```python
MIDDLEWARE = [
    ...
    'syntek_ip_filtering.middleware.IPAllowlistMiddleware',
    ...
]
```

Settings:

```python
SYNTEK_IP_FILTERING = {
    'MODE': 'allowlist',  # or 'blocklist'
    'ALLOWED_IPS': [
        '127.0.0.1',
        '::1',
        '192.168.1.0/24',  # CIDR notation
        '10.0.0.0/8',
    ],
    'BLOCKED_IPS': [
        '1.2.3.4',
        '5.6.7.0/24',
    ],
    'PROTECTED_PATHS': [
        '/admin/',
        '/api/admin/',
        '/internal/',
    ],
    'ENABLE_CACHING': True,
    'CACHE_TTL': 300,  # 5 minutes
    'RESPONSE_MESSAGE': 'Access denied from your IP address',
    'RESPONSE_STATUS': 403,
    'LOG_BLOCKED': True,
}
```

## Usage

### Allowlist Mode (Default)

Only specified IPs can access protected paths:

```python
SYNTEK_IP_FILTERING = {
    'MODE': 'allowlist',
    'ALLOWED_IPS': [
        '203.0.113.0/24',  # Office network
        '198.51.100.50',    # Specific admin IP
    ],
    'PROTECTED_PATHS': [
        '/admin/',
        '/api/admin/',
    ],
}
```

### Blocklist Mode

Block specific IPs while allowing all others:

```python
SYNTEK_IP_FILTERING = {
    'MODE': 'blocklist',
    'BLOCKED_IPS': [
        '192.0.2.100',      # Known bad actor
        '198.18.0.0/15',    # Blocked range
    ],
}
```

### Path-Specific Rules

Protect specific paths only:

```python
SYNTEK_IP_FILTERING = {
    'MODE': 'allowlist',
    'ALLOWED_IPS': ['192.168.1.0/24'],
    'PROTECTED_PATHS': [
        '/admin/',
        '/api/admin/',
        '/internal/',
    ],
}
# Other paths (/api/public/, /) are accessible to all
```

### Staging/Development Environment

Restrict entire site to internal IPs:

```python
# settings.py (staging)
SYNTEK_IP_FILTERING = {
    'MODE': 'allowlist',
    'ALLOWED_IPS': [
        '10.0.0.0/8',       # VPN network
        '172.16.0.0/12',    # Office network
        '203.0.113.50',     # Your home IP
    ],
    'PROTECTED_PATHS': [],  # Empty = protect all paths
}
```

## API Reference

### Middleware

#### IPAllowlistMiddleware

Main middleware class for IP filtering.

**Configuration Options:**

| Option             | Type | Default              | Description                      |
| ------------------ | ---- | -------------------- | -------------------------------- |
| `MODE`             | str  | `'allowlist'`        | `'allowlist'` or `'blocklist'`   |
| `ALLOWED_IPS`      | list | `['127.0.0.1']`      | IPs allowed in allowlist mode    |
| `BLOCKED_IPS`      | list | `[]`                 | IPs blocked in blocklist mode    |
| `PROTECTED_PATHS`  | list | `['/admin/']`        | Paths to protect (empty = all)   |
| `ENABLE_CACHING`   | bool | `True`               | Cache IP check results           |
| `CACHE_TTL`        | int  | `300`                | Cache TTL in seconds             |
| `RESPONSE_MESSAGE` | str  | `'Access denied...'` | Error message for blocked IPs    |
| `RESPONSE_STATUS`  | int  | `403`                | HTTP status for blocked requests |
| `LOG_BLOCKED`      | bool | `True`               | Log blocked access attempts      |
| `ENABLED`          | bool | `True`               | Enable/disable middleware        |

## Security Considerations

- **Proxy Configuration**: Ensure `HTTP_X_FORWARDED_FOR` is trusted (only from your load balancer)
- **Fail Closed**: Invalid configuration blocks all access by default
- **Cache Poisoning**: Cache TTL should be short enough to respond to threats
- **CIDR Ranges**: Be careful with broad ranges (e.g., `/8`) that may include unwanted IPs
- **Logging**: Enable `LOG_BLOCKED` to monitor suspicious activity
- **Rate Limiting**: Use with rate limiting for comprehensive protection

## Proxy/Load Balancer Setup

### Nginx

```nginx
location / {
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

### AWS ELB/ALB

Automatically sets `X-Forwarded-For` header.

### Cloudflare

Uses `CF-Connecting-IP` header (add custom extraction if needed).

## Performance

- **Caching**: Enables ~1000x faster lookups
- **CIDR**: Efficient IP range matching
- **Overhead**: ~1-5ms per request (cached)
- **Memory**: Minimal (~1KB per 1000 IPs)

## Testing

```bash
pytest tests/
```

## Common Patterns

### Admin-Only Access

```python
SYNTEK_IP_FILTERING = {
    'MODE': 'allowlist',
    'ALLOWED_IPS': ['office-network-cidr'],
    'PROTECTED_PATHS': ['/admin/'],
}
```

### Block Known Bad IPs

```python
SYNTEK_IP_FILTERING = {
    'MODE': 'blocklist',
    'BLOCKED_IPS': ['1.2.3.4', '5.6.7.8'],
}
```

### VPN-Only Staging

```python
SYNTEK_IP_FILTERING = {
    'MODE': 'allowlist',
    'ALLOWED_IPS': ['10.8.0.0/24'],  # VPN subnet
    'PROTECTED_PATHS': [],  # Protect everything
}
```

## License

MIT
