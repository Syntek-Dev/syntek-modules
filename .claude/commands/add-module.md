---
description: Scaffold a new module in the correct layer
usage: /add-module <layer> <module-name>
---

Scaffold a new module package in the correct layer.

**Layers:** `backend`, `web`, `mobile`, `rust`

**Examples:**
```bash
/add-module backend syntek-crm
/add-module web @syntek/ui-crm
/add-module mobile @syntek/mobile-crm
/add-module rust syntek-signing
```

**Backend package structure (`packages/backend/syntek-<name>/`):**
```
syntek-<name>/
├── pyproject.toml
├── CHANGELOG.md
├── README.md
├── syntek_<name>/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   └── settings.py      # SYNTEK_<NAME> defaults
└── tests/
    ├── __init__.py
    └── test_<name>.py
```

**Web package structure (`packages/web/<name>/`):**
```
<name>/
├── package.json
├── CHANGELOG.md
├── src/
│   ├── index.ts
│   └── components/
└── tests/
```

**Remember:**
- Register in `pnpm-workspace.yaml` (for web/mobile)
- Register in `Cargo.toml` workspace (for Rust)
- Register in root `pyproject.toml` (for backend)
- Add entry to Module Registry in `.claude/CLAUDE.md`
- Add entry to README.md module catalogue

$ARGUMENTS
