# Staging Environment

## Overview

Staging environment is for testing modules in near-production conditions before releasing to production.

**Note:** This repository contains **modules**, not a deployable application. Staging refers to testing modules in staging environments of projects that consume these modules (e.g., syntek-platform).

## Module Publishing to Staging

### Backend Modules (PyPI Test)

```bash
# Build package
cd backend/authentication
python setup.py sdist bdist_wheel

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI in syntek-platform staging
pip install --index-url https://test.pypi.org/simple/ syntek-authentication==1.0.0rc1
```

### Web/Mobile Modules (NPM with Tag)

```bash
# Publish with staging tag
cd web/packages/ui-auth
npm version prerelease --preid=rc
npm publish --tag staging

# Install in syntek-platform staging
npm install @syntek/ui-auth@staging
```

### Rust Modules (Git Branch)

```bash
# Create staging branch
git checkout -b staging/encryption-v1.0.0-rc1

# Push to remote
git push origin staging/encryption-v1.0.0-rc1

# Use in syntek-platform Cargo.toml
# [dependencies]
# syntek-encryption = { git = "https://github.com/syntek/syntek-modules", branch = "staging/encryption-v1.0.0-rc1" }
```

## Testing Modules in Staging

### 1. Update Module Version in Consumer Projects

**syntek-platform staging environment:**

```bash
# Update backend requirements
echo "syntek-authentication==1.0.0rc1" >> requirements-staging.txt

# Update web package.json
npm install @syntek/ui-auth@staging

# Update rust dependencies
# Edit Cargo.toml with staging branch
```

### 2. Deploy to Staging Environment

```bash
# Deploy syntek-platform to staging with updated modules
cd ~/syntek-platform
git checkout staging
# Update module versions
git commit -m "Update syntek-modules to staging versions"
git push origin staging

# CI/CD deploys to staging
```

### 3. Run Integration Tests

```bash
# Run integration tests in staging
./scripts/test-staging.sh

# Manual testing
open https://staging.syntek-platform.com
```

## Staging Checklist

Before releasing modules to production:

- [ ] All unit tests pass
- [ ] Integration tests pass in staging environment
- [ ] Performance tests pass
- [ ] Security scan passed
- [ ] No breaking changes (or documented)
- [ ] Changelog updated
- [ ] Documentation updated
- [ ] Migration guides written (if breaking changes)
- [ ] Backwards compatibility tested (if applicable)
- [ ] Load testing completed
- [ ] Monitoring and logging working
- [ ] Rollback plan documented

## Monitoring Staging

### Backend Modules

```bash
# Check GlitchTip for errors
open https://glitchtip.syntek.com/syntek-platform-staging

# Check PostgreSQL queries
.claude/plugins/db-tool.py slow-queries --env staging

# Check Rust encryption performance
.claude/plugins/log-tool.py search "encryption_time" --env staging
```

### Web/Mobile Modules

```bash
# Check browser console errors
.claude/plugins/chrome-tool.py errors --env staging

# Check bundle sizes
npm run analyze --workspace=@syntek/ui-auth

# Check performance
lighthouse https://staging.syntek-platform.com
```

## Staging Issues

### Rollback Module Version

```bash
# Backend
pip install syntek-authentication==0.9.0

# Web/Mobile
npm install @syntek/ui-auth@0.9.0

# Rust
# Edit Cargo.toml to use previous version/branch
```

### Debug Module in Staging

```bash
# Enable debug logging
export DEBUG=syntek-modules:*

# Add temporary logging to module
# Republish to staging with version bump
```

## Staging Data

### Test Data

```bash
# Load staging test data
python manage.py loaddata staging_users
python manage.py loaddata staging_subscriptions
```

### Data Sanitization

```bash
# If using production snapshot
# Sanitize sensitive data
python manage.py sanitize_staging_data
```

## Staging Configuration

### Environment Variables

```bash
# .env.staging
DEBUG=False
ENVIRONMENT=staging
GLITCHTIP_DSN=https://staging-dsn@glitchtip.syntek.com/1
DATABASE_URL=postgresql://staging_db
RUST_ENCRYPTION_KEY=<staging-key>
CLOUDINARY_CLOUD_NAME=syntek-staging
```

### Feature Flags

```python
# Test new features in staging first
FEATURE_FLAGS = {
    'new_subscription_flow': True,  # Enabled in staging
    'beta_analytics': True,          # Enabled in staging
}
```

## Promoting to Production

Once staging tests pass:

```bash
# 1. Merge staging branch to main
git checkout main
git merge staging/authentication-v1.0.0-rc1

# 2. Tag release
git tag v1.0.0
git push origin v1.0.0

# 3. Publish to production registries
# See production.md for details
```

## Useful Commands

```bash
# Check staging status
.claude/plugins/project-tool.py status --env staging

# View staging logs
.claude/plugins/log-tool.py view --env staging --tail 100

# Run staging tests
pytest tests/staging

# Check staging performance
.claude/plugins/quality-tool.py benchmark --env staging
```
