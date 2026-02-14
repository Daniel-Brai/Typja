import time
from pathlib import Path

import typer
from rich.console import Console

from typja.config.loader import ConfigLoader
from typja.exceptions import TypjaConfigError
from typja.helpers import find_templates

console = Console()


def watch(
    root: str = typer.Option(
        ".",
        "--root",
        "-r",
        help="Root directory of the project. Defaults to current directory.",
    ),
) -> None:
    """
    Watch templates for changes and auto checks them for type errors and linting issues.

    This command watches your template files and automatically runs type checking whenever files are modified.

    Examples:

        # Watch from current directory (looks for typja.toml here)
        typja watch

        # Watch from specific project root
        typja watch --root ./my-project/
    """

    try:
        root_path = Path(root).resolve()

        config_file = root_path / "typja.toml"

        if not config_file.exists():
            try:
                config_file = ConfigLoader.find_config(root_path)
                console.print(f"[blue]Found config:[/blue] {config_file}\n")
            except TypjaConfigError as e:
                console.print(
                    f"[red]Error:[/red] No typja.toml found in {root_path} or parent directories.\n"
                    "[blue]Hint:[/blue] Run 'typja init' to create a configuration file."
                )
                raise typer.Exit(1) from e

        config = ConfigLoader.load(config_file)

        watch_paths = config.get_template_dirs()

        console.print("[blue]Starting watch mode...[/blue]")
        console.print(f"[blue]Watching:[/blue] {', '.join(str(p) for p in watch_paths)}\n")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        file_mtimes: dict[Path, float] = {}

        def get_all_templates() -> list[Path]:
            templates = []
            for watch_path in watch_paths:
                if not watch_path.exists():
                    continue
                templates.extend(
                    find_templates(watch_path, config.environment.include_patterns, config.environment.exclude_patterns)
                )
            return templates

        from typja.cli.check import check as run_check

        console.print("[blue]Running initial check...[/blue]\n")
        try:
            run_check(root=str(root_path), fix=False, strict=False)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Initial check failed: {str(e)}\n")

        for template in get_all_templates():
            if template.exists():
                file_mtimes[template] = template.stat().st_mtime

        console.print("\n[green]✓ Watching for changes...[/green]\n")

        while True:
            time.sleep(2)  # Check every 2 seconds

            changed_files = []
            current_templates = get_all_templates()

            for template in current_templates:
                if not template.exists():
                    if template in file_mtimes:
                        del file_mtimes[template]
                    continue

                current_mtime = template.stat().st_mtime

                if template not in file_mtimes:
                    changed_files.append(template)
                    file_mtimes[template] = current_mtime

                elif current_mtime > file_mtimes[template]:
                    changed_files.append(template)
                    file_mtimes[template] = current_mtime

            if changed_files:
                console.print(f"[yellow]Detected changes in {len(changed_files)} file(s)[/yellow]")
                for file in changed_files:
                    console.print(f"  • {file.relative_to(root_path)}")
                console.print()

                try:
                    run_check(root=str(root_path), fix=False, strict=False)
                except Exception as e:
                    console.print(f"[red]Check failed:[/red] {str(e)}")

                console.print("\n[green]✓ Watching for changes...[/green]\n")

    except KeyboardInterrupt as e:
        console.print("\n[blue]Stopped watching.[/blue]")
        raise typer.Exit(0) from e

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1) from e
