#!/usr/bin/env python3
"""
db-tool.py

Provides database detection and configuration utilities for Claude Code agents.
Returns structured JSON output for integration with database, backend, and setup agents.
Supports detection of database type, connection info, and ORM/migration framework.
"""
import json
import sys
import os
import re
from pathlib import Path
from typing import Optional, Any


def find_config_files(directory: Optional[str] = None) -> dict:
    """
    Find database configuration files in the specified directory.

    Args:
        directory: Directory to search (uses current directory if None)

    Returns:
        Dictionary containing found configuration files
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    # Database config file patterns and their frameworks
    config_patterns = {
        # Laravel/PHP
        "config/database.php": "laravel",
        ".env": "env",
        # Django/Python
        "settings.py": "django",
        "**/settings.py": "django",
        "config/settings.py": "django",
        # Prisma
        "prisma/schema.prisma": "prisma",
        # TypeORM
        "ormconfig.json": "typeorm",
        "ormconfig.js": "typeorm",
        "data-source.ts": "typeorm",
        "src/data-source.ts": "typeorm",
        # Sequelize
        "config/config.json": "sequelize",
        ".sequelizerc": "sequelize",
        # Knex
        "knexfile.js": "knex",
        "knexfile.ts": "knex",
        # Rails
        "config/database.yml": "rails",
        # Alembic (SQLAlchemy)
        "alembic.ini": "alembic",
        # General
        "database.json": "generic",
        "db.json": "generic",
    }

    found_files = []
    detected_frameworks = set()

    for pattern, framework in config_patterns.items():
        if "*" in pattern:
            matches = list(search_dir.glob(pattern))
        else:
            path = search_dir / pattern
            matches = [path] if path.exists() else []

        for match in matches:
            if match.is_file():
                found_files.append({
                    "path": str(match),
                    "name": match.name,
                    "framework": framework,
                })
                detected_frameworks.add(framework)

    return {
        "files": found_files,
        "frameworks": sorted(detected_frameworks),
        "count": len(found_files),
        "directory": str(search_dir)
    }


def detect_database_from_env(env_path: Optional[str] = None) -> dict:
    """
    Detect database configuration from environment files.

    Args:
        env_path: Path to env file (searches for .env files if None)

    Returns:
        Dictionary containing detected database configuration
    """
    search_paths = []

    if env_path:
        search_paths = [Path(env_path)]
    else:
        cwd = Path.cwd()
        search_paths = [
            cwd / ".env",
            cwd / ".env.local",
            cwd / ".env.dev",
            cwd / ".env.development",
        ]

    # Database connection patterns
    db_patterns = {
        "DB_CONNECTION": "connection_type",
        "DB_HOST": "host",
        "DB_PORT": "port",
        "DB_DATABASE": "database",
        "DB_USERNAME": "username",
        "DATABASE_URL": "url",
        "POSTGRES_HOST": "host",
        "POSTGRES_DB": "database",
        "MYSQL_HOST": "host",
        "MYSQL_DATABASE": "database",
        "MONGODB_URI": "url",
        "REDIS_HOST": "redis_host",
        "REDIS_PORT": "redis_port",
    }

    config = {}
    source_file = None

    for path in search_paths:
        if path.exists():
            source_file = str(path)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue

                        if '=' in line:
                            key, _, value = line.partition('=')
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")

                            if key in db_patterns:
                                config[db_patterns[key]] = value
                            elif key == "DB_CONNECTION":
                                config["type"] = value
            except Exception:
                continue
            break

    if not config:
        return {"detected": False, "error": "No database configuration found in env files"}

    # Determine database type
    db_type = None
    if "connection_type" in config:
        db_type = config["connection_type"]
    elif "url" in config:
        url = config["url"].lower()
        if "postgres" in url or "postgresql" in url:
            db_type = "postgresql"
        elif "mysql" in url:
            db_type = "mysql"
        elif "mongodb" in url:
            db_type = "mongodb"
        elif "sqlite" in url:
            db_type = "sqlite"
        elif "mssql" in url or "sqlserver" in url:
            db_type = "sqlserver"

    return {
        "detected": True,
        "type": db_type,
        "host": config.get("host"),
        "port": config.get("port"),
        "database": config.get("database"),
        "username": config.get("username"),
        "has_url": "url" in config,
        "has_redis": "redis_host" in config or "redis_port" in config,
        "source_file": source_file,
    }


def detect_orm_framework(directory: Optional[str] = None) -> dict:
    """
    Detect the ORM and migration framework used in the project.

    Args:
        directory: Directory to search (uses current directory if None)

    Returns:
        Dictionary containing detected ORM information
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    detected = {
        "orm": None,
        "migration_tool": None,
        "language": None,
        "indicators": [],
    }

    # Check for package files and their contents
    checks = [
        # Laravel/Eloquent
        ("composer.json", "laravel/framework", "eloquent", "laravel", "php"),
        ("composer.json", "illuminate/database", "eloquent", "laravel", "php"),
        # Django
        ("requirements.txt", "django", "django-orm", "django", "python"),
        ("Pipfile", "django", "django-orm", "django", "python"),
        ("pyproject.toml", "django", "django-orm", "django", "python"),
        # SQLAlchemy
        ("requirements.txt", "sqlalchemy", "sqlalchemy", "alembic", "python"),
        ("requirements.txt", "alembic", "sqlalchemy", "alembic", "python"),
        # Prisma
        ("package.json", "prisma", "prisma", "prisma", "typescript"),
        ("package.json", "@prisma/client", "prisma", "prisma", "typescript"),
        # TypeORM
        ("package.json", "typeorm", "typeorm", "typeorm", "typescript"),
        # Sequelize
        ("package.json", "sequelize", "sequelize", "sequelize-cli", "javascript"),
        # Knex
        ("package.json", "knex", "knex", "knex", "javascript"),
        # Rails ActiveRecord
        ("Gemfile", "rails", "activerecord", "rails", "ruby"),
        ("Gemfile", "activerecord", "activerecord", "rails", "ruby"),
        # Drizzle
        ("package.json", "drizzle-orm", "drizzle", "drizzle-kit", "typescript"),
    ]

    for pkg_file, indicator, orm, migration, lang in checks:
        pkg_path = search_dir / pkg_file
        if pkg_path.exists():
            try:
                content = pkg_path.read_text(encoding='utf-8').lower()
                if indicator.lower() in content:
                    detected["orm"] = orm
                    detected["migration_tool"] = migration
                    detected["language"] = lang
                    detected["indicators"].append(f"Found '{indicator}' in {pkg_file}")
                    break
            except Exception:
                continue

    # Check for migration directories
    migration_dirs = [
        ("database/migrations", "laravel"),
        ("migrations", "generic"),
        ("prisma/migrations", "prisma"),
        ("src/migrations", "typeorm"),
        ("db/migrate", "rails"),
        ("alembic/versions", "alembic"),
    ]

    for dir_path, framework in migration_dirs:
        full_path = search_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            migrations = list(full_path.glob("*.php")) + \
                        list(full_path.glob("*.py")) + \
                        list(full_path.glob("*.ts")) + \
                        list(full_path.glob("*.js")) + \
                        list(full_path.glob("*.rb")) + \
                        list(full_path.glob("*.sql"))

            detected["migration_directory"] = str(full_path)
            detected["migration_count"] = len(migrations)
            detected["indicators"].append(f"Found migration directory: {dir_path}")

            if not detected["migration_tool"]:
                detected["migration_tool"] = framework

    detected["detected"] = detected["orm"] is not None or detected.get("migration_directory") is not None

    return detected


