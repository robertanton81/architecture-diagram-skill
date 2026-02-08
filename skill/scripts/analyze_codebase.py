#!/usr/bin/env python3
"""Analyze a codebase to extract architectural components for C4 diagramming.

Scans a project directory and outputs a JSON structure with:
- Top-level modules/packages (potential C4 systems or containers)
- Entry points and services (APIs, servers, workers)
- Dependencies (from package.json, requirements.txt, go.mod, etc.)
- Connections between modules (imports/requires across boundaries)

Usage:
    python analyze_codebase.py <project_path> [--depth 2] [--output json|summary]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "target", "bin", "obj",
    ".idea", ".vscode", ".claude", "coverage", ".tox", "vendor",
}

IGNORE_FILES = {".DS_Store", "Thumbs.db", ".gitignore", ".env"}


def detect_project_type(path: Path) -> list[str]:
    """Detect project type(s) from manifest files."""
    types = []
    markers = {
        "package.json": "node",
        "requirements.txt": "python",
        "pyproject.toml": "python",
        "setup.py": "python",
        "go.mod": "go",
        "Cargo.toml": "rust",
        "pom.xml": "java",
        "build.gradle": "java",
        "Gemfile": "ruby",
        "composer.json": "php",
        "*.csproj": "dotnet",
        "*.sln": "dotnet",
    }
    for marker, ptype in markers.items():
        if "*" in marker:
            if list(path.glob(marker)):
                types.append(ptype)
        elif (path / marker).exists():
            types.append(ptype)
    return list(set(types)) or ["unknown"]


def parse_package_json(path: Path) -> dict:
    """Extract info from package.json."""
    try:
        with open(path / "package.json") as f:
            pkg = json.load(f)
        return {
            "name": pkg.get("name", ""),
            "description": pkg.get("description", ""),
            "dependencies": list(pkg.get("dependencies", {}).keys()),
            "devDependencies": list(pkg.get("devDependencies", {}).keys()),
            "scripts": list(pkg.get("scripts", {}).keys()),
            "main": pkg.get("main", ""),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def parse_requirements(path: Path) -> list[str]:
    """Extract dependencies from requirements.txt."""
    req_file = path / "requirements.txt"
    if not req_file.exists():
        return []
    deps = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-"):
            name = re.split(r"[>=<!\[]", line)[0].strip()
            if name:
                deps.append(name)
    return deps


def parse_pyproject(path: Path) -> dict:
    """Extract basic info from pyproject.toml."""
    toml_file = path / "pyproject.toml"
    if not toml_file.exists():
        return {}
    content = toml_file.read_text()
    info = {}
    name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
    if name_match:
        info["name"] = name_match.group(1)
    desc_match = re.search(r'description\s*=\s*"([^"]+)"', content)
    if desc_match:
        info["description"] = desc_match.group(1)
    return info


def find_entry_points(path: Path, project_types: list[str]) -> list[dict]:
    """Find likely service entry points."""
    entries = []
    patterns = {
        "node": [
            ("server.ts", "API server"),
            ("server.js", "API server"),
            ("index.ts", "Entry point"),
            ("index.js", "Entry point"),
            ("app.ts", "Application"),
            ("app.js", "Application"),
            ("main.ts", "Main entry"),
            ("main.js", "Main entry"),
            ("worker.ts", "Background worker"),
            ("worker.js", "Background worker"),
        ],
        "python": [
            ("main.py", "Main entry"),
            ("app.py", "Application"),
            ("manage.py", "Django management"),
            ("wsgi.py", "WSGI server"),
            ("asgi.py", "ASGI server"),
            ("celery.py", "Task worker"),
        ],
        "go": [("main.go", "Main entry")],
        "dotnet": [("Program.cs", "Main entry"), ("Startup.cs", "App startup")],
    }

    for ptype in project_types:
        for filename, role in patterns.get(ptype, []):
            for found in path.rglob(filename):
                rel = found.relative_to(path)
                if not any(p in IGNORE_DIRS for p in rel.parts):
                    entries.append({
                        "file": str(rel),
                        "role": role,
                        "directory": str(rel.parent) if str(rel.parent) != "." else "root",
                    })
    return entries


def find_top_level_modules(path: Path, max_depth: int = 2) -> list[dict]:
    """Identify top-level modules/packages as potential C4 containers."""
    modules = []
    src_dirs = ["src", "lib", "pkg", "packages", "apps", "services", "internal", "cmd"]

    # Check for monorepo-style structure
    for src_dir in src_dirs:
        src_path = path / src_dir
        if src_path.is_dir():
            for child in sorted(src_path.iterdir()):
                if child.is_dir() and child.name not in IGNORE_DIRS:
                    mod = analyze_module(child, path)
                    if mod:
                        modules.append(mod)

    # If no src dirs found, use top-level directories
    if not modules:
        for child in sorted(path.iterdir()):
            if child.is_dir() and child.name not in IGNORE_DIRS and not child.name.startswith("."):
                mod = analyze_module(child, path)
                if mod:
                    modules.append(mod)

    return modules


def analyze_module(mod_path: Path, root: Path) -> dict | None:
    """Analyze a single module directory."""
    files = list(mod_path.rglob("*"))
    code_files = [f for f in files if f.is_file() and f.suffix in {
        ".ts", ".js", ".py", ".go", ".rs", ".java", ".cs", ".rb", ".php",
        ".tsx", ".jsx", ".vue", ".svelte",
    } and not any(p in IGNORE_DIRS for p in f.relative_to(root).parts)]

    if not code_files:
        return None

    extensions = defaultdict(int)
    for f in code_files:
        extensions[f.suffix] += 1

    # Detect type hints
    component_type = "module"
    rel_path = str(mod_path.relative_to(root))

    type_hints = {
        "api": "API service",
        "server": "server",
        "web": "web application",
        "frontend": "frontend",
        "backend": "backend service",
        "worker": "background worker",
        "queue": "message queue consumer",
        "db": "database layer",
        "database": "database layer",
        "gateway": "API gateway",
        "auth": "authentication service",
        "common": "shared library",
        "shared": "shared library",
        "lib": "library",
        "utils": "utilities",
        "config": "configuration",
        "models": "data models",
        "services": "service layer",
        "controllers": "controller layer",
        "routes": "routing layer",
    }

    name = mod_path.name.lower()
    for hint, ctype in type_hints.items():
        if hint in name:
            component_type = ctype
            break

    has_package_json = (mod_path / "package.json").exists()
    has_dockerfile = (mod_path / "Dockerfile").exists()

    return {
        "name": mod_path.name,
        "path": rel_path,
        "type": component_type,
        "file_count": len(code_files),
        "languages": dict(sorted(extensions.items(), key=lambda x: -x[1])),
        "has_own_manifest": has_package_json or (mod_path / "pyproject.toml").exists(),
        "has_dockerfile": has_dockerfile,
        "is_deployable": has_dockerfile or has_package_json,
    }


def find_cross_module_imports(path: Path, modules: list[dict]) -> list[dict]:
    """Find import relationships between top-level modules."""
    connections = []
    module_names = {m["name"] for m in modules}

    for mod in modules:
        mod_path = path / mod["path"]
        for code_file in mod_path.rglob("*"):
            if not code_file.is_file():
                continue
            if code_file.suffix not in {".ts", ".js", ".py", ".go", ".tsx", ".jsx"}:
                continue
            if any(p in IGNORE_DIRS for p in code_file.relative_to(path).parts):
                continue

            try:
                content = code_file.read_text(errors="ignore")
            except Exception:
                continue

            for other_mod in module_names:
                if other_mod == mod["name"]:
                    continue
                # Check for imports referencing another module
                patterns = [
                    rf'from\s+["\'].*{re.escape(other_mod)}',
                    rf'import\s+.*["\'].*{re.escape(other_mod)}',
                    rf'require\(["\'].*{re.escape(other_mod)}',
                    rf'from\s+{re.escape(other_mod)}\s+import',
                ]
                for pat in patterns:
                    if re.search(pat, content):
                        conn = {
                            "from": mod["name"],
                            "to": other_mod,
                            "file": str(code_file.relative_to(path)),
                        }
                        if conn not in connections:
                            connections.append(conn)
                        break

    return connections


def detect_technologies(path: Path, pkg_info: dict) -> list[dict]:
    """Detect key technologies used in the project."""
    techs = []
    indicators = {
        "react": {"type": "framework-library", "c4_type": "app"},
        "next": {"type": "framework-library", "c4_type": "app"},
        "vue": {"type": "framework-library", "c4_type": "app"},
        "angular": {"type": "framework-library", "c4_type": "app"},
        "express": {"type": "framework-library", "c4_type": "app"},
        "fastapi": {"type": "framework-library", "c4_type": "app"},
        "django": {"type": "framework-library", "c4_type": "app"},
        "flask": {"type": "framework-library", "c4_type": "app"},
        "postgresql": {"type": "data-storage", "c4_type": "store"},
        "pg": {"type": "data-storage", "c4_type": "store"},
        "mongodb": {"type": "data-storage", "c4_type": "store"},
        "mongoose": {"type": "data-storage", "c4_type": "store"},
        "redis": {"type": "data-storage", "c4_type": "store"},
        "mysql": {"type": "data-storage", "c4_type": "store"},
        "prisma": {"type": "data-storage", "c4_type": "store"},
        "typeorm": {"type": "data-storage", "c4_type": "store"},
        "sequelize": {"type": "data-storage", "c4_type": "store"},
        "rabbitmq": {"type": "message-broker", "c4_type": "app"},
        "kafka": {"type": "message-broker", "c4_type": "app"},
        "docker": {"type": "deployment", "c4_type": "system"},
        "kubernetes": {"type": "deployment", "c4_type": "system"},
    }

    all_deps = set(pkg_info.get("dependencies", []) + pkg_info.get("devDependencies", []))

    for dep in all_deps:
        dep_lower = dep.lower().replace("@", "").replace("/", "-")
        for tech, info in indicators.items():
            if tech in dep_lower:
                techs.append({"name": dep, "technology_type": info["type"], "suggested_c4_type": info["c4_type"]})

    # Check for Dockerfiles
    if list(path.rglob("Dockerfile")) or list(path.rglob("docker-compose*.yml")):
        techs.append({"name": "Docker", "technology_type": "deployment", "suggested_c4_type": "system"})

    return techs


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_codebase.py <project_path> [--output json|summary]", file=sys.stderr)
        sys.exit(1)

    project_path = Path(sys.argv[1]).resolve()
    output_mode = "json"

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_mode = sys.argv[idx + 1]

    if not project_path.is_dir():
        print(f"Error: {project_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    project_types = detect_project_type(project_path)
    pkg_info = parse_package_json(project_path)
    py_deps = parse_requirements(project_path)
    pyproject_info = parse_pyproject(project_path)
    modules = find_top_level_modules(project_path)
    entry_points = find_entry_points(project_path, project_types)
    connections = find_cross_module_imports(project_path, modules)
    technologies = detect_technologies(project_path, pkg_info)

    result = {
        "project": {
            "path": str(project_path),
            "name": pkg_info.get("name") or pyproject_info.get("name") or project_path.name,
            "description": pkg_info.get("description") or pyproject_info.get("description", ""),
            "types": project_types,
        },
        "modules": modules,
        "entry_points": entry_points,
        "connections": connections,
        "technologies": technologies,
        "dependencies": {
            "node": pkg_info.get("dependencies", []),
            "python": py_deps,
        },
    }

    if output_mode == "summary":
        print(f"Project: {result['project']['name']}")
        print(f"Type(s): {', '.join(project_types)}")
        print(f"\nModules ({len(modules)}):")
        for m in modules:
            print(f"  - {m['name']} ({m['type']}, {m['file_count']} files)")
        print(f"\nEntry points ({len(entry_points)}):")
        for e in entry_points:
            print(f"  - {e['file']} ({e['role']})")
        print(f"\nConnections ({len(connections)}):")
        for c in connections:
            print(f"  - {c['from']} -> {c['to']}")
        print(f"\nTechnologies ({len(technologies)}):")
        for t in technologies:
            print(f"  - {t['name']} ({t['technology_type']})")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
