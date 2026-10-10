def detect_technologies(paths: list[str], manifest_evidence: dict = None) -> dict:
    """Detects technologies and verified commands without ungrounded assumptions."""
    evidence = manifest_evidence or {}
    techs = set()
    setup_cmds = []
    run_cmds = []

    filenames = [p.split("/")[-1] for p in paths]
    extensions = {p.split(".")[-1].lower() for p in paths if "." in p}

    if "py" in extensions or "requirements.txt" in filenames or "pyproject.toml" in filenames:
        techs.add("Python")
        if "requirements.txt" in filenames:
            setup_cmds.append("pip install -r requirements.txt")
        elif "pyproject.toml" in filenames:
            setup_cmds.append("pip install .")

        for candidate in ["app.py", "main.py", "manage.py", "run.py", "wsgi.py"]:
            if candidate in filenames:
                run_cmds.append(f"python {candidate}")
                break

    if "package.json" in filenames or "js" in extensions or "jsx" in extensions or "ts" in extensions:
        techs.add("JavaScript")
        if "ts" in extensions or "tsx" in extensions:
            techs.add("TypeScript")

        if "package-lock.json" in filenames:
            setup_cmds.append("npm ci")
        elif "package.json" in filenames:
            setup_cmds.append("npm install")

        scripts = evidence.get("scripts", {})
        if "start" in scripts:
            run_cmds.append("npm start")
        elif "dev" in scripts:
            run_cmds.append("npm run dev")
        elif evidence.get("entrypoints"):
            run_cmds.append(f"node {evidence['entrypoints'][0]}")

    if "html" in extensions:
        techs.add("HTML5")
    if "css" in extensions:
        techs.add("CSS3")

    if evidence.get("has_docker") or "Dockerfile" in filenames:
        techs.add("Docker")

    return {
        "technologies": sorted(list(techs)),
        "setup_commands": setup_cmds,
        "run_commands": run_cmds,
        "dependencies": sorted(list(set(evidence.get("dependencies", [])))),
        "license": evidence.get("license_name")
    }