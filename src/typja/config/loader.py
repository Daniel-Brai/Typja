import sys
from pathlib import Path
from typing import Any

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from typja.config.schema import (
    EnvironmentConfig,
    ErrorsConfig,
    FormattingConfig,
    LintingConfig,
    ProjectConfig,
    TypjaConfig,
)
from typja.exceptions import TypjaConfigError


class ConfigLoader:
    """
    Loader for typja configuration from typja.toml
    """

    @staticmethod
    def load(config_path: Path | str | None = None) -> TypjaConfig:
        """
        Load configuration from typja.toml

        Args:
            config_path (Path | str | None): Path to typja.toml. If None, searches current directory.

        Returns:
            TypjaConfig: TypjaConfig instance
        """

        if config_path is None:
            config_path = ConfigLoader.find_config()
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise TypjaConfigError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise TypjaConfigError(f"Failed to parse {config_path}: {str(e)}") from e

        return ConfigLoader.parse_config(data)

    @staticmethod
    def find_config(start_dir: Path | None = None) -> Path:
        """
        Find typja.toml by searching up the directory tree

        Args:
            start_dir (Path | None): Directory to start search from. Defaults to cwd.

        Returns:
            Path: The path to typja.toml

        Raises:
            TypjaConfigError: If typja.toml is not found
        """

        if start_dir is None:
            start_dir = Path.cwd()
        else:
            start_dir = Path(start_dir)

        current = start_dir.resolve()

        while True:
            config_path = current / "typja.toml"
            if config_path.exists():
                return config_path

            parent = current.parent
            if parent == current:
                break
            current = parent

        raise TypjaConfigError(
            f"typja.toml not found in {start_dir} or any parent directory.\n"
            "Hint: Run 'typja init' to create a configuration file."
        )

    @staticmethod
    def parse_config(data: dict[str, Any]) -> TypjaConfig:

        project_data = data.get("project", {})
        project = ProjectConfig(
            root=project_data.get("root", "."),
            paths=project_data.get("paths", ["./types"]),
            fail_on_warning=project_data.get("fail_on_warning", False),
        )

        env_data = data.get("environment", {})
        environment = EnvironmentConfig(
            jinja_env=env_data.get("jinja_env"),
            template_dirs=env_data.get("template_dirs", ["./templates"]),
            include_patterns=env_data.get("include_patterns", ["*.html", "*.jinja", "*.jinja2", "*.j2"]),
            exclude_patterns=env_data.get(
                "exclude_patterns", ["**/node_modules/**", "**/.git/**", "**/dist/**", "**/__pycache__/**"]
            ),
        )

        lint_data = data.get("linting", {})
        linting = LintingConfig(
            strict=lint_data.get("strict", False),
            prefer_pep604_unions=lint_data.get("prefer_pep604_unions", True),
            union_style=lint_data.get("union_style", "warning"),
            fix_union_syntax=lint_data.get("fix_union_syntax", True),
            warn_unused_imports=lint_data.get("warn_unused_imports", True),
            warn_undefined_variables=lint_data.get("warn_undefined_variables", True),
            warn_type_mismatches=lint_data.get("warn_type_mismatches", True),
            validate_imports=lint_data.get("validate_imports", True),
            validate_filters=lint_data.get("validate_filters", True),
            validate_macros=lint_data.get("validate_macros", True),
            validate_variables=lint_data.get("validate_variables", True),
            check_missing_annotations=lint_data.get("check_missing_annotations", False),
        )

        format_data = data.get("formatting", {})
        formatting = FormattingConfig(
            enabled=format_data.get("enabled", True),
            sort_imports=format_data.get("sort_imports", True),
        )

        errors_data = data.get("errors", {})
        errors = ErrorsConfig(
            verbosity=errors_data.get("verbosity", "normal"),
            show_snippets=errors_data.get("show_snippets", True),
            show_hints=errors_data.get("show_hints", True),
            color=errors_data.get("color", "auto"),
        )

        return TypjaConfig(
            project=project,
            environment=environment,
            linting=linting,
            formatting=formatting,
            errors=errors,
        )


def load_config(config_path: Path | str | None = None) -> TypjaConfig:
    """
    Load typja configuration from typja.toml

    Args:
        config_path (Path | str | None): Path to typja.toml. If None, searches current directory.

    Returns:
        TypjaConfig: The loaded configuration
    """

    return ConfigLoader.load(config_path)
