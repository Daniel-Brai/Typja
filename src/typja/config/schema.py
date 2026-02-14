from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class ProjectConfig:
    """
    Schema for project configuration section, defining root directory and paths to analyze

    Attributes:
        root (str): Root directory for the project (default: ".")
        paths (list[str]): List of file paths or glob patterns to analyze (default: [])
        fail_on_warning (bool): Whether to treat warnings as errors (default: False)
    """

    root: str = "."
    paths: list[str] = field(default_factory=list)
    fail_on_warning: bool = False


@dataclass
class EnvironmentConfig:
    """
    Schema for jinja environment configuration section

    Attributes:
        jinja_env (str | None): Optional path to a custom Jinja environment module
        template_dirs (list[str]): List of directories to search for templates (default: ["./templates"])
        include_patterns (list[str]): List of glob patterns to include as templates (default: ["*.html", "*.jinja", "*.jinja2", "*.j2"])
        exclude_patterns (list[str]): List of glob patterns to exclude from template analysis (default: ["**/node_modules
    """

    jinja_env: str | None = None
    template_dirs: list[str] = field(default_factory=lambda: ["./templates"])
    include_patterns: list[str] = field(default_factory=lambda: ["*.html", "*.jinja", "*.jinja2", "*.j2"])
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/.git/**",
            "**/dist/**",
            "**/build/**",
            "wheels/**",
            ".venv/**",
            "**/__pycache__/**",
        ]
    )


@dataclass
class LintingConfig:
    """
    Schema for linting configuration section

    Attributes:
        strict (bool): Whether to enable strict linting rules (default: False)
        prefer_pep604_unions (bool): Whether to prefer PEP 604 union syntax (default: True)
        union_style (Literal["error", "warning", "ignore"]): How to handle non-PEP 604 unions (default: "warning")
        fix_union_syntax (bool): Whether to automatically fix union syntax issues (default: True
        warn_unused_imports (bool): Whether to warn about unused imports (default: True)
        warn_undefined_variables (bool): Whether to warn about undefined variables (default: True)
        warn_type_mismatches (bool): Whether to warn about type mismatches (default:
        True)
        validate_imports (bool): Whether to validate that imports can be resolved (default: True)
        validate_filters (bool): Whether to validate that filters can be resolved (default: True)
        validate_macros (bool): Whether to validate that macros can be resolved (default: True)
        validate_variables (bool): Whether to validate that variables can be resolved (default: True)
        check_missing_annotations (bool): Whether to check for missing type annotations (default: False)
    """

    strict: bool = False
    prefer_pep604_unions: bool = True
    union_style: Literal["error", "warning", "ignore"] = "warning"
    fix_union_syntax: bool = True
    warn_unused_imports: bool = True
    warn_undefined_variables: bool = True
    warn_type_mismatches: bool = True
    validate_imports: bool = True
    validate_filters: bool = True
    validate_macros: bool = True
    validate_variables: bool = True
    check_missing_annotations: bool = False


@dataclass
class FormattingConfig:
    """
    Schema for formatting configuration section

    Attributes:
        enabled (bool): Whether to enable automatic formatting (default: True)
        sort_imports (bool): Whether to automatically sort imports (default: True)
    """

    enabled: bool = True
    sort_imports: bool = True


@dataclass
class ErrorsConfig:
    """
    Schema for error reporting configuration section

    Attributes:
        verbosity (Literal["minimal", "normal", "verbose"]): Level of detail in error reports (default: "normal")
        show_snippets (bool): Whether to include code snippets in error reports (default: True)
        show_hints (bool): Whether to include hints for fixing issues in error reports (default: True)
        color (Literal["auto", "always", "never"]): When to use colored output (default: "auto")
    """

    verbosity: Literal["minimal", "normal", "verbose"] = "normal"
    show_snippets: bool = True
    show_hints: bool = True
    color: Literal["auto", "always", "never"] = "auto"


@dataclass
class TypjaConfig:
    """
    Main configuration schema for typja.toml, encompassing all sections

    Attributes:
        project (ProjectConfig): Project configuration
        environment (EnvironmentConfig): Jinja environment configuration
        linting (LintingConfig): Linting configuration
        formatting (FormattingConfig): Formatting configuration
        errors (ErrorsConfig): Error reporting configuration
    """

    project: ProjectConfig = field(default_factory=ProjectConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    linting: LintingConfig = field(default_factory=LintingConfig)
    formatting: FormattingConfig = field(default_factory=FormattingConfig)
    errors: ErrorsConfig = field(default_factory=ErrorsConfig)

    @property
    def root_path(self) -> Path:
        return Path(self.project.root)

    def get_template_dirs(self) -> list[Path]:
        return [self.root_path / path for path in self.environment.template_dirs]

    def get_type_paths(self) -> list[Path]:
        import glob

        paths: list[Path] = []
        for pattern in self.project.paths:
            full_pattern = str(self.root_path / pattern)

            if any(c in pattern for c in ["*", "?", "[", "]"]):
                matched = glob.glob(full_pattern, recursive=True)
                paths.extend(Path(p) for p in matched)
            else:
                path = self.root_path / pattern
                if path.exists():
                    paths.append(path)

        return paths
