#!/usr/bin/env python3
"""
project-tool.py

Provides project structure detection and analysis utilities for Claude Code agents.
Returns structured JSON output for integration with setup, backend, and frontend agents.
Supports framework detection, directory structure analysis, and technology stack identification.
"""
import json
import sys
import os
from pathlib import Path
from typing import Optional, Any


def detect_language(directory: Optional[str] = None) -> dict:
    """
    Detect the primary programming language of a project.

    Args:
        directory: Directory to analyse (uses current directory if None)

    Returns:
        Dictionary containing detected language information
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    # Language indicators with their package/config files
    language_indicators = {
        "php": ["composer.json", "composer.lock", "artisan", "index.php"],
        "python": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "manage.py"],
        "javascript": ["package.json"],
        "typescript": ["tsconfig.json"],
        "ruby": ["Gemfile", "Gemfile.lock", "Rakefile"],
        "go": ["go.mod", "go.sum"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "csharp": ["*.csproj", "*.sln"],
        "swift": ["Package.swift", "*.xcodeproj"],
    }

    detected = {}
    primary = None

    for lang, indicators in language_indicators.items():
        for indicator in indicators:
            if "*" in indicator:
                matches = list(search_dir.glob(indicator))
                if matches:
                    detected[lang] = detected.get(lang, 0) + len(matches)
            else:
                if (search_dir / indicator).exists():
                    detected[lang] = detected.get(lang, 0) + 1

    # Determine primary language
    if detected:
        # TypeScript projects also have package.json, prioritise TS
        if "typescript" in detected and "javascript" in detected:
            detected["typescript"] += 1
        primary = max(detected, key=detected.get)

    # Get language version if possible
    version = None
    if primary == "php" and (search_dir / "composer.json").exists():
        try:
            import json as json_mod
            with open(search_dir / "composer.json") as f:
                data = json_mod.load(f)
                version = data.get("require", {}).get("php")
        except Exception:
            pass
    elif primary == "python":
        for file in [".python-version", "runtime.txt"]:
            path = search_dir / file
            if path.exists():
                try:
                    version = path.read_text().strip()
                except Exception:
                    pass
                break
    elif primary in ["javascript", "typescript"] and (search_dir / ".nvmrc").exists():
        try:
            version = (search_dir / ".nvmrc").read_text().strip()
        except Exception:
            pass

    return {
        "primary": primary,
        "detected": detected,
        "version": version,
        "directory": str(search_dir),
    }


def detect_framework(directory: Optional[str] = None) -> dict:
    """
    Detect the web framework used in the project.

    Args:
        directory: Directory to analyse (uses current directory if None)

    Returns:
        Dictionary containing detected framework information
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    # Framework detection rules
    frameworks = {
        # PHP frameworks
        "laravel": {
            "indicators": ["artisan", "app/Http/Kernel.php", "bootstrap/app.php"],
            "package_file": "composer.json",
            "package_indicator": "laravel/framework",
        },
        "symfony": {
            "indicators": ["symfony.lock", "config/bundles.php"],
            "package_file": "composer.json",
            "package_indicator": "symfony/framework-bundle",
        },
        "wordpress": {
            "indicators": ["wp-config.php", "wp-content", "wp-admin"],
            "package_file": None,
        },
        "drupal": {
            "indicators": ["core/lib/Drupal.php", "sites/default"],
            "package_file": "composer.json",
            "package_indicator": "drupal/core",
        },
        # Python frameworks
        "django": {
            "indicators": ["manage.py", "settings.py"],
            "package_file": "requirements.txt",
            "package_indicator": "django",
        },
        "flask": {
            "indicators": ["app.py"],
            "package_file": "requirements.txt",
            "package_indicator": "flask",
        },
        "fastapi": {
            "indicators": ["main.py"],
            "package_file": "requirements.txt",
            "package_indicator": "fastapi",
        },
        # JavaScript/TypeScript frameworks
        "nextjs": {
            "indicators": ["next.config.js", "next.config.mjs", "next.config.ts", "pages", "app"],
            "package_file": "package.json",
            "package_indicator": "next",
        },
        "nuxt": {
            "indicators": ["nuxt.config.js", "nuxt.config.ts"],
            "package_file": "package.json",
            "package_indicator": "nuxt",
        },
        "remix": {
            "indicators": ["remix.config.js"],
            "package_file": "package.json",
            "package_indicator": "@remix-run/react",
        },
        "express": {
            "indicators": [],
            "package_file": "package.json",
            "package_indicator": "express",
        },
        "nestjs": {
            "indicators": ["nest-cli.json"],
            "package_file": "package.json",
            "package_indicator": "@nestjs/core",
        },
        # React ecosystem
        "react": {
            "indicators": [],
            "package_file": "package.json",
            "package_indicator": "react",
        },
        "react-native": {
            "indicators": ["app.json", "metro.config.js", "ios", "android"],
            "package_file": "package.json",
            "package_indicator": "react-native",
        },
        "expo": {
            "indicators": ["app.json", "expo.json"],
            "package_file": "package.json",
            "package_indicator": "expo",
        },
        "create-react-app": {
            "indicators": [],
            "package_file": "package.json",
            "package_indicator": "react-scripts",
        },
        "vite-react": {
            "indicators": ["vite.config.js", "vite.config.ts"],
            "package_file": "package.json",
            "package_indicator": "@vitejs/plugin-react",
        },
        # Vue ecosystem
        "vue": {
            "indicators": ["vue.config.js"],
            "package_file": "package.json",
            "package_indicator": "vue",
        },
        "angular": {
            "indicators": ["angular.json"],
            "package_file": "package.json",
            "package_indicator": "@angular/core",
        },
        "svelte": {
            "indicators": ["svelte.config.js"],
            "package_file": "package.json",
            "package_indicator": "svelte",
        },
        "sveltekit": {
            "indicators": ["svelte.config.js"],
            "package_file": "package.json",
            "package_indicator": "@sveltejs/kit",
        },
        # Ruby frameworks
        "rails": {
            "indicators": ["config/application.rb", "bin/rails"],
            "package_file": "Gemfile",
            "package_indicator": "rails",
        },
        # Go frameworks
        "gin": {
            "indicators": [],
            "package_file": "go.mod",
            "package_indicator": "github.com/gin-gonic/gin",
        },
        "fiber": {
            "indicators": [],
            "package_file": "go.mod",
            "package_indicator": "github.com/gofiber/fiber",
        },
        # Mobile frameworks
        "flutter": {
            "indicators": ["pubspec.yaml", "lib/main.dart", "ios", "android"],
            "package_file": "pubspec.yaml",
            "package_indicator": "flutter",
        },
        "ionic": {
            "indicators": ["ionic.config.json"],
            "package_file": "package.json",
            "package_indicator": "@ionic/core",
        },
        # Static site generators
        "gatsby": {
            "indicators": ["gatsby-config.js", "gatsby-config.ts"],
            "package_file": "package.json",
            "package_indicator": "gatsby",
        },
        "astro": {
            "indicators": ["astro.config.mjs", "astro.config.js"],
            "package_file": "package.json",
            "package_indicator": "astro",
        },
        "eleventy": {
            "indicators": [".eleventy.js", "eleventy.config.js"],
            "package_file": "package.json",
            "package_indicator": "@11ty/eleventy",
        },
    }

    detected = []

    for framework, rules in frameworks.items():
        confidence = 0

        # Check file indicators
        for indicator in rules.get("indicators", []):
            path = search_dir / indicator
            if path.exists():
                confidence += 2

        # Check package file for dependency
        pkg_file = rules.get("package_file")
        pkg_indicator = rules.get("package_indicator")

        if pkg_file and pkg_indicator:
            pkg_path = search_dir / pkg_file
            if pkg_path.exists():
                try:
                    content = pkg_path.read_text().lower()
                    if pkg_indicator.lower() in content:
                        confidence += 3
                except Exception:
                    pass

        if confidence > 0:
            detected.append({
                "name": framework,
                "confidence": confidence,
            })

    # Sort by confidence
    detected.sort(key=lambda x: x["confidence"], reverse=True)

    primary = detected[0]["name"] if detected else None
    all_detected = [d["name"] for d in detected]

    # Determine if React-based
    is_react_based = any(f in all_detected for f in ["react", "react-native", "expo", "nextjs", "gatsby", "create-react-app", "vite-react"])

    return {
        "primary": primary,
        "detected": all_detected,
        "details": detected,
        "is_react_based": is_react_based,
        "is_mobile": any(f in all_detected for f in ["react-native", "expo", "flutter", "ionic"]),
        "directory": str(search_dir),
    }


