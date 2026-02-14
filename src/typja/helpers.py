from pathlib import Path


def find_templates(root: Path, include_patterns: list[str], exclude_patterns: list[str]) -> list[Path]:
    """
    Find template files matching patterns

    Args:
        root (Path): Root directory to search
        include_patterns (list[str]): Patterns to include (e.g., ['*.html', '*.jinja'])
        exclude_patterns (list[str]): Patterns to exclude (e.g., ['**/node_modules/**'])

    Returns:
        list[Path]: List of template file paths
    """

    if not root.exists():
        return []

    templates: list[Path] = []

    for pattern in include_patterns:
        for file_path in root.rglob(pattern.lstrip("./")):
            if file_path.is_file():
                relative = file_path.relative_to(root)
                should_exclude = False

                for exc in exclude_patterns:
                    if exc.startswith("**/") and exc.endswith("/**"):
                        dir_name = exc[3:-3]
                        if dir_name in relative.parts:
                            should_exclude = True
                            break

                    elif relative.match(exc):
                        should_exclude = True
                        break

                if not should_exclude:
                    templates.append(file_path)

    return sorted(set(templates))
