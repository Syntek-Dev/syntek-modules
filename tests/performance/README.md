# Performance Testing

Load testing for authentication endpoints using k6 and Locust.

## Quick Start

\`\`\`bash
# Install k6
brew install k6

# Run load test
k6 run k6/auth/login.js

# Install Locust
pip install locust

# Run Locust
locust -f locust/auth_loadtest.py
\`\`\`

## Performance Targets

- Login: < 500ms (p95)
- Registration: < 700ms (p95)
- Throughput: 1000+ req/s
- Concurrent users: 10,000

## Tests

- Smoke test: 1 user
- Load test: 100 users, 10min
- Stress test: 1000+ users
- Spike test: Sudden surge
- Soak test: 1 hour sustained

See individual test files for details.