def detect_container_type(directory: Optional[str] = None) -> dict:
    """
    Detect the container/deployment setup.

    Args:
        directory: Directory to analyse (uses current directory if None)

    Returns:
        Dictionary containing container configuration
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    containers = {
        "ddev": {
            "indicators": [".ddev/config.yaml", ".ddev/config.yml"],
            "type": "ddev",
        },
        "docker_compose": {
            "indicators": ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"],
            "type": "docker-compose",
        },
        "docker": {
            "indicators": ["Dockerfile", "Dockerfile.dev", "Dockerfile.prod"],
            "type": "docker",
        },
        "kubernetes": {
            "indicators": ["k8s", "kubernetes", "*.yaml"],
            "type": "kubernetes",
        },
        "vercel": {
            "indicators": ["vercel.json"],
            "type": "vercel",
        },
        "netlify": {
            "indicators": ["netlify.toml"],
            "type": "netlify",
        },
    }

    detected = []

    for name, config in containers.items():
        for indicator in config["indicators"]:
            if "*" in indicator:
                matches = list(search_dir.glob(indicator))
                if matches:
                    detected.append(config["type"])
                    break
            else:
                if (search_dir / indicator).exists():
                    detected.append(config["type"])
                    break

    # Remove duplicates while preserving order
    detected = list(dict.fromkeys(detected))

    return {
        "primary": detected[0] if detected else None,
        "detected": detected,
        "has_docker": "docker" in detected or "docker-compose" in detected,
        "has_ddev": "ddev" in detected,
        "directory": str(search_dir),
    }


def analyse_structure(directory: Optional[str] = None) -> dict:
    """
    Analyse the project directory structure.

    Args:
        directory: Directory to analyse (uses current directory if None)

    Returns:
        Dictionary containing structure analysis
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    # Common directories to look for
    common_dirs = [
        "src", "app", "lib", "public", "static", "assets",
        "components", "pages", "views", "templates", "screens",
        "tests", "test", "spec", "__tests__", "e2e",
        "config", "configs", "settings",
        "docs", "documentation",
        "scripts", "bin", "tools",
        "api", "routes", "controllers",
        "models", "entities", "schemas",
        "services", "utils", "helpers", "hooks",
        ".github", ".gitlab", ".circleci",
        "node_modules", "vendor", "venv", ".venv",
        "ios", "android",  # React Native / mobile
    ]

    found_dirs = []
    for dir_name in common_dirs:
        path = search_dir / dir_name
        if path.exists() and path.is_dir():
            # Count items in directory
            try:
                item_count = len(list(path.iterdir()))
            except PermissionError:
                item_count = -1

            found_dirs.append({
                "name": dir_name,
                "path": str(path),
                "items": item_count,
            })

    # Find root-level config files
    config_files = []
    config_patterns = [
        "*.json", "*.yaml", "*.yml", "*.toml", "*.ini",
        "*.config.js", "*.config.ts", "*.config.mjs",
        ".*rc", ".env*", "metro.config.*",
        "Makefile", "Dockerfile*", "docker-compose*",
    ]

    for pattern in config_patterns:
        for file_path in search_dir.glob(pattern):
            if file_path.is_file() and not file_path.name.startswith("package-lock"):
                config_files.append(file_path.name)

    return {
        "directories": found_dirs,
        "directory_count": len(found_dirs),
        "config_files": sorted(set(config_files)),
        "config_count": len(set(config_files)),
        "root": str(search_dir),
    }


