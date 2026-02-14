import typer
from rich.console import Console

from typja.cli import check, init, watch

app = typer.Typer(
    name="typja",
    help="Type checking for Jinja2 templates",
    add_completion=False,
)

console = Console()


app.command()(init.init)
app.command()(watch.watch)
app.command()(check.check)


@app.callback()
def callback():
    """
    typja - Type checking for Jinja2 templates
    """
    pass


def version_callback(value: bool):
    if value:
        from typja import __version__

        console.print(f"typja version {__version__}")

        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    pass


if __name__ == "__main__":
    app()
