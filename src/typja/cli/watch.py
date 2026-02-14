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
    Watch type paths and templates directories for changes and auto checks them for type errors and linting issues.

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

        template_dirs = config.get_template_dirs()
        type_paths = config.get_type_paths()

        watch_paths: list[Path] = []
        watch_paths.extend(template_dirs)
        watch_paths.extend(type_paths)
        watch_paths.append(config_file)

        console.print("[blue]Starting watch mode...[/blue]")

        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        file_mtimes: dict[Path, float] = {}

        def get_all_templates() -> list[Path]:
            templates = []
            for watch_path in template_dirs:
                if not watch_path.exists():
                    continue
                templates.extend(
                    find_templates(
                        watch_path,
                        config.environment.include_patterns,
                        config.environment.exclude_patterns,
                    )
                )
            return templates

        def get_all_type_files() -> list[Path]:
            type_files: list[Path] = []
            for type_path in type_paths:
                if not type_path.exists():
                    continue
                if type_path.is_file() and type_path.suffix == ".py":
                    type_files.append(type_path)
                elif type_path.is_dir():
                    for py_file in type_path.rglob("*.py"):
                        if "__pycache__" not in py_file.parts and not any(
                            py_file.match(pattern) for pattern in config.environment.exclude_patterns
                        ):
                            type_files.append(py_file)
            return type_files

        def get_all_watched_files() -> list[Path]:
            files = get_all_templates()
            files.extend(get_all_type_files())
            if config_file.exists():
                files.append(config_file)
            return files

        from typja.cli.check import check as run_check

        console.print("[blue]Running initial check...[/blue]\n")
        try:
            run_check(root=str(root_path), fix=False, strict=False)
        except typer.Exit as e:
            if e.exit_code != 0:
                console.print(f"\n[yellow]Warning:[/yellow] Initial check failed with exit code: {e.exit_code}\n")
        except Exception as e:
            console.print(f"\n[yellow]Warning:[/yellow] Initial check failed: {str(e)}\n")

        for file_path in get_all_watched_files():
            if file_path.exists():
                file_mtimes[file_path] = file_path.stat().st_mtime

        console.print("\n[green]✓ Watching for changes...[/green]\n")

        while True:
            time.sleep(1)

            changed_files = []
            current_files = get_all_watched_files()

            for file_path in current_files:
                if not file_path.exists():
                    if file_path in file_mtimes:
                        del file_mtimes[file_path]
                    continue

                current_mtime = file_path.stat().st_mtime

                if file_path not in file_mtimes:
                    changed_files.append(file_path)
                    file_mtimes[file_path] = current_mtime

                elif current_mtime > file_mtimes[file_path]:
                    changed_files.append(file_path)
                    file_mtimes[file_path] = current_mtime

            if changed_files:
                console.print(f"[yellow]Detected changes in {len(changed_files)} file(s)[/yellow]")
                for file in changed_files:
                    try:
                        console.print(f"  • {file.relative_to(root_path)}")
                    except ValueError:
                        console.print(f"  • {file}")

                console.print()

                try:
                    run_check(root=str(root_path), fix=False, strict=False)
                except typer.Exit as e:
                    if e.exit_code != 0:
                        console.print(f"[red]Check failed with exit code:[/red] {e.exit_code}")
                except Exception as e:
                    console.print(f"[red]Check failed:[/red] {str(e)}")

                console.print("\n[green]✓ Watching for changes...[/green]\n")

    except KeyboardInterrupt as e:
        console.print("\n[blue]Stopped watching.[/blue]")
        raise typer.Exit(0) from e

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1) from e
