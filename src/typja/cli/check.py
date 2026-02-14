import importlib
from pathlib import Path

import typer
from jinja2 import Environment
from rich.console import Console

from typja.analyzer import TemplateAnalyzer, ValidationIssue
from typja.config.loader import ConfigLoader
from typja.exceptions import TypjaConfigError
from typja.helpers import find_templates
from typja.linter import Linter
from typja.registry import TypeRegistry
from typja.reporter import Reporter
from typja.resolver import TypeResolver

console = Console()


def check(
    root: str = typer.Option(
        ".",
        "--root",
        "-r",
        help="Root directory of the project.",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix issues where possible.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Enable strict mode (treat warnings as errors).",
    ),
) -> None:
    """
    Check templates for type errors and linting issues.

    This command analyzes your Jinja2 templates and validates:
    - Type annotations in typja comments
    - Variable usage matches declared types
    - Attribute access on typed variables
    - Import statements reference valid types if any

    Examples:

        # Check templates in current project
        typja check

        # Check with auto-fix enabled
        typja check --fix

        # Check in strict mode
        typja check --strict
    """

    try:
        root_path = Path(root).resolve()

        config_file = root_path / "typja.toml"

        if not config_file.exists():
            try:
                config_file = ConfigLoader.find_config(root_path)
            except TypjaConfigError as e:
                console.print(
                    f"[red]Error:[/red] No typja.toml found in {root_path} or parent directories.\n"
                    "[blue]Hint:[/blue] Run 'typja init' to create a configuration file or specify the project root with --root."
                )
                raise typer.Exit(1) from e

        config = ConfigLoader.load(config_file)

        if strict:
            config.project.fail_on_warning = True

        registry = TypeRegistry()
        resolver = TypeResolver(
            config.root_path,
            exclude_patterns=config.environment.exclude_patterns,
        )

        jinja_env: Environment | None = None

        if config.environment.jinja_env:
            if ":" not in config.environment.jinja_env:
                console.print("[red]Error:[/red] Invalid jinja_env format in typja.toml. Use 'module.path:attribute'.")
                raise typer.Exit(1)

            module_path, attr_name = config.environment.jinja_env.split(":", 1)
            module_path = module_path.strip()
            attr_name = attr_name.strip()

            if not module_path or not attr_name:
                console.print("[red]Error:[/red] Invalid jinja_env format in typja.toml. Use 'module.path:attribute'.")
                raise typer.Exit(1)

            try:
                module = importlib.import_module(module_path)
            except Exception as e:
                console.print(
                    f"[red]Error:[/red] Failed to import jinja environment in '{module_path}' specified in typja.toml: {str(e)}"
                )
                raise typer.Exit(1) from e

            if not hasattr(module, attr_name):
                console.print(
                    f"[red]Error:[/red] For jinja environment specified in typja.toml, '{module_path}' has no attribute '{attr_name}'."
                )
                raise typer.Exit(1)

            candidate = getattr(module, attr_name)
            if not isinstance(candidate, Environment):
                console.print("[red]Error:[/red] jinja_env must be a Jinja2 Environment instance.")
                raise typer.Exit(1)

            jinja_env = candidate

        type_paths = config.get_type_paths()
        if type_paths:
            console.print(f"[blue]Resolving types from {len(type_paths)} path(s)...[/blue]")
            resolver.resolve_paths(type_paths)
            resolver.populate_registry(registry)
            console.print(f"[green]✓[/green] Found {len(resolver.resolved_types)} type(s)\n")

        templates = []
        for template_dir in config.get_template_dirs():
            if template_dir.exists():
                found = find_templates(
                    template_dir,
                    config.environment.include_patterns,
                    config.environment.exclude_patterns,
                )
                templates.extend(found)

        if not templates:
            console.print("[yellow]No templates found to check.[/yellow]")
            raise typer.Exit(0)

        console.print(f"[blue]Checking {len(templates)} template(s)...[/blue]\n")

        all_issues: list[ValidationIssue] = []
        linter = Linter()

        for template_path in templates:
            try:
                content = template_path.read_text(encoding="utf-8")

                analyzer = TemplateAnalyzer(
                    registry=registry,
                    resolver=resolver,
                    jinja_env=jinja_env,
                )

                issues = analyzer.analyze_template(content, str(template_path))

                lint_config = {
                    "prefer_pep604_unions": config.linting.prefer_pep604_unions,
                    "union_style": config.linting.union_style,
                    "warn_unused_imports": config.linting.warn_unused_imports,
                    "fix_union_syntax": config.linting.fix_union_syntax,
                }
                lint_issues = linter.lint_template(content, str(template_path), lint_config)

                issues.extend(lint_issues)

                if fix and (issues or lint_issues):
                    fixed_content = linter.auto_fix(content, issues + lint_issues)
                    if fixed_content != content:
                        template_path.write_text(fixed_content, encoding="utf-8")
                        console.print(f"[green]✓[/green] Fixed {template_path.relative_to(config.root_path)}")

                all_issues.extend(issues)

            except Exception as e:
                console.print(f"[red]Error analyzing {template_path}:[/red] {str(e)}")

        reporter = Reporter(config.errors)
        reporter.report(all_issues)

        errors = sum(1 for issue in all_issues if issue.severity == "error")
        warnings = sum(1 for issue in all_issues if issue.severity == "warning")

        reporter.report_summary(
            total_files=len(templates),
            total_issues=len(all_issues),
            errors=errors,
            warnings=warnings,
        )

        if errors > 0:
            raise typer.Exit(1)

        if warnings > 0 and config.project.fail_on_warning:
            raise typer.Exit(1)

        if len(all_issues) == 0:
            console.print("[green]✓ No issues found[/green]")

        raise typer.Exit(0)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error checking templates:[/red] {str(e)}")
        raise typer.Exit(1) from e
