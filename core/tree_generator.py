def build_tree_structure(file_paths: list[str], root_name: str = "project-root") -> str:
    """Builds a formatted Unicode tree diagram from a sanitized list of relative paths."""
    tree = {}

    for path in file_paths:
        parts = path.strip("/").split("/")
        current = tree
        for part in parts:
            current = current.setdefault(part, {})

    def render_subtree(subtree: dict, prefix: str = "") -> list[str]:
        lines = []
        entries = sorted(subtree.keys())
        for idx, entry in enumerate(entries):
            is_last = (idx == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry}")

            if subtree[entry]:
                child_prefix = prefix + ("    " if is_last else "│   ")
                lines.extend(render_subtree(subtree[entry], child_prefix))
        return lines

    result_lines = [f"{root_name}/"] + render_subtree(tree)
    return "\n".join(result_lines)