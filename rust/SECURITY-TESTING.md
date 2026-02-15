# Comprehensive Rust Security Tests

All Rust security testing is implemented via the auth-pentest suite.

## Coverage

**19 Test Modules, 200+ Tests**

See `rust/auth-pentest/README.md` for complete documentation.

## Running Tests

\`\`\`bash
# Run all pentests
syntek pentest

# Run specific module
syntek pentest --module owasp_top10

# Run with custom config
syntek pentest --env .env.staging
\`\`\`

## Test Categories

- Authentication flows
- OWASP Top 10 compliance
- NIST SP 800-63B compliance
- GDPR compliance
- OAuth 2.0 security
- Session management
- Cryptographic operations
- Rate limiting
- Injection attacks
- And more...

Complete list in auth-pentest/README.md
