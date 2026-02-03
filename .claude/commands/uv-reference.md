# uv Quick Reference

`uv` is a fast Python package installer and resolver written in Rust. It's a drop-in replacement for pip that's 10-100x faster.

## Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with homebrew (macOS)
brew install uv
```

## Virtual Environments

```bash
# Create virtual environment
uv venv

# Create with specific Python version
uv venv --python 3.14

# Activate (same as regular venv)
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

## Package Installation

```bash
# Install packages (like pip install)
uv pip install django

# Install from requirements file
uv pip install -r requirements.txt

# Install from pyproject.toml
uv pip install -e .
uv pip install -e ".[dev]"
uv pip install -e ".[dev,test,docs]"

# Install specific module in development mode
uv pip install -e backend/authentication

# Install multiple modules
uv pip install -e backend/authentication -e backend/profiles

# Install from git
uv pip install "git+https://github.com/syntek/syntek-modules.git#subdirectory=backend/authentication"

# Install specific version
uv pip install django==6.0.2
```

## Package Management

```bash
# List installed packages
uv pip list

# Show package info
uv pip show django

# Freeze dependencies
uv pip freeze > requirements.txt

# Uninstall package
uv pip uninstall django

# Upgrade package
uv pip install --upgrade django

# Upgrade all packages
uv pip install --upgrade -r requirements.txt
```

## Working with pyproject.toml

```bash
# Install project with all dependencies
uv pip install -e .

# Install with optional dependencies
uv pip install -e ".[dev]"        # Development dependencies
uv pip install -e ".[test]"       # Test dependencies
uv pip install -e ".[docs]"       # Documentation dependencies
uv pip install -e ".[dev,test]"   # Multiple groups

# Sync dependencies (install/uninstall to match exactly)
uv pip sync requirements.txt
```

## Compilation

```bash
# Compile requirements (resolve dependencies)
uv pip compile pyproject.toml -o requirements.txt

# Compile with extras
uv pip compile pyproject.toml --extra dev -o requirements-dev.txt

# Update all dependencies
uv pip compile --upgrade pyproject.toml -o requirements.txt
```

## Performance

uv is significantly faster than pip:

| Operation                 | pip  | uv    | Speedup |
| ------------------------- | ---- | ----- | ------- |
| Install Django            | 5.2s | 0.3s  | 17x     |
| Install from cache        | 2.1s | 0.02s | 105x    |
| Large project (100+ deps) | 45s  | 2s    | 22x     |

## Comparison with pip

| Feature               | pip    | uv        |
| --------------------- | ------ | --------- |
| Speed                 | Slow   | Very Fast |
| Dependency resolution | Slow   | Fast      |
| Parallel downloads    | No     | Yes       |
| Cache                 | Basic  | Advanced  |
| Written in            | Python | Rust      |
| Drop-in replacement   | -      | Yes       |

## Common Workflows

### Project Setup

```bash
# Clone repo
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules

# Create virtual environment
uv venv
source .venv/bin/activate

# Install project with dev dependencies
uv pip install -e ".[dev]"

# Install specific modules
uv pip install -e backend/authentication -e backend/profiles
```

### Module Development

```bash
# Install module in development mode
cd backend/authentication
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Build distribution
python -m build
```

### Updating Dependencies

```bash
# Update a specific package
uv pip install --upgrade django

# Update all packages in requirements.txt
uv pip install --upgrade -r requirements.txt

# Recompile requirements with latest versions
uv pip compile --upgrade pyproject.toml -o requirements.txt
```

### Working with Multiple Modules

```bash
# Install all backend modules
uv pip install -e backend/*

# Or explicitly
uv pip install -e backend/authentication \
               -e backend/profiles \
               -e backend/media \
               -e backend/logging

# Update all modules
for module in backend/*/; do
    uv pip install --upgrade -e "$module"
done
```

## Environment Variables

```bash
# Set custom cache directory
export UV_CACHE_DIR=~/.cache/uv

# Set custom Python path
export UV_PYTHON=/usr/bin/python3.14

# Disable cache
export UV_NO_CACHE=1

# Verbose output
export UV_VERBOSE=1
```

## Tips & Tricks

### 1. Speed up CI/CD

```yaml
# .github/workflows/test.yml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv pip install -e ".[test]"
  # Much faster than pip!
```

### 2. Cache in Docker

```dockerfile
# Dockerfile
FROM python:3.14-slim

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy only requirements first (layer caching)
COPY pyproject.toml .
RUN uv pip install -e ".[dev]"

# Copy rest of code
COPY . .
```

### 3. Lock Dependencies

```bash
# Generate lock file
uv pip compile pyproject.toml -o requirements.lock

# Install from lock file (exact versions)
uv pip install -r requirements.lock
```

### 4. Parallel Installation

uv automatically parallelizes downloads and installations:

```bash
# This installs all packages in parallel
uv pip install django strawberry-graphql psycopg pytest black ruff mypy
```

### 5. Offline Installation

```bash
# Build wheel cache
uv pip download -r requirements.txt -d wheels/

# Install offline
uv pip install --no-index --find-links wheels/ -r requirements.txt
```

## Troubleshooting

### uv not found

```bash
# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Or source the env
source $HOME/.cargo/env
```

### Package not found

```bash
# Update uv
uv self update

# Clear cache
rm -rf ~/.cache/uv

# Try with verbose output
UV_VERBOSE=1 uv pip install package-name
```

### Conflict resolution

```bash
# Show dependency tree
uv pip tree

# Force reinstall
uv pip install --force-reinstall package-name

# Use pip compile to see conflicts
uv pip compile pyproject.toml --verbose
```

## Migration from pip

### requirements.txt → pyproject.toml

```bash
# Old way (pip)
pip install -r requirements.txt

# New way (uv with pyproject.toml)
uv pip install -e ".[dev]"
```

### setup.py → pyproject.toml

```bash
# Old way
pip install -e .

# New way (same command, different config file)
uv pip install -e .
```

All existing `pip install` commands work with uv:

```bash
# These all work with uv
uv pip install package
uv pip install -r requirements.txt
uv pip install -e .
uv pip install -e ".[dev]"
uv pip install package==1.0.0
uv pip install git+https://github.com/...
```

## Resources

- **Official Docs:** <https://github.com/astral-sh/uv>
- **Benchmarks:** <https://github.com/astral-sh/uv#benchmarks>
- **Changelog:** <https://github.com/astral-sh/uv/releases>
- **Discord:** <https://discord.gg/astral-sh>