def get_project_info(directory: Optional[str] = None) -> dict:
    """
    Get comprehensive project information.

    Args:
        directory: Directory to analyse (uses current directory if None)

    Returns:
        Dictionary containing complete project analysis
    """
    search_dir = Path(directory) if directory else Path.cwd()

    language = detect_language(str(search_dir))
    framework = detect_framework(str(search_dir))
    container = detect_container_type(str(search_dir))
    structure = analyse_structure(str(search_dir))

    # Get project name from various sources
    project_name = search_dir.name

    # Try to get from package files
    for pkg_file in ["package.json", "composer.json", "Cargo.toml", "pyproject.toml", "app.json"]:
        pkg_path = search_dir / pkg_file
        if pkg_path.exists():
            try:
                content = pkg_path.read_text()
                if pkg_file.endswith(".json"):
                    import json as json_mod
                    data = json_mod.loads(content)
                    if "name" in data:
                        project_name = data["name"]
                        break
                    elif "expo" in data and "name" in data.get("expo", {}):
                        project_name = data["expo"]["name"]
                        break
                elif pkg_file == "Cargo.toml" or pkg_file == "pyproject.toml":
                    import re
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        project_name = match.group(1)
                        break
            except Exception:
                pass

    return {
        "name": project_name,
        "path": str(search_dir),
        "language": language.get("primary"),
        "language_version": language.get("version"),
        "framework": framework.get("primary"),
        "all_frameworks": framework.get("detected", []),
        "is_react_based": framework.get("is_react_based", False),
        "is_mobile": framework.get("is_mobile", False),
        "container": container.get("primary"),
        "has_docker": container.get("has_docker", False),
        "has_ddev": container.get("has_ddev", False),
        "directory_count": structure.get("directory_count", 0),
        "config_files": structure.get("config_files", []),
    }


def main():
    """Main entry point for the Project tool."""
    if len(sys.argv) < 2:
        # Default: comprehensive project info
        print(json.dumps(get_project_info(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "info":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_project_info(directory), indent=2))

    elif command == "language":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(detect_language(directory), indent=2))

    elif command == "framework":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(detect_framework(directory), indent=2))

    elif command == "container":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(detect_container_type(directory), indent=2))

    elif command == "structure":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(analyse_structure(directory), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["info", "language", "framework", "container", "structure"]
        }, indent=2))


if __name__ == "__main__":
    main()
