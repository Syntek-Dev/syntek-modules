#!/usr/bin/env bash
# Install the syntek CLI globally

set -e

echo "🚀 Installing syntek CLI..."

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed. Please install Rust first:"
    echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

# Navigate to CLI directory and install
cd rust/project-cli
echo "📦 Building CLI..."
cargo install --path .

echo ""
echo "✅ syntek CLI installed successfully!"
echo ""
echo "Next steps:"
echo "  1. syntek install  - Install all dependencies"
echo "  2. syntek init     - Setup Git hooks, secrets, and dev tools"
echo "  3. syntek dev      - Start development environment"
echo ""
echo "Available commands:"
echo "  syntek install     - Install dependencies"
echo "  syntek init        - Initialize project (hooks, secrets, dev tools)"
echo "  syntek dev         - Start development environment"
echo "  syntek test        - Run test suite"
echo "  syntek lint        - Lint all code"
echo "  syntek format      - Format all code"
echo "  syntek build       - Build all projects"
echo "  syntek audit       - Security audit (all ecosystems)"
echo "  syntek clean       - Clean build artifacts"
echo ""
echo "Run 'syntek --help' for more information."