def find_migrations(directory: Optional[str] = None) -> dict:
    """
    Find and list migration files in the project.

    Args:
        directory: Directory to search (uses current directory if None)

    Returns:
        Dictionary containing migration file information
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    # Common migration directories
    migration_dirs = [
        "database/migrations",
        "migrations",
        "prisma/migrations",
        "src/migrations",
        "db/migrate",
        "alembic/versions",
    ]

    found_migrations = []
    migration_dir = None

    for dir_path in migration_dirs:
        full_path = search_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            migration_dir = str(full_path)

            # Find migration files
            for ext in ["php", "py", "ts", "js", "rb", "sql"]:
                for file_path in full_path.glob(f"*.{ext}"):
                    # Extract timestamp/version from filename
                    name = file_path.stem
                    timestamp = None

                    # Common patterns: 2024_01_15_000000_, 20240115000000_, V1__
                    timestamp_match = re.match(r'^(\d{4}_?\d{2}_?\d{2}_?\d{6}|\d{14}|V\d+)', name)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)

                    found_migrations.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "timestamp": timestamp,
                        "extension": ext,
                    })

            break

    # Sort by name (usually chronological)
    found_migrations.sort(key=lambda x: x["name"])

    return {
        "directory": migration_dir,
        "migrations": found_migrations,
        "count": len(found_migrations),
        "latest": found_migrations[-1]["name"] if found_migrations else None,
    }


def detect_database_type() -> dict:
    """
    Comprehensive database type detection using all available methods.

    Returns:
        Dictionary containing complete database detection results
    """
    result = {
        "detected": False,
        "type": None,
        "orm": None,
        "framework": None,
    }

    # Try env detection first
    env_detection = detect_database_from_env()
    if env_detection.get("detected"):
        result["detected"] = True
        result["type"] = env_detection.get("type")
        result["connection"] = {
            "host": env_detection.get("host"),
            "port": env_detection.get("port"),
            "database": env_detection.get("database"),
        }

    # Detect ORM
    orm_detection = detect_orm_framework()
    if orm_detection.get("detected"):
        result["detected"] = True
        result["orm"] = orm_detection.get("orm")
        result["migration_tool"] = orm_detection.get("migration_tool")
        result["language"] = orm_detection.get("language")

    # Find migrations
    migrations = find_migrations()
    if migrations.get("count", 0) > 0:
        result["has_migrations"] = True
        result["migration_count"] = migrations["count"]
        result["migration_directory"] = migrations["directory"]

    return result


def main():
    """Main entry point for the Database tool."""
    if len(sys.argv) < 2:
        # Default: comprehensive detection
        print(json.dumps(detect_database_type(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "detect":
        print(json.dumps(detect_database_type(), indent=2))

    elif command == "config":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(find_config_files(directory), indent=2))

    elif command == "env":
        env_path = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(detect_database_from_env(env_path), indent=2))

    elif command == "orm":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(detect_orm_framework(directory), indent=2))

    elif command == "migrations":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(find_migrations(directory), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["detect", "config", "env", "orm", "migrations"]
        }, indent=2))


if __name__ == "__main__":
    main()
