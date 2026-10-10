import os
import re
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3.6-flash"
]

UNSUPPORTED_BUZZWORDS = [
    "production-ready", "production ready", "military-grade", "ultra-fast",
    "real-time", "bulletproof", "unmatched performance", "next-generation"
]

def clean_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(markdown|md)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()

def build_offline_grounded_readme(project_name: str, tech_data: dict, tree_diagram: str) -> str:
    """Deterministic fallback generator when cloud endpoints are completely unavailable (503)."""
    technologies = tech_data.get("technologies", [])
    dependencies = tech_data.get("dependencies", [])
    setup_cmds = tech_data.get("setup_commands", [])
    run_cmds = tech_data.get("run_commands", [])
    license_detected = tech_data.get("license")

    tech_bullets = "\n".join([f"- {t}" for t in technologies]) if technologies else "- None identified"
    deps_bullets = "\n".join([f"- `{d}`" for d in dependencies[:15]]) if dependencies else "- No manifest dependencies extracted"

    install_block = f"```bash\n{chr(10).join(setup_cmds)}\n```" if setup_cmds else "No automated installation script detected."
    run_block = f"```bash\n{chr(10).join(run_cmds)}\n```" if run_cmds else "Execute standard runtime entry point for this language."

    sections = [
        f"# {project_name}",
        "",
        "## Description",
        f"Technical documentation for `{project_name}`, compiled from codebase manifests and directory structure.",
        "",
        "## Tech Stack",
        tech_bullets,
        "",
        "## Dependencies",
        deps_bullets,
        "",
        "## Project Structure",
        "```text",
        tree_diagram,
        "```",
        "",
        "## Getting Started",
        "",
        "### Prerequisites",
        "Ensure runtime environments for the detected languages are installed.",
        "",
        "### Installation",
        install_block,
        "",
        "## Usage",
        run_block,
        ""
    ]

    if license_detected:
        sections.extend([
            "## License",
            f"This project is governed under the {license_detected}."
        ])
    else:
        sections.extend([
            "## License",
            "No license file detected."
        ])

    return "\n".join(sections)

def generate_with_resilience(prompt: str) -> str:
    """Tries candidates with exponential backoff on 503 errors."""
    if not client:
        return ""

    for model_name in MODEL_FALLBACKS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text or ""
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                else:
                    break

    return ""

def audit_readme_facts(readme_text: str, facts: dict) -> list[str]:
    flaws = []
    text_lower = readme_text.lower()

    if not facts.get("license"):
        for lic in ["mit license", "apache license", "gpl", "bsd license"]:
            if lic in text_lower:
                flaws.append("License hallucination: Project has no LICENSE file, but an open-source license was claimed.")
                break

    for word in UNSUPPORTED_BUZZWORDS:
        if word in text_lower:
            flaws.append(f"Unsupported marketing claim detected: '{word}'.")

    detected_tech = [t.lower() for t in facts.get("technologies", [])]
    detected_deps = [d.lower() for d in facts.get("dependencies", [])]
    known_entities = set(detected_tech + detected_deps)

    for common_unsupported in ["mongodb", "postgresql", "redis", "kubernetes", "aws", "react", "vue"]:
        if common_unsupported in text_lower and common_unsupported not in known_entities:
            flaws.append(f"Unsubstantiated technology reference: '{common_unsupported}'.")

    for ph in ["[todo]", "<insert", "[replace", "your_repo_url"]:
        if ph in text_lower:
            flaws.append(f"Unfilled placeholder token: '{ph}'.")

    return flaws


def run_readme_agent(project_name: str, tech_data: dict, tree_diagram: str) -> dict:
    technologies = tech_data.get("technologies", [])
    dependencies = tech_data.get("dependencies", [])
    setup_cmds = tech_data.get("setup_commands", [])
    run_cmds = tech_data.get("run_commands", [])
    license_detected = tech_data.get("license")

    tech_str = ", ".join(technologies) if technologies else "None identified"
    deps_str = ", ".join(dependencies[:15]) if dependencies else "None extracted"
    setup_str = ", ".join(setup_cmds) if setup_cmds else "No package manager config detected"
    run_str = ", ".join(run_cmds) if run_cmds else "Standard runtime entry point not confirmed"
    license_str = license_detected if license_detected else "No license file detected"

    prompt_lines = [
        "You are a technical documentation agent committed to 100% factual accuracy.",
        "Generate a professional README.md for the following project based ONLY on the verified facts below.",
        "",
        "VERIFIED PROJECT FACTS:",
        f"- Project Name: {project_name}",
        f"- Detected Technologies: {tech_str}",
        f"- Verified Dependencies: {deps_str}",
        f"- Verified Setup Commands: {setup_str}",
        f"- Verified Run Commands: {run_str}",
        f"- License Status: {license_str}",
        "",
        "PROJECT STRUCTURE:",
        "```text",
        tree_diagram,
        "```",
        "",
        "STRICT RULES TO PREVENT HALLUCINATION:",
        "1. NEVER claim a license (such as MIT) unless explicitly verified above. If license status is 'No license file detected', omit the section or state 'No license detected'.",
        "2. Do NOT assume or invent databases, deployment platforms, APIs, performance characteristics, or repository URLs not present in the verified facts.",
        "3. If an installation or run command is not confirmed, state 'Not detected' or omit the command block.",
        "4. Do NOT use buzzwords (e.g., 'production-ready', 'secure', 'real-time').",
        "5. Output ONLY valid Markdown text."
    ]
    base_prompt = "\n".join(prompt_lines)

    raw_draft = generate_with_resilience(base_prompt)

    used_offline_fallback = False
    if not raw_draft:
        raw_draft = build_offline_grounded_readme(project_name, tech_data, tree_diagram)
        used_offline_fallback = True

    draft = clean_markdown_fences(raw_draft)

    flaws = audit_readme_facts(draft, tech_data)

    was_rectified = False
    if flaws and not used_offline_fallback:
        flaws_formatted = "\n".join([f"- {f}" for f in flaws])
        rectification_lines = [
            "The previous README draft contained unsupported claims or hallucinations:",
            flaws_formatted,
            "",
            "Here are the ONLY verified facts allowed:",
            f"- Project Name: {project_name}",
            f"- Detected Technologies: {tech_str}",
            f"- Verified Dependencies: {deps_str}",
            f"- Verified Setup Commands: {setup_str}",
            f"- Verified Run Commands: {run_str}",
            f"- License Status: {license_str}",
            "",
            "Rewrite the README.md to be completely grounded. Strip out every flagged assumption, unverified license claim, or invented dependency. Output ONLY valid Markdown."
        ]
        rectification_prompt = "\n".join(rectification_lines)

        raw_rectified = generate_with_resilience(rectification_prompt)
        if raw_rectified:
            draft = clean_markdown_fences(raw_rectified)
            was_rectified = True

    return {
        "readme": draft,
        "rectified": was_rectified,
        "offline_fallback": used_offline_fallback,
        "flaws_detected": flaws,
        "verified_facts": {
            "technologies": technologies,
            "license": license_detected or "Not detected",
            "dependencies_count": len(dependencies)
        }
    }