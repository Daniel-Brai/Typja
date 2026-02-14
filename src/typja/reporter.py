import sys
from pathlib import Path
from typing import TextIO

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

from typja.analyzer import ValidationIssue
from typja.config import ErrorsConfig

TYPJA_THEME = Theme(
    {
        "error": "bold red",
        "warning": "bold yellow",
        "info": "bold blue",
        "success": "bold green",
        "hint": "dim cyan",
        "path": "bold magenta",
        "line_number": "dim",
    }
)


class Reporter:
    """
    Reporter for validation issues, warnings, and errors
    """

    def __init__(self, config: ErrorsConfig, output: TextIO = sys.stdout):
        self.config = config
        self.output = output

        force_terminal = None
        if config.color == "always":
            force_terminal = True
        elif config.color == "never":
            force_terminal = False

        self.console = Console(
            file=output,
            theme=TYPJA_THEME,
            force_terminal=force_terminal,
        )

    def report(self, issues: list[ValidationIssue]) -> None:
        """
        Report all validation issues

        Args:
            issues (list[ValidationIssue]): List of validation issues to report
        """

        if not issues:
            return

        issues_by_file: dict[str, list[ValidationIssue]] = {}
        for issue in issues:
            if issue.filename not in issues_by_file:
                issues_by_file[issue.filename] = []
            issues_by_file[issue.filename].append(issue)

        for filename in sorted(issues_by_file.keys()):
            file_issues = sorted(issues_by_file[filename], key=lambda x: x.line)
            self._report_file_issues(filename, file_issues)

    def _report_file_issues(self, filename: str, issues: list[ValidationIssue]) -> None:
        """
        Report issues for a file

        Args:
            filename (str): Path to the file
            issues (list[ValidationIssue]): Issues in this file
        """

        self.console.print()
        self.console.print(f"[path]{filename}[/path]")

        for issue in issues:
            self._report_issue(issue)

    def _report_issue(self, issue: ValidationIssue) -> None:
        """
        Report a single validation issue

        Args:
            issue (ValidationIssue): Validation issue to report
        """

        if issue.severity == "error":
            severity_style = "error"
            icon = "✗"
        elif issue.severity == "warning":
            severity_style = "warning"
            icon = "⚠"
        else:
            severity_style = "info"
            icon = "ℹ"

        location = f"  {issue.line}"
        if issue.col:
            location += f":{issue.col}"

        if self.config.verbosity == "minimal":
            self.console.print(
                f"[line_number]{location}[/line_number] "
                f"[{severity_style}]{icon}[/{severity_style}] "
                f"{issue.message}"
            )

        elif self.config.verbosity == "normal":
            self.console.print(
                f"[line_number]{location}[/line_number] "
                f"[{severity_style}]{icon} {issue.severity}:[/{severity_style}] "
                f"{issue.message}"
            )

            if self.config.show_hints and issue.hint:
                self.console.print(f"    [hint]💡 {issue.hint}[/hint]")

        elif self.config.verbosity == "verbose":
            self.console.print(
                f"[line_number]{location}[/line_number] "
                f"[{severity_style}]{icon} {issue.severity}:[/{severity_style}] "
                f"{issue.message}"
            )

            if self.config.show_snippets:
                self._show_code_snippet(issue)

            if self.config.show_hints and issue.hint:
                self.console.print(f"    [hint]💡 Hint: {issue.hint}[/hint]")

            self.console.print()

    def _show_code_snippet(self, issue: ValidationIssue) -> None:
        """
        Show code snippet around the issue location

        Args:
            issue (ValidationIssue): Validation issue
        """

        try:
            file_path = Path(issue.filename)
            if not file_path.exists():
                return

            content = file_path.read_text()
            lines = content.splitlines()

            start_line = max(0, issue.line - 4)
            end_line = min(len(lines), issue.line + 3)

            snippet_lines = lines[start_line:end_line]
            snippet = "\n".join(snippet_lines)

            syntax = Syntax(
                snippet,
                "jinja2",
                theme="monokai",
                line_numbers=True,
                start_line=start_line + 1,
                highlight_lines={issue.line},
            )

            self.console.print(
                Panel(
                    syntax,
                    border_style="dim",
                    padding=(0, 1),
                )
            )

        except Exception:
            return

    def report_summary(self, total_files: int, total_issues: int, errors: int, warnings: int) -> None:
        """
        Report summary statistics.

        Args:
            total_files (int): Total number of files checked
            total_issues (int): Total number of issues found
            errors (int): Number of errors
            warnings (int): Number of warnings
        """

        self.console.print()

        if total_issues == 0:
            self.console.print("[success]✓ No issues found![/success]")
            return

        table = Table(show_header=False, box=None, padding=(0, 2))

        table.add_row("[dim]Files checked:[/dim]", str(total_files))

        if errors > 0:
            table.add_row("[error]Errors:[/error]", f"[error]{errors}[/error]")

        if warnings > 0:
            table.add_row("[warning]Warnings:[/warning]", f"[warning]{warnings}[/warning]")

        self.console.print(table)

    def success(self, message: str) -> None:
        """
        Print a success message

        Args:
            message (str): Success message
        """

        self.console.print(f"[success]✓ {message}[/success]")

    def error(self, message: str) -> None:
        """
        Print an error message

        Args:
            message (str): Error message
        """

        self.console.print(f"[error]✗ {message}[/error]")

    def warning(self, message: str) -> None:
        """
        Print a warning message

        Args:
            message (str): Warning message
        """

        self.console.print(f"[warning]⚠ {message}[/warning]")

    def info(self, message: str) -> None:
        """
        Print an info message

        Args:
            message (str): Info message
        """

        self.console.print(f"[info]ℹ {message}[/info]")
