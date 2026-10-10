def generate_markdown(project_name: str, tech_data: dict, tree_diagram: str) -> str:
    tech_list = tech_data.get("technologies", [])
    setup_cmds = tech_data.get("setup_commands", [])
    run_cmds = tech_data.get("run_commands", [])

    if tech_list:
        tech_bullets = "\n".join([f"- {tech}" for tech in tech_list])
    else:
        tech_bullets = "- Not identified"

    if setup_cmds:
        commands = "\n".join(setup_cmds)
        install_block = f"```bash\n{commands}\n```"
    else:
        install_block = "No automated package manager configuration detected."

    if run_cmds:
        commands = "\n".join(run_cmds)
        run_block = f"```bash\n{commands}\n```"
    else:
        run_block = "Follow the standard entrypoint execution for the detected language."

    content = [
        f"# {project_name}",
        "",
        "## 📖 Description",
        f"An automated summary and documentation scaffold for the `{project_name}` project.",
        "",
        "## 🛠️ Built With",
        tech_bullets,
        "",
        "## 📂 Project Structure",
        "```text",
        tree_diagram,
        "```",
        "",
        "## 🚀 Getting Started",
        "",
        "### Prerequisites",
        "Ensure you have the required runtime environments installed based on the technologies listed above.",
        "",
        "### Installation",
        install_block,
        "",
        "## 💻 Usage",
        run_block,
        "",
        "## 📝 License",
        "This project is open-source and available under the MIT License.",
        ""
    ]

    return "\n".join(content)