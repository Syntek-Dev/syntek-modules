# Syntek CLI Installation

This folder provides us with Rust CLI scripts using `syntek install [module]` to install the whole of a module in one
project. Including the Rust security, Django and Postgres Backend, GraphQL API, web, mobile and shared UI frontend.

It will purely run to add the packages to the correct location not to install them.

We will need a command to initialise this repo in the CLI for projects to allow the Rust CLI to pull through what we need.

Each CLI tool should be modular and then called in a install.rs.

## Folder Structure

```text
cli/
├── README.md                    # This file
└── src/
    ├── commands/               # CLI command implementations
    │   ├── init.rs            # Initialize syntek in a project
    │   ├── install.rs         # Main installation orchestrator
    │   ├── list.rs            # List available modules
    │   └── ...                # Additional commands
    ├── config/                 # Configuration management
    │   ├── loader.rs          # Load and parse syntek config files
    │   ├── validator.rs       # Validate project structure
    │   └── preferences.rs     # Installation preferences
    ├── install/                # Module installation logic
    │   ├── backend.rs         # Backend module installers
    │   ├── frontend.rs        # Frontend (web/mobile/shared) installers
    │   ├── rust.rs            # Rust crate installers
    │   └── graphql.rs         # GraphQL schema installers
    ├── security/              # Security utilities
    │   ├── permissions.rs     # File permission validation
    │   ├── env.rs             # Environment variable sanitization
    │   └── secrets.rs         # Secret handling for API keys/tokens
    └── utils/                 # Shared utilities
        ├── exec.rs            # Command execution helpers
        ├── fs.rs              # File operations
        ├── path.rs            # Path validation
        └── error.rs           # Error handling
```

## Directory Purpose

### `commands/`

Individual CLI command implementations (subcommands). Each command is self-contained and handles a specific CLI operation:

- **`init.rs`** - Initialize syntek in a project (create config, setup structure)
- **`install.rs`** - Main installation orchestrator that coordinates module installation
- **`list.rs`** - List available modules from the syntek-modules repository
- Additional commands as needed

### `config/`

Configuration management for reading, validating, and managing syntek project settings:

- **`loader.rs`** - Load and parse syntek configuration files (TOML/JSON)
- **`validator.rs`** - Validate project structure and dependencies
- **`preferences.rs`** - Manage installation preferences (target directories, versions)

### `install/`

Module installation logic organized by technology stack. Each installer handles copying/configuring specific module types:

- **`backend.rs`** - Django backend module installers (security bundles, feature modules)
- **`frontend.rs`** - Web (Next.js), Mobile (React Native), and Shared UI installers
- **`rust.rs`** - Rust crate installers (encryption, security layers)
- **`graphql.rs`** - GraphQL schema and middleware installers

### `security/`

Security utilities following secure CLI patterns:

- **`permissions.rs`** - Validate file permissions, ensure secure config files
- **`env.rs`** - Environment variable sanitization, prevent secret leakage
- **`secrets.rs`** - Secret handling for API keys, tokens (using `secrecy` crate)

### `utils/`

Shared helper functions used across commands:

- **`exec.rs`** - Command execution helpers (run shell commands securely)
- **`fs.rs`** - File operations (copy, move, validate paths)
- **`path.rs`** - Path validation and manipulation
- **`error.rs`** - Centralized error handling and reporting

## Design Principles

1. **Modularity** - Each command is self-contained and reusable
2. **Security First** - Follow secure CLI patterns (no secrets in args, permission validation)
3. **Separation of Concerns** - Clear boundaries between commands, config, installation, and utilities
4. **Error Handling** - Comprehensive error messages with actionable suggestions
5. **No Installation** - Only copies modules to correct locations, doesn't run package managers
