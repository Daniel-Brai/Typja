from io import StringIO

import pytest

from typja.analyzer import ValidationIssue
from typja.config.schema import ErrorsConfig
from typja.reporter import Reporter


class TestReporter:

    def test_create_reporter(self):
        config = ErrorsConfig()
        reporter = Reporter(config)

        assert reporter is not None
        assert reporter.config == config

    def test_create_reporter_with_output(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        assert reporter.output == output

    def test_report_empty_issues(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.report([])

        result = output.getvalue()
        assert isinstance(result, str)

    def test_report_single_issue(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        issue = ValidationIssue(
            severity="error",
            message="Test error",
            filename="test.html",
            line=1,
            col=0,
        )

        reporter.report([issue])

        result = output.getvalue()
        assert "test.html" in result
        assert "Test error" in result

    def test_report_multiple_issues(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        issues = [
            ValidationIssue(
                severity="error",
                message="Error 1",
                filename="test.html",
                line=1,
                col=0,
            ),
            ValidationIssue(
                severity="warning",
                message="Warning 1",
                filename="test.html",
                line=5,
                col=10,
            ),
        ]

        reporter.report(issues)

        result = output.getvalue()
        assert "Error 1" in result
        assert "Warning 1" in result

    def test_report_issues_multiple_files(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        issues = [
            ValidationIssue(
                severity="error",
                message="Error in file1",
                filename="file1.html",
                line=1,
                col=0,
            ),
            ValidationIssue(
                severity="error",
                message="Error in file2",
                filename="file2.html",
                line=1,
                col=0,
            ),
        ]

        reporter.report(issues)

        result = output.getvalue()
        assert "file1.html" in result
        assert "file2.html" in result
        assert "Error in file1" in result
        assert "Error in file2" in result

    def test_report_with_hints(self):
        config = ErrorsConfig(show_hints=True)
        output = StringIO()
        reporter = Reporter(config, output=output)

        issue = ValidationIssue(
            severity="error",
            message="Test error",
            filename="test.html",
            line=1,
            col=0,
            hint="Try this instead",
        )

        reporter.report([issue])

        result = output.getvalue()
        assert "Try this instead" in result

    def test_report_without_hints(self):
        config = ErrorsConfig(show_hints=False)
        output = StringIO()
        reporter = Reporter(config, output=output)

        issue = ValidationIssue(
            severity="error",
            message="Test error",
            filename="test.html",
            line=1,
            col=0,
            hint="This should not appear",
        )

        reporter.report([issue])

        result = output.getvalue()
        assert "This should not appear" not in result

    def test_report_minimal_verbosity(self):
        config = ErrorsConfig(verbosity="minimal")
        output = StringIO()
        reporter = Reporter(config, output=output)

        issue = ValidationIssue(
            severity="error",
            message="Test error",
            filename="test.html",
            line=1,
            col=0,
        )

        reporter.report([issue])

        result = output.getvalue()
        assert "Test error" in result

    def test_report_normal_verbosity(self):
        config = ErrorsConfig(verbosity="normal")
        output = StringIO()
        reporter = Reporter(config, output=output)

        issue = ValidationIssue(
            severity="warning",
            message="Test warning",
            filename="test.html",
            line=5,
            col=10,
        )

        reporter.report([issue])

        result = output.getvalue()
        assert "Test warning" in result
        assert "warning" in result.lower()

    def test_report_verbose_verbosity(self):
        config = ErrorsConfig(verbosity="verbose", show_hints=True)
        output = StringIO()
        reporter = Reporter(config, output=output)

        issue = ValidationIssue(
            severity="error",
            message="Test error",
            filename="test.html",
            line=1,
            col=0,
            hint="Helpful hint",
        )

        reporter.report([issue])

        result = output.getvalue()
        assert "Test error" in result
        assert "Helpful hint" in result

    def test_report_summary_no_issues(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.report_summary(total_files=5, total_issues=0, errors=0, warnings=0)

        result = output.getvalue()
        assert "No issues found" in result or "✓" in result

    def test_report_summary_with_errors(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.report_summary(total_files=5, total_issues=10, errors=10, warnings=0)

        result = output.getvalue()
        assert "10" in result
        assert "5" in result

    def test_report_summary_with_warnings(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.report_summary(total_files=3, total_issues=5, errors=0, warnings=5)

        result = output.getvalue()
        assert "5" in result

    def test_report_summary_mixed(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.report_summary(total_files=10, total_issues=15, errors=8, warnings=7)

        result = output.getvalue()
        assert "8" in result
        assert "7" in result
        assert "10" in result

    def test_success_message(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.success("All tests passed")

        result = output.getvalue()
        assert "All tests passed" in result

    def test_error_message(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.error("Something went wrong")

        result = output.getvalue()
        assert "Something went wrong" in result

    def test_warning_message(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.warning("Be careful")

        result = output.getvalue()
        assert "Be careful" in result

    def test_info_message(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        reporter.info("Just so you know")

        result = output.getvalue()
        assert "Just so you know" in result

    def test_report_sorted_by_line(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        issues = [
            ValidationIssue(
                severity="error",
                message="Error at line 10",
                filename="test.html",
                line=10,
                col=0,
            ),
            ValidationIssue(
                severity="error",
                message="Error at line 5",
                filename="test.html",
                line=5,
                col=0,
            ),
            ValidationIssue(
                severity="error",
                message="Error at line 1",
                filename="test.html",
                line=1,
                col=0,
            ),
        ]

        reporter.report(issues)

        result = output.getvalue()

        pos_line1 = result.find("Error at line 1")
        pos_line5 = result.find("Error at line 5")
        pos_line10 = result.find("Error at line 10")

        assert pos_line1 < pos_line5 < pos_line10

    def test_report_color_always(self):
        config = ErrorsConfig(color="always")
        output = StringIO()
        reporter = Reporter(config, output=output)

        assert reporter.config.color == "always"

    def test_report_color_never(self):
        config = ErrorsConfig(color="never")
        output = StringIO()
        reporter = Reporter(config, output=output)

        assert reporter.config.color == "never"

    def test_report_color_auto(self):
        config = ErrorsConfig(color="auto")
        output = StringIO()
        reporter = Reporter(config, output=output)

        assert reporter.config.color == "auto"

    def test_report_issue_with_column(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        issue = ValidationIssue(
            severity="error",
            message="Error at specific column",
            filename="test.html",
            line=5,
            col=15,
        )

        reporter.report([issue])

        result = output.getvalue()
        assert "5" in result
        assert "15" in result

    def test_report_issue_severity_styles(self):
        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        issues = [
            ValidationIssue(
                severity="error",
                message="Error message",
                filename="test.html",
                line=1,
                col=0,
            ),
            ValidationIssue(
                severity="warning",
                message="Warning message",
                filename="test.html",
                line=2,
                col=0,
            ),
        ]

        reporter.report(issues)

        result = output.getvalue()
        assert "Error message" in result
        assert "Warning message" in result

    def test_report_files_sorted_alphabetically(self):

        config = ErrorsConfig()
        output = StringIO()
        reporter = Reporter(config, output=output)

        issues = [
            ValidationIssue(
                severity="error",
                message="Error in zebra",
                filename="zebra.html",
                line=1,
                col=0,
            ),
            ValidationIssue(
                severity="error",
                message="Error in alpha",
                filename="alpha.html",
                line=1,
                col=0,
            ),
        ]

        reporter.report(issues)

        result = output.getvalue()

        pos_alpha = result.find("alpha.html")
        pos_zebra = result.find("zebra.html")

        assert pos_alpha < pos_zebra
