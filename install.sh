#!/usr/bin/env bash
# install.sh — Bootstrap syntek-modules development environment
#
# What this does:
#   1. Checks required tools are installed
#   2. Creates the Python virtual environment (.venv)
#   3. Installs root-level Python dev tooling into the venv
#   4. Installs JavaScript/TypeScript dependencies (pnpm install)
#   5. Builds the syntek-dev Rust CLI in release mode
#   6. Symlinks syntek-dev to ~/.local/bin/syntek-dev
#
# Usage:
#   chmod +x install.sh && ./install.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

step()  { echo -e "  ${CYAN}-->${RESET} $*"; }
ok()    { echo -e "  ${GREEN}OK${RESET}  $*"; }
warn()  { echo -e "  ${YELLOW}!${RESET}   $*"; }
fail()  { echo -e "  ${RED}FAIL${RESET} $*"; }
header(){ echo -e "\n${BOLD}$*${RESET}"; echo "-------------------------------------------"; }

# ---------------------------------------------------------------------------
# 1. Check required tools
# ---------------------------------------------------------------------------
header "Checking prerequisites"

MISSING=0
check_tool() {
    local tool="$1"
    local hint="$2"
    if command -v "$tool" &>/dev/null; then
        ok "$tool $(command -v "$tool")"
    else
        fail "$tool not found — $hint"
        MISSING=1
    fi
}

check_tool "rustup"  "install from https://rustup.rs"
check_tool "cargo"   "install from https://rustup.rs"
check_tool "uv"      "install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
check_tool "node"    "install Node.js 24.x from https://nodejs.org"
check_tool "pnpm"    "install with: npm install -g pnpm@10"
check_tool "git"     "install via your package manager"

if [[ $MISSING -eq 1 ]]; then
    echo ""
    fail "One or more required tools are missing. Install them and re-run ./install.sh"
    exit 1
fi

# Check Node.js version is 24+
NODE_MAJOR=$(node --version | sed 's/v//' | cut -d. -f1)
if [[ "$NODE_MAJOR" -lt 24 ]]; then
    warn "Node.js $NODE_MAJOR.x detected — Node.js 24.x is required"
fi

# ---------------------------------------------------------------------------
# 2. Python virtual environment
# ---------------------------------------------------------------------------
header "Python virtual environment"

if [[ ! -d "$ROOT/.venv" ]]; then
    step "Creating .venv (Python 3.14)..."
    uv venv --python 3.14
    ok ".venv created"
else
    ok ".venv already exists"
fi

# Activate for all remaining steps in this script.
# Note: this does NOT activate in the caller's shell — see the reminder below.
# shellcheck source=/dev/null
source "$ROOT/.venv/bin/activate"
ok "Virtual environment active — $(python --version)"

step "Syncing Python dev dependencies from uv.lock..."
uv sync --group dev --quiet
ok "Python dependencies installed"

# ---------------------------------------------------------------------------
# 3. JavaScript / TypeScript dependencies
# ---------------------------------------------------------------------------
header "JavaScript / TypeScript dependencies"

step "Running pnpm install..."
cd "$ROOT"
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
ok "pnpm install complete"

# ---------------------------------------------------------------------------
# 4. Build syntek-dev CLI (Rust, release mode)
# ---------------------------------------------------------------------------
header "Building syntek-dev CLI"

step "Running cargo build --release -p syntek-dev..."
cargo build --release -p syntek-dev
ok "Binary built: target/release/syntek-dev"

# ---------------------------------------------------------------------------
# 5. Install syntek-dev to ~/.local/bin
# ---------------------------------------------------------------------------
header "Installing syntek-dev to PATH"

mkdir -p "$BIN_DIR"
ln -sf "$ROOT/target/release/syntek-dev" "$BIN_DIR/syntek-dev"
ok "Symlinked to $BIN_DIR/syntek-dev"

# Check PATH
if echo "$PATH" | grep -q "$BIN_DIR"; then
    ok "$BIN_DIR is already on your PATH"
else
    warn "$BIN_DIR is not on your PATH"
    warn "Add this line to your ~/.zshrc or ~/.bashrc:"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}Setup complete.${RESET}"
echo ""
echo "  Activate the Python venv in your terminal:"
echo ""
echo "    source .venv/bin/activate"
echo ""
echo "  Then:"
echo "    syntek-dev --help             # view all CLI commands"
echo "    syntek-dev up                 # start development services"
echo "    syntek-dev test               # run the full test suite"
echo "    syntek-dev lint               # run all linters"
echo ""
