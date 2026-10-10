import os
from flask import Flask, render_template, request, jsonify
from core.scanner import sanitize_file_list, extract_manifest_evidence
from core.tech_detector import detect_technologies
from core.tree_generator import build_tree_structure
from core.agent import run_readme_agent

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scan", methods=["POST"])
def scan_project():
    data = request.get_json()
    if not data or "paths" not in data:
        return jsonify({"error": "No file paths provided"}), 400

    raw_paths = data.get("paths", [])
    files_content = data.get("manifests", {})
    project_name = data.get("projectName", "My Project").strip() or "My Project"

    if not raw_paths:
        return jsonify({"error": "No files found in directory"}), 400


    clean_paths = sanitize_file_list(raw_paths)


    manifest_facts = extract_manifest_evidence(files_content)


    tech_info = detect_technologies(clean_paths, manifest_facts)


    tree_text = build_tree_structure(clean_paths, root_name=project_name)


    try:
        agent_result = run_readme_agent(project_name, tech_info, tree_text)
    except Exception as e:
        return jsonify({"error": f"Agent workflow failed: {str(e)}"}), 500

    return jsonify({
        "projectName": project_name,
        "technologies": tech_info["technologies"],
        "license": tech_info["license"] or "Not detected",
        "tree": tree_text,
        "readme": agent_result["readme"],
        "validation": {
            "was_rectified": agent_result["rectified"],
            "flaws_removed": agent_result["flaws_detected"]
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)