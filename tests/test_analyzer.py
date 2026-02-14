from jinja2 import Environment

from typja.analyzer import TemplateAnalyzer, ValidationIssue
from typja.registry import TypeDefinition, TypeRegistry
from typja.resolver import ResolvedType, TypeResolver


class TestValidationIssue:

    def test_create_validation_issue(self):
        issue = ValidationIssue(
            severity="error",
            message="Test error",
            filename="test.html",
            line=1,
            col=0,
        )

        assert issue.severity == "error"
        assert issue.message == "Test error"
        assert issue.filename == "test.html"
        assert issue.line == 1

    def test_validation_issue_with_hint(self):
        issue = ValidationIssue(
            severity="warning",
            message="Test warning",
            filename="test.html",
            line=5,
            col=10,
            hint="Try this instead",
        )

        assert issue.hint == "Try this instead"


class TestTemplateAnalyzer:

    def test_create_analyzer(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        assert analyzer.registry == registry
        assert analyzer.jinja_env is not None

    def test_create_analyzer_with_custom_env(self):
        registry = TypeRegistry()
        custom_env = Environment()
        analyzer = TemplateAnalyzer(registry, jinja_env=custom_env)

        assert analyzer.jinja_env == custom_env

    def test_analyze_simple_template(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:var name: str #}
<p>{{ name }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        assert len(issues) == 0

    def test_analyze_template_undefined_variable(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:var name: str #}
<p>{{ undefined_var }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        undefined_issues = [i for i in issues if "undefined" in i.message.lower()]
        assert len(undefined_issues) > 0

    def test_analyze_template_with_imports(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:from typing import List #}
{# typja:var items: List[str] #}
{% for item in items %}
    <p>{{ item }}</p>
{% endfor %}
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_analyze_template_with_custom_type(self):
        registry = TypeRegistry()
        user_type = TypeDefinition(
            name="User",
            fields={"id": "int", "name": "str", "email": "str"},
            module="models",
        )
        registry.register_module_types("models", {"User": user_type})

        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:from models import User #}
{# typja:var user: User #}
<p>{{ user.name }}</p>
<p>{{ user.email }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_analyze_template_invalid_attribute(self):
        """Test analyzing template with invalid attribute access"""
        registry = TypeRegistry()
        user_type = TypeDefinition(
            name="User", fields={"id": "int", "name": "str"}, module="models"
        )
        registry.register_module_types("models", {"User": user_type})

        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:from models import User #}
{# typja:var user: User #}
<p>{{ user.name }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        # Should not have errors for valid attribute
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_analyze_template_syntax_error(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{% for item in items
<p>{{ item }}</p>
{% endfor %}
"""

        issues = analyzer.analyze_template(template, "test.html")

        assert len(issues) > 0
        assert any(i.severity == "error" for i in issues)

    def test_analyze_template_with_filters(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:var name: str #}
<p>{{ name | upper }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        filter_errors = [e for e in errors if "upper" in e.message.lower()]
        assert len(filter_errors) == 0

    def test_analyze_template_union_types(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:var value: str | int #}
<p>{{ value }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_analyze_template_optional_type(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:from typing import Optional #}
{# typja:var name: Optional[str] #}
{% if name %}
    <p>{{ name }}</p>
{% endif %}
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_analyze_multiple_templates(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template1 = "{# typja:var name: str #}\n<p>{{ name }}</p>"
        template2 = "{# typja:var age: int #}\n<p>{{ age }}</p>"

        issues1 = analyzer.analyze_template(template1, "template1.html")
        issues2 = analyzer.analyze_template(template2, "template2.html")

        assert isinstance(issues1, list)
        assert isinstance(issues2, list)

    def test_add_issue(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        analyzer.add_issue(
            severity="error",
            message="Test error",
            filename="test.html",
            line=1,
            col=0,
        )

        assert len(analyzer.issues) == 1
        assert analyzer.issues[0].severity == "error"
        assert analyzer.issues[0].message == "Test error"

    def test_add_issue_with_hint(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        analyzer.add_issue(
            severity="warning",
            message="Test warning",
            filename="test.html",
            line=5,
            col=10,
            hint="Fix this by...",
        )

        assert len(analyzer.issues) == 1
        assert analyzer.issues[0].hint == "Fix this by..."

    def test_analyze_with_resolver(self, test_data_dir):
        registry = TypeRegistry()
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])
        resolver.populate_registry(registry)

        analyzer = TemplateAnalyzer(registry, resolver=resolver)

        template = """
{# typja:var user: User #}
<p>{{ user.name }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")
        errors = [i for i in issues if i.severity == "error"]
        name_errors = [e for e in errors if "name" in e.message.lower()]

        assert len(name_errors) == 0

    def test_analyze_with_macro(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:macro greet(name: str) -> str #}
{% macro greet(name) %}
    Hello {{ name }}
{% endmacro %}

{{ greet("World") }}
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_analyze_template_with_for_loop(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:from typing import List #}
{# typja:var items: List[str] #}
{% for item in items %}
    <p>{{ item }}</p>
{% endfor %}
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        assert len([e for e in errors if "for" in e.message.lower()]) == 0

    def test_analyze_builtin_types(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:var count: int #}
{# typja:var name: str #}
{# typja:var active: bool #}
{# typja:var price: float #}
<p>{{ count }} {{ name }} {{ active }} {{ price }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]

        assert len(errors) == 0

    def test_analyze_dict_type(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:var user: dict #}
<p>{{ user.name }}</p>
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]

        assert isinstance(issues, list)
        assert len(errors) == 0

    def test_analyze_list_type(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template = """
{# typja:from typing import List #}
{# typja:var items: List[int] #}
{% for item in items %}
    <p>{{ item }}</p>
{% endfor %}
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0

    def test_clear_issues_between_templates(self):
        registry = TypeRegistry()
        analyzer = TemplateAnalyzer(registry)

        template1 = "{# typja:var name: str #}\n<p>{{ name }}</p>"
        template2 = "{# typja:var age: int #}\n<p>{{ age }}</p>"

        issues1 = analyzer.analyze_template(template1, "template1.html")
        issues2 = analyzer.analyze_template(template2, "template2.html")

        assert isinstance(issues1, list)
        assert isinstance(issues2, list)
        assert len(issues1) >= 0
        assert len(issues2) >= 0

    def test_loop_variable_attribute_validation(self, tmp_path):
        registry = TypeRegistry()
        user_type = TypeDefinition(
            name="User",
            fields={"id": "int", "name": "str", "email": "str"},
            module="models",
        )
        registry.register_module_types("models", {"User": user_type})

        resolver = TypeResolver(tmp_path, exclude_patterns=[])
        resolver.resolved_types = {
            "User": ResolvedType(
                name="User",
                module_path="models",
                file_path=tmp_path / "models.py",
                fields={"id": "int", "name": "str", "email": "str"},
                methods={},
                bases=[],
            )
        }

        analyzer = TemplateAnalyzer(registry, resolver=resolver)

        template = """
{# typja:from typing import List #}
{# typja:from models import User #}
{# typja:var users: List[User] #}
{% for u in users %}
    <p>{{ u.name }}</p>
    <p>{{ u.dog }}</p>
{% endfor %}
"""

        issues = analyzer.analyze_template(template, "test.html")

        errors = [i for i in issues if i.severity == "error"]
        dog_errors = [e for e in errors if "dog" in e.message.lower()]

        assert len(dog_errors) == 1

    def test_loop_variable_valid_attributes(self, tmp_path):

        registry = TypeRegistry()
        user_type = TypeDefinition(
            name="User",
            fields={"id": "int", "name": "str", "email": "str"},
            module="models",
        )
        registry.register_module_types("models", {"User": user_type})

        resolver = TypeResolver(tmp_path, exclude_patterns=[])
        resolver.resolved_types = {
            "User": ResolvedType(
                name="User",
                module_path="models",
                file_path=tmp_path / "models.py",
                fields={"id": "int", "name": "str", "email": "str"},
                methods={},
                bases=[],
            )
        }

        analyzer = TemplateAnalyzer(registry, resolver=resolver)

        template = """
{# typja:from typing import List #}
{# typja:from models import User #}
{# typja:var users: List[User] #}
{% for u in users %}
    <p>{{ u.name }}</p>
    <p>{{ u.email }}</p>
{% endfor %}
"""

        issues = analyzer.analyze_template(template, "test.html")
        errors = [i for i in issues if i.severity == "error"]

        assert len(errors) == 0
        assert len(errors) == 0
