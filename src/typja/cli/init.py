from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from typja.config import DEFAULT_TYPJA_TOML, load_config
from typja.exceptions import TypjaConfigError

console = Console()


def init(
    root: str = typer.Option(
        ".",
        "--root",
        "-r",
        help="Root directory for the project (where typja.toml will be created).",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing typja.toml file."),
) -> None:
    """
    Initialize a new typja.toml configuration file

    This command creates a new typja.toml file in the specified directory with sensible defaults. You can then customize it for your project.

    Examples:

        # Create typja.toml in current directory
        typja init

        # Create typja.toml in a specific directory
        typja init --root ./my-project

        # Overwrite existing typja.toml
        typja init --force
    """

    root_path = Path(root).resolve()

    target_path = root_path / "typja.toml"

    current_config_path = Path("typja.toml")
    old_config_to_delete = None

    if current_config_path.exists() and current_config_path.resolve() != target_path.resolve():
        try:
            existing_config = load_config(current_config_path)
            existing_root = Path(existing_config.project.root).resolve()
            if existing_root == root_path:
                old_config_to_delete = current_config_path
        except TypjaConfigError:
            pass

    if target_path.exists() and not force:
        overwrite = Confirm.ask(f"[yellow]{target_path} already exists. Overwrite?[/yellow]")
        if not overwrite:
            console.print("[blue]Initialization cancelled.[/blue]")
            raise typer.Exit(0)

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)

        config_content = DEFAULT_TYPJA_TOML
        if root != ".":
            config_content = config_content.replace('root = "."', f'root = "{root}"')

        target_path.write_text(config_content, encoding="utf-8")
        console.print(f"[green]✓[/green] Created {target_path}")

        if old_config_to_delete and old_config_to_delete.exists():
            old_config_to_delete.unlink()
            console.print(f"[yellow]✓[/yellow] Removed old config from {old_config_to_delete}")

    except Exception as e:
        console.print(f"[red]Error creating configuration:[/red] {str(e)}")
        raise typer.Exit(1) from e
