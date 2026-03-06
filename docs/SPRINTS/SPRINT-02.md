# Sprint 02 — Design Tokens, CI/CD & Manifest Framework

**Sprint Goal**: Define the canonical design token system (colours, spacing, typography, fonts, breakpoints), wire up the full CI/CD pipeline, and establish the module manifest spec and shared Rust CLI installer library that every subsequent module ships with.

**Total Points**: 15 / 11 ⚠️ OVER CAPACITY
**MoSCoW Balance**: Must 100%
**Status**: Planned

## Stories

| Story | Title | Points | MoSCoW | Dependencies Met |
|---|---|---|---|---|
| [US003](../STORIES/US003.md) | Design Token System | 5 | Must | US001 ✓ |
| [US005](../STORIES/US005.md) | CI/CD Pipeline (Forgejo Actions) | 5 | Must | US001 ✓ |
| [US074](../STORIES/US074.md) | Module Manifest Spec & CLI Shared Framework | 5 | Must | US001 ✓ |

## Notes

- ⚠️ This sprint is 15 points, but all three stories are fully independent and target different team members working in parallel — US003 (design tokens), US005 (CI/CD pipeline), and US074 (Rust manifest crate). Each is a focused 5-point effort with no shared files.
- US074 must complete before any module story (US006 onwards) begins writing its `syntek.manifest.toml` or CLI binary.
- **Parallel opportunity**: The Rust layer (Sprint 03) and Web Design System (Sprint 31) can both begin after this sprint completes — US006 has no story dependencies, and US042 only needs US002 and US003.
