# Production Environment

## Overview

Production releases of modules to public registries for consumption by production applications.

## Release Process

### 1. Pre-Release Checklist

- [ ] All tests passing (unit, integration, e2e)
- [ ] Staging tests completed successfully
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] CHANGELOG.md updated
- [ ] VERSION bumped (semantic versioning)
- [ ] Migration guide written (if breaking changes)
- [ ] Backwards compatibility verified
- [ ] Code review approved
- [ ] Release notes prepared

### 2. Version Bumping

```bash
# Use version management agent
/syntek-dev-suite:version
Bump authentication module to v1.0.0

# Or manually
cd backend/authentication
# Edit setup.py version
git commit -m "Bump authentication to v1.0.0"
git tag authentication-v1.0.0
```

### 3. Publishing

#### Backend Modules (PyPI)

```bash
# Build
cd backend/authentication
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*

# Verify
pip install syntek-authentication==1.0.0
```

#### Web/Mobile Modules (NPM)

```bash
# Publish to NPM
cd web/packages/ui-auth
npm version 1.0.0
npm publish

# Verify
npm install @syntek/ui-auth@1.0.0
```

#### Rust Modules (Crates.io)

```bash
# Publish to crates.io
cd rust/encryption
cargo publish

# Verify
cargo search syntek-encryption
```

### 4. Git Tagging

```bash
# Create release tag
git tag -a v1.0.0 -m "Release v1.0.0

- New subscription module
- Enhanced encryption
- Bug fixes and improvements"

# Push tags
git push origin v1.0.0
git push origin --tags
```

### 5. GitHub Release

```bash
# Create GitHub release
gh release create v1.0.0 \
  --title "Syntek Modules v1.0.0" \
  --notes "See CHANGELOG.md for details"

# Or use agent
/syntek-dev-suite:git
Create GitHub release for v1.0.0
```

### 6. Update Consuming Projects

**syntek-platform production:**

```bash
# Update requirements.txt
syntek-authentication==1.0.0
syntek-subscriptions==1.0.0

# Update package.json
{
  "@syntek/ui-auth": "^1.0.0",
  "@syntek/ui-subscriptions": "^1.0.0"
}

# Update Cargo.toml
[dependencies]
syntek-encryption = "1.0.0"
```

### 7. Monitor Production

```bash
# Check error rates
open https://glitchtip.syntek.com/syntek-platform-prod

# Check performance
.claude/plugins/quality-tool.py benchmark --env production

# Check logs
.claude/plugins/log-tool.py view --env production --tail 100
```

## Versioning Strategy

### Semantic Versioning

- **MAJOR (1.0.0):** Breaking changes
- **MINOR (1.1.0):** New features, backwards compatible
- **PATCH (1.1.1):** Bug fixes, backwards compatible

### Version Matrix

Maintain compatibility matrix:

```markdown
## Compatibility

| Module         | Version | Django | React | React Native |
| -------------- | ------- | ------ | ----- | ------------ |
| Authentication | 1.0.0   | 6.0+   | 19.0+ | 0.83+        |
| Subscriptions  | 1.0.0   | 6.0+   | 19.0+ | 0.83+        |
| Encryption     | 1.0.0   | 3.14+  | -     | -            |
```

## Production Monitoring

### Error Tracking

```bash
# GlitchTip dashboard
open https://glitchtip.syntek.com

# Check error rates
.claude/plugins/log-tool.py search "ERROR" --env production --last 24h
```

### Performance Monitoring

```bash
# Backend performance
.claude/plugins/db-tool.py slow-queries --env production

# Rust encryption performance
.claude/plugins/log-tool.py search "encryption_time" --env production

# Frontend bundle sizes
npm run analyze --workspaces
```

### Usage Analytics

```bash
# Module download stats
# PyPI: https://pypistats.org/packages/syntek-authentication
# NPM: npm info @syntek/ui-auth
# Crates.io: https://crates.io/crates/syntek-encryption
```

## Rollback Procedure

### If Critical Bug Found

1. **Immediate:** Notify all consumers

   ```bash
   # Slack/Email/GitHub issue
   echo "URGENT: Critical bug in syntek-authentication v1.0.0"
   ```

2. **Yank bad version** (don't delete)

   ```bash
   # PyPI
   twine yank syntek-authentication==1.0.0

   # NPM
   npm deprecate @syntek/ui-auth@1.0.0 "Critical bug, use 1.0.1"

   # Crates.io
   cargo yank syntek-encryption@1.0.0
   ```

3. **Publish patch immediately**

   ```bash
   # Fix bug
   # Bump to v1.0.1
   # Publish
   ```

4. **Update consuming projects**

   ```bash
   # Emergency deploy to production with v1.0.1
   ```

## Security Releases

### For Security Vulnerabilities

1. **DO NOT publish details publicly yet**
2. Fix vulnerability in private branch
3. Publish patched version immediately
4. Notify consumers privately first
5. Publish security advisory after consumers update

```bash
# Create security advisory
gh security-advisory create \
  --severity high \
  --cve-id CVE-2024-XXXXX \
  --description "SQL injection in authentication module"
```

## Production Support

### Support Channels

- **GitHub Issues:** Bug reports and feature requests
- **Slack:** #syntek-modules-support
- **Email:** <support@syntek.com>
- **Documentation:** <https://docs.syntek.com/modules>

### SLA

- **Critical bugs:** 4-hour response
- **Security issues:** 1-hour response
- **Feature requests:** 1-week response
- **Questions:** 24-hour response

## Documentation

### Public Documentation

```bash
# Build and publish docs
cd docs
make html
./deploy-docs.sh

# Verify
open https://docs.syntek.com/modules
```

### Release Notes

```markdown
## Release v1.0.0 - 2024-02-03

### New Features

- Subscription module with recurring billing
- Enhanced encryption with field-level granularity

### Breaking Changes

- Authentication module now requires Django 6.0+
- Migration required: `python manage.py migrate authentication`

### Bug Fixes

- Fixed memory leak in Rust encryption (#123)
- Fixed React Native touch handling (#124)

### Deprecations

- `old_login_method()` deprecated, use `new_login()` instead

### Upgrade Guide

See MIGRATION.md for detailed upgrade instructions.
```

## Continuous Deployment

### CI/CD Pipeline

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  publish-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Publish to PyPI
        run: |
          python setup.py sdist bdist_wheel
          twine upload dist/*

  publish-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Publish to NPM
        run: |
          npm publish --workspaces

  publish-rust:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Publish to crates.io
        run: |
          cargo publish --manifest-path rust/encryption/Cargo.toml
```

## Useful Commands

```bash
# Check production health
.claude/plugins/project-tool.py health --env production

# View production logs
.claude/plugins/log-tool.py view --env production

# Check module versions in production
.claude/plugins/project-tool.py versions --env production

# Audit production security
.claude/plugins/quality-tool.py security-audit --env production

# Generate release report
/syntek-dev-suite:reporting
Generate production release report for v1.0.0
```

## Disaster Recovery

### Backup Strategy

- Git tags are permanent backups
- All versions remain on registries
- Documentation archived per version

### Recovery

```bash
# Restore from git tag
git checkout v0.9.0

# Republish if needed
./scripts/publish.sh v0.9.0
```
