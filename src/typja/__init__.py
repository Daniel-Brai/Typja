"""
typja - Type checking for Jinja2 templates
"""

from importlib.metadata import version

from typja.constants import PACKAGE_NAME

__version__ = version(PACKAGE_NAME)


def main() -> None:
    from typja.cli.app import app

    app()


__all__ = ["main"]
