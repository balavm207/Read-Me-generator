# Automatic AI README Generator

A developer utility that inspects local codebase manifests and directory structure to construct factual, verified technical documentation without generative hallucinations.

---

## Overview

Automated documentation tools often invent licenses, hallucinate non-existent database integrations, or fill sections with generic marketing filler. 

This tool implements an empirical 7-stage agent pipeline:
1. **Scan**: Traverses the project tree while stripping vendor dependencies (`node_modules`, `venv`) and sensitive secret stores (`.env`).
2. **Analyze**: Detects runtimes and entry-point patterns (`app.py`, `main.py`).
3. **Filter**: Isolates configuration manifests (`requirements.txt`, `pyproject.toml`, `Dockerfile`, `LICENSE`).
4. **Generate**: Directs Google Gemini to draft documentation constrained to verified facts.
5. **Validate**: Runs deterministic audits against the draft to detect ungrounded claims or hallucinated licenses.
6. **Correct**: Re-prompts the model with strict violation logs to scrub errors before rendering.
7. **Finalize**: Emits standard Markdown ready for export.

---

## Tech Stack

- **Backend**: Python 3.11+, Flask
- **LLM Engine**: Google Gemini API (`gemini-3.6-flash` via `google-genai` SDK)
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Developer Workbench UI)

---

## Project Structure
```text
Agent AI/
├── core/
│   ├── __init__.py
│   ├── agent.py
│   ├── readme_generator.py
│   ├── scanner.py
│   ├── tech_detector.py
│   └── tree_generator.py
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
├── .gitignore
├── app.py
├── README.md
└── requirements.txt