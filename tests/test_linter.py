from typja.linter import Linter
from typja.parser import CommentParser


class TestLinter:

    def test_create_linter(self):
        linter = Linter()
        assert linter is not None

    def test_lint_simple_template(self):
        linter = Linter()
        template = """
{# typja:var name: str #}
<p>{{ name }}</p>
"""

        config = {
            "prefer_pep604_unions": True,
            "union_style": "warning",
            "warn_unused_imports": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_lint_old_style_union(self):

        linter = Linter()
        template = """
{# typja:from typing import Union #}
{# typja:var value: Union[str, int] #}
<p>{{ value }}</p>
"""

        config = {
            "prefer_pep604_unions": True,
            "union_style": "warning",
        }

        issues = linter.lint_template(template, "test.html", config)

        union_issues = [i for i in issues if "union" in i.message.lower()]
        assert len(union_issues) > 0

    def test_lint_pep604_union_preferred(self):
        linter = Linter()
        template = """
{# typja:var value: str | int #}
<p>{{ value }}</p>
"""

        config = {
            "prefer_pep604_unions": True,
            "union_style": "warning",
        }

        issues = linter.lint_template(template, "test.html", config)

        union_issues = [
            i
            for i in issues
            if "union" in i.message.lower() and "style" in i.message.lower()
        ]
        assert len(union_issues) == 0

    def test_lint_unused_import(self):
        linter = Linter()
        template = """
{# typja:from typing import List, Dict #}
{# typja:var items: List[str] #}
<p>{{ items }}</p>
"""

        config = {
            "warn_unused_imports": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        unused_issues = [
            i
            for i in issues
            if "unused" in i.message.lower() and "dict" in i.message.lower()
        ]
        assert len(unused_issues) > 0

    def test_lint_all_imports_used(self):
        linter = Linter()
        template = """
{# typja:from typing import List #}
{# typja:var items: List[str] #}
<p>{{ items }}</p>
"""

        config = {
            "warn_unused_imports": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        unused_issues = [i for i in issues if "unused" in i.message.lower()]
        assert len(unused_issues) == 0

    def test_lint_duplicate_declarations(self):
        linter = Linter()
        template = """
{# typja:var name: str #}
{# typja:var name: int #}
<p>{{ name }}</p>
"""

        config = {
            "warn_duplicate_declarations": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        dup_issues = [i for i in issues if "duplicate" in i.message.lower()]
        assert len(dup_issues) > 0

    def test_lint_sorted_imports(self):
        linter = Linter()
        template = """
{# typja:from typing import Dict #}
{# typja:from typing import List #}
{# typja:var items: List[str] #}
{# typja:var mapping: Dict[str, int] #}
"""

        config = {
            "require_sorted_imports": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_lint_redundant_none(self):

        linter = Linter()
        template = """
{# typja:from typing import Optional #}
{# typja:var value: Optional[str | None] #}
<p>{{ value }}</p>
"""

        config = {
            "warn_redundant_none": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        assert isinstance(issues, list)
        assert len(issues) > 0

    def test_lint_union_style_error(self):

        linter = Linter()
        template = """
{# typja:from typing import Union #}
{# typja:var value: Union[str, int] #}
<p>{{ value }}</p>
"""

        config = {
            "prefer_pep604_unions": True,
            "union_style": "error",
        }

        issues = linter.lint_template(template, "test.html", config)

        assert isinstance(issues, list)
        assert len(issues) > 0

    def test_lint_union_style_ignore(self):

        linter = Linter()
        template = """
{# typja:from typing import Union #}
{# typja:var value: Union[str, int] #}
<p>{{ value }}</p>
"""

        config = {
            "prefer_pep604_unions": False,
            "union_style": "ignore",
        }

        issues = linter.lint_template(template, "test.html", config)

        union_issues = [
            i
            for i in issues
            if "union" in i.message.lower() and "style" in i.message.lower()
        ]
        assert len(union_issues) == 0

    def test_lint_template_no_issues(self):
        linter = Linter()
        template = """
{# typja:from typing import List #}
{# typja:var items: List[str] #}
{% for item in items %}
    <p>{{ item }}</p>
{% endfor %}
"""

        config = {
            "prefer_pep604_unions": True,
            "union_style": "warning",
            "warn_unused_imports": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_lint_multiple_templates(self):
        linter = Linter()

        template1 = "{# typja:var name: str #}\n<p>{{ name }}</p>"
        template2 = "{# typja:var age: int #}\n<p>{{ age }}</p>"

        config = {"prefer_pep604_unions": True}

        issues1 = linter.lint_template(template1, "template1.html", config)
        issues2 = linter.lint_template(template2, "template2.html", config)

        assert isinstance(issues1, list)
        assert isinstance(issues2, list)
        assert len(issues1) == 0
        assert len(issues2) == 0

    def test_lint_with_macro_declarations(self):

        linter = Linter()
        template = """
{# typja:macro greet(name: str) -> str #}
{% macro greet(name) %}
    Hello {{ name }}
{% endmacro %}
"""

        config = {"prefer_pep604_unions": True}

        issues = linter.lint_template(template, "test.html", config)

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_lint_with_filter_declarations(self):

        linter = Linter()
        template = """
{# typja:from typing import Callable #}
{# typja:filter uppercase: Callable[[str], str] #}
{# typja:var name: str #}
<p>{{ name | uppercase }}</p>
"""

        config = {
            "prefer_pep604_unions": True,
            "warn_unused_imports": True,
        }

        issues = linter.lint_template(template, "test.html", config)

        unused_callable = [
            i
            for i in issues
            if "unused" in i.message.lower() and "callable" in i.message.lower()
        ]
        assert len(unused_callable) == 0

    def test_lint_fix_union_syntax(self):
        linter = Linter()

        old_union = "Union[str, int]"
        fixed = linter._fix_pep604_union(old_union)

        assert fixed == "str | int"

    def test_lint_fix_complex_union(self):
        linter = Linter()

        old_union = "Union[str, int, list]"
        fixed = linter._fix_pep604_union(old_union)

        assert fixed == "str | int | list"

    def test_lint_check_pep604_union(self):

        linter = Linter()
        parser = CommentParser()

        comments = parser.parse_template("{# typja:var value: str | int #}")
        decl = comments[0].declarations[0]
        assert linter._check_pep604_union(decl.type_annotation) is True  # type: ignore

        comments = parser.parse_template(
            "{# typja:from typing import Union #}\n{# typja:var value: Union[str, int] #}"
        )
        var_comment = [c for c in comments if c.kind == "var"][0]
        decl = var_comment.declarations[0]

        assert linter._check_pep604_union(decl.type_annotation) is False  # type: ignore

    def test_lint_check_unused_import(self):

        linter = Linter()

        content = """
{# typja:from typing import List #}
{# typja:var items: List[str] #}
"""
        list_result = linter._check_unused_import("List", content)
        dict_result = linter._check_unused_import("Dict", content)
        
        assert list_result is True
        assert dict_result is False

    def test_lint_template_from_fixtures(self, valid_templates_dir):

        linter = Linter()

        simple_template = (valid_templates_dir / "simple_vars.html").read_text()

        config = {
            "prefer_pep604_unions": True,
            "union_style": "warning",
            "warn_unused_imports": True,
        }

        issues = linter.lint_template(simple_template, "simple_vars.html", config)

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_lint_union_type_fixture(self, valid_templates_dir):
        linter = Linter()

        union_template = (valid_templates_dir / "union_types.html").read_text()

        config = {
            "prefer_pep604_unions": True,
            "union_style": "warning",
        }

        issues = linter.lint_template(union_template, "union_types.html", config)

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_lint_severity_levels(self):

        linter = Linter()
        template = """
{# typja:from typing import Union #}
{# typja:var value: Union[str, int] #}
<p>{{ value }}</p>
"""

        config_warning = {
            "prefer_pep604_unions": True,
            "union_style": "warning",
        }

        config_error = {
            "prefer_pep604_unions": True,
            "union_style": "error",
        }

        issues_warning = linter.lint_template(template, "test.html", config_warning)
        issues_error = linter.lint_template(template, "test.html", config_error)

        warnings = [i for i in issues_warning if i.severity == "warning"]
        errors = [i for i in issues_error if i.severity == "error"]

        assert len(warnings) > 0 or len(errors) > 0
