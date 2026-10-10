import os
import json
import re

IGNORE_DIRS = {
    "node_modules", ".git", ".github", "__pycache__", "venv", ".venv",
    "env", ".env", "dist", "build", ".next", ".nuxt", "target", "vendor",
    ".idea", ".vscode", "coverage", ".pytest_cache"
}

SENSITIVE_FILES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_dsa", "credentials.json", "secrets.json",
    "service-account.json"
}

CONFIG_MANIFEST_WHITELIST = {
    "requirements.txt", "package.json", "pyproject.toml", "pom.xml",
    "build.gradle", "cargo.toml", "composer.json", "dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "license", "license.txt",
    "license.md", "readme.md"
}

def sanitize_file_list(raw_paths: list[str]) -> list[str]:
    """Filters out vendor folders, caches, and sensitive files."""
    clean = []
    for path in raw_paths:
        parts = path.replace("\\", "/").strip("/").split("/")
        if any(part in IGNORE_DIRS for part in parts[:-1]):
            continue
        filename = parts[-1].lower()
        if filename in SENSITIVE_FILES or filename.startswith(".env") or filename.endswith((".pem", ".key")):
            continue
        clean.append("/".join(parts))
    return clean

def extract_manifest_evidence(files_with_content: dict[str, str]) -> dict:
    """Safely parses whitelisted configuration manifests for ground truth facts."""
    evidence = {
        "dependencies": [],
        "dev_dependencies": [],
        "scripts": {},
        "license_name": None,
        "entrypoints": [],
        "has_docker": False
    }

    for path, content in files_with_content.items():
        filename = os.path.basename(path).lower()
        if filename not in CONFIG_MANIFEST_WHITELIST:
            continue

        if filename == "package.json":
            try:
                data = json.loads(content)
                evidence["dependencies"].extend(list(data.get("dependencies", {}).keys())[:25])
                evidence["dev_dependencies"].extend(list(data.get("devDependencies", {}).keys())[:15])
                evidence["scripts"].update(data.get("scripts", {}))
                if data.get("license") and isinstance(data.get("license"), str):
                    evidence["license_name"] = data["license"]
                if data.get("main"):
                    evidence["entrypoints"].append(data["main"])
            except Exception:
                pass

        elif filename == "requirements.txt":
            deps = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = re.split(r"[=<>]", line)[0].strip()
                    if pkg:
                        deps.append(pkg)
            evidence["dependencies"].extend(deps[:30])

        elif filename == "pyproject.toml":
            deps = re.findall(r'["\']([a-zA-Z0-9_\-\.]+)(?:[>=<~!].*)?["\']', content)
            if deps:
                evidence["dependencies"].extend(deps[:20])

        elif filename in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
            evidence["has_docker"] = True

        elif "license" in filename:
            first_chunk = "\n".join(content.splitlines()[:10]).upper()
            if "MIT" in first_chunk:
                evidence["license_name"] = "MIT License"
            elif "APACHE" in first_chunk:
                evidence["license_name"] = "Apache 2.0 License"
            elif "GNU" in first_chunk or "GPL" in first_chunk:
                evidence["license_name"] = "GPL License"
            elif "BSD" in first_chunk:
                evidence["license_name"] = "BSD License"
            else:
                evidence["license_name"] = "Custom / Unspecified License"

    return evidence