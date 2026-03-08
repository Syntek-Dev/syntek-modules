## Summary

<!-- 1–3 bullet points describing what this PR does -->

-
-

## Type of Change

- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring (no behaviour change)
- [ ] Tooling / CI

## Related Issues

<!-- Closes #123 or N/A -->

## syntek-docs PR

<!-- If this PR adds or changes any public API, a linked syntek-docs PR is required before merging to staging/main -->
<!-- Link: https://syntekstudio.com/dev/docs — docs repo: syntek-docs -->

- [ ] No public API changes — docs PR not required
- [ ] Docs PR raised: <!-- link here -->

## Testing

<!-- How were these changes tested? Which syntek-dev test commands were run? -->

```bash
syntek-dev test --
```

## Checklist

- [ ] `syntek-dev lint --fix` run and all issues resolved
- [ ] `syntek-dev lint` passes (exit 0)
- [ ] `syntek-dev ci` passes locally
- [ ] Tests added or updated for new behaviour
- [ ] Version files updated if applicable (`VERSION`, `CHANGELOG.md`, etc.)
- [ ] Documentation updated if applicable
- [ ] Commit messages follow the format in `.claude/GIT-GUIDE.md`
- [ ] `syntek-docs` PR raised and linked above (if public API changed)

## Branch Flow

- [ ] This PR targets `testing` (not `dev`, `staging`, or `main` directly)
