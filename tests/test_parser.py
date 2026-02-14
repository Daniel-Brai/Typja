import pytest

from typja.exceptions import TypjaParseError
from typja.parser import CommentParser
from typja.parser.ast import (
    FilterDeclaration,
    FromImportStatement,
    ImportStatement,
    MacroDeclaration,
    TypeAnnotation,
    VariableDeclaration,
)
from typja.parser.imports import ImportParser
from typja.parser.type import TypeParser


class TestParserAST:
    """Test AST node classes and their string representations"""

    def test_type_annotation_simple(self):
        ta = TypeAnnotation(raw="str", name="str", module=None)
        assert ta.name == "str"
        assert ta.module is None
        assert ta.args is None
        assert not ta.is_union
        assert str(ta) == "str"

    def test_type_annotation_with_module(self):
        ta = TypeAnnotation(raw="typing.List", name="List", module="typing")
        assert ta.name == "List"
        assert ta.module == "typing"
        assert str(ta) == "typing.List"

    def test_type_annotation_generic(self):
        str_arg = TypeAnnotation(raw="str", name="str", module=None)
        ta = TypeAnnotation(
            raw="List[str]", name="List", module="typing", args=[str_arg]
        )
        assert ta.name == "List"
        assert ta.args is not None
        assert len(ta.args) == 1
        assert ta.args[0].name == "str"

    def test_type_annotation_union(self):

        str_type = TypeAnnotation(raw="str", name="str", module=None)
        int_type = TypeAnnotation(raw="int", name="int", module=None)
        ta = TypeAnnotation(
            raw="str | int",
            name="Union",
            module=None,
            is_union=True,
            union_types=[str_type, int_type],
        )
        assert ta.is_union
        assert ta.union_types is not None
        assert len(ta.union_types) == 2

    def test_import_statement(self):

        stmt = ImportStatement(module="datetime", line=1, col=0)
        assert stmt.module == "datetime"
        assert stmt.line == 1
        assert str(stmt) == "import datetime"

    def test_from_import_statement(self):

        stmt = FromImportStatement(
            module="typing", names=[("List", None), ("Dict", "D")], line=1, col=0
        )
        assert stmt.module == "typing"
        assert len(stmt.names) == 2
        assert stmt.names[0] == ("List", None)
        assert stmt.names[1] == ("Dict", "D")
        assert str(stmt) == "from typing import List, Dict as D"

    def test_from_import_statement_no_alias(self):
        stmt = FromImportStatement(
            module="typing", names=[("Optional", None)], line=1, col=0
        )
        assert str(stmt) == "from typing import Optional"

    def test_variable_declaration(self):
        ta = TypeAnnotation(raw="str", name="str", module=None)
        var = VariableDeclaration(name="username", type_annotation=ta, line=1, col=0)
        assert var.name == "username"
        assert var.type_annotation.name == "str"
        assert str(var) == "username: str"

    def test_variable_declaration_complex_type(self):
        str_arg = TypeAnnotation(raw="str", name="str", module=None)
        list_type = TypeAnnotation(
            raw="List[str]", name="List", module="typing", args=[str_arg]
        )
        var = VariableDeclaration(name="items", type_annotation=list_type, line=1)
        assert var.name == "items"
        assert var.type_annotation.name == "List"


class TestParserTypes:

    def test_parse_simple_type(self):
        parser = TypeParser()
        ta = parser.parse_type("str", 1, 0)
        assert ta.name == "str"
        assert ta.module is None

    def test_parse_builtin_types(self):
        parser = TypeParser()
        builtins = ["int", "str", "float", "bool", "list", "dict", "tuple", "set"]
        for builtin in builtins:
            ta = parser.parse_type(builtin, 1, 0)
            assert ta.name == builtin

    def test_parse_qualified_type(self):
        parser = TypeParser()
        ta = parser.parse_type("typing.List", 1, 0)
        assert ta.name == "List"
        assert ta.module == "typing"

    def test_parse_generic_list(self):
        parser = TypeParser()
        ta = parser.parse_type("List[str]", 1, 0)
        assert ta.name == "List"
        assert ta.args is not None
        assert len(ta.args) == 1
        assert ta.args[0].name == "str"

    def test_parse_generic_dict(self):
        parser = TypeParser()
        ta = parser.parse_type("Dict[str, int]", 1, 0)
        assert ta.name == "Dict"
        assert ta.args is not None
        assert len(ta.args) == 2
        assert ta.args[0].name == "str"
        assert ta.args[1].name == "int"

    def test_parse_nested_generic(self):
        parser = TypeParser()
        ta = parser.parse_type("List[List[str]]", 1, 0)
        assert ta.name == "List"
        assert ta.args is not None
        assert ta.args[0].name == "List"
        assert ta.args[0].args is not None
        assert ta.args[0].args[0].name == "str"

    def test_parse_union_pep604(self):
        parser = TypeParser()
        ta = parser.parse_type("str | int", 1, 0)
        assert ta.is_union
        assert ta.union_types is not None
        assert len(ta.union_types) == 2
        assert ta.union_types[0].name == "str"
        assert ta.union_types[1].name == "int"

    def test_parse_union_old_style(self):
        parser = TypeParser()
        ta = parser.parse_type("Union[str, int]", 1, 0)
        assert ta.is_union
        assert ta.module == "typing"
        assert ta.union_types is not None
        assert len(ta.union_types) == 2

    def test_parse_optional(self):
        parser = TypeParser()
        ta = parser.parse_type("Optional[str]", 1, 0)
        assert ta.is_union
        assert ta.module == "typing"
        assert ta.union_types is not None
        assert len(ta.union_types) == 2
        assert any(t.name == "str" for t in ta.union_types)
        assert any(t.name == "None" for t in ta.union_types)

    def test_parse_callable_simple(self):
        parser = TypeParser()
        ta = parser.parse_type("Callable[[str], int]", 1, 0)
        assert ta.name == "Callable"
        assert ta.args is not None

    def test_parse_tuple(self):
        parser = TypeParser()
        ta = parser.parse_type("Tuple[int, str, bool]", 1, 0)
        assert ta.name == "Tuple"
        assert ta.args is not None
        assert len(ta.args) == 3

    def test_parse_complex_union(self):
        parser = TypeParser()
        ta = parser.parse_type("str | int | list", 1, 0)
        assert ta.is_union
        assert ta.union_types is not None
        assert len(ta.union_types) == 3

    def test_parse_type_with_spaces(self):
        parser = TypeParser()
        ta = parser.parse_type("  str  ", 1, 0)
        assert ta.name == "str"

    def test_parse_union_malformed(self):
        parser = TypeParser()
        with pytest.raises(TypjaParseError):
            parser.parse_type("Union[str, int", 1, 0)

    def test_parse_optional_malformed(self):
        parser = TypeParser()
        with pytest.raises(TypjaParseError):
            parser.parse_type("Optional[str", 1, 0)

        parser = TypeParser()
        with pytest.raises(TypjaParseError):
            parser.parse_type("Optional[str", 1, 0)

    def test_parse_generic_malformed(self):
        parser = TypeParser()
        with pytest.raises(TypjaParseError):
            parser.parse_type("List[str", 1, 0)


class TestParserImports:

    def test_parse_simple_import(self):
        parser = ImportParser()
        stmt = parser.parse_import("import datetime", 1, 0)

        assert isinstance(stmt, ImportStatement)
        assert stmt.module == "datetime"
        assert stmt.line == 1

    def test_parse_qualified_import(self):
        parser = ImportParser()
        stmt = parser.parse_import("import os.path", 1, 0)

        assert stmt.module == "os.path"

    def test_parse_from_import_single(self):
        parser = ImportParser()
        stmt = parser.parse_from_import("from typing import List", 1, 0)

        assert isinstance(stmt, FromImportStatement)
        assert stmt.module == "typing"
        assert len(stmt.names) == 1
        assert stmt.names[0] == ("List", None)

    def test_parse_from_import_multiple(self):
        parser = ImportParser()
        stmt = parser.parse_from_import("from typing import List, Dict, Tuple", 1, 0)

        assert stmt.module == "typing"
        assert len(stmt.names) == 3
        assert stmt.names[0] == ("List", None)
        assert stmt.names[1] == ("Dict", None)
        assert stmt.names[2] == ("Tuple", None)

    def test_parse_from_import_with_alias(self):
        parser = ImportParser()
        stmt = parser.parse_from_import("from typing import Dict as D", 1, 0)

        assert stmt.module == "typing"
        assert len(stmt.names) == 1
        assert stmt.names[0] == ("Dict", "D")

    def test_parse_from_import_mixed_aliases(self):
        parser = ImportParser()
        stmt = parser.parse_from_import(
            "from typing import List, Dict as D, Optional", 1, 0
        )

        assert len(stmt.names) == 3
        assert stmt.names[0] == ("List", None)
        assert stmt.names[1] == ("Dict", "D")
        assert stmt.names[2] == ("Optional", None)

    def test_parse_import_invalid(self):
        parser = ImportParser()
        with pytest.raises(TypjaParseError):
            parser.parse_import("import", 1, 0)

    def test_parse_import_extra_text(self):
        parser = ImportParser()
        with pytest.raises(TypjaParseError):
            parser.parse_import("import datetime extra", 1, 0)

        parser = ImportParser()
        with pytest.raises(TypjaParseError):
            parser.parse_import("import datetime extra", 1, 0)

    def test_parse_from_import_invalid(self):
        parser = ImportParser()
        with pytest.raises(TypjaParseError):
            parser.parse_from_import("from typing", 1, 0)

    def test_parse_from_import_no_module(self):
        parser = ImportParser()
        with pytest.raises(TypjaParseError):
            parser.parse_from_import("from import List", 1, 0)


class TestParserComment:
    """Test comment parser functionality"""

    def test_parse_simple_var(self):
        parser = CommentParser()
        comments = parser.parse_template("{# typja:var name: str #}")

        assert len(comments) == 1
        assert comments[0].kind == "var"
        assert len(comments[0].declarations) == 1

        decl = comments[0].declarations[0]

        assert isinstance(decl, VariableDeclaration)
        assert decl.name == "name"
        assert decl.type_annotation.name == "str"

    def test_parse_multiple_vars_single_comment(self):
        parser = CommentParser()
        comments = parser.parse_template("{# typja:var name: str, age: int #}")

        assert len(comments) == 1
        assert comments[0].kind == "var"
        assert len(comments[0].declarations) == 2

    def test_parse_import(self):
        parser = CommentParser()
        comments = parser.parse_template("{# typja:import datetime #}")

        assert len(comments) == 1
        assert comments[0].kind == "import"

        decl = comments[0].declarations[0]

        assert isinstance(decl, ImportStatement)
        assert decl.module == "datetime"

    def test_parse_from_import(self):
        parser = CommentParser()
        comments = parser.parse_template("{# typja:from typing import List #}")

        assert len(comments) == 1
        assert comments[0].kind == "from_import"

        decl = comments[0].declarations[0]

        assert isinstance(decl, FromImportStatement)
        assert decl.module == "typing"

    def test_parse_filter(self):
        parser = CommentParser()
        comments = parser.parse_template(
            "{# typja:filter uppercase: Callable[[str], str] #}"
        )

        assert len(comments) == 1
        assert comments[0].kind == "filter"

        decl = comments[0].declarations[0]

        assert isinstance(decl, FilterDeclaration)

    def test_parse_macro(self):
        parser = CommentParser()
        comments = parser.parse_template("{# typja:macro greet(name: str) -> str #}")

        assert len(comments) == 1
        assert comments[0].kind == "macro"

        decl = comments[0].declarations[0]

        assert isinstance(decl, MacroDeclaration)

    def test_parse_ignore(self):
        parser = CommentParser()
        comments = parser.parse_template("{# typja:ignore #}")

        assert len(comments) == 1
        assert comments[0].kind == "ignore"

    def test_parse_multiline_comment(self):
        parser = CommentParser()
        template = """{# 
        typja:var user: dict
        #}"""

        comments = parser.parse_template(template)

        assert len(comments) == 1
        assert comments[0].kind == "var"

    def test_parse_multiple_comments(self):
        parser = CommentParser()
        template = """
        {# typja:import datetime #}
        {# typja:var name: str #}
        {# typja:var age: int #}
        """
        comments = parser.parse_template(template)

        assert len(comments) == 3

    def test_parse_template_with_content(self, sample_template_simple):
        parser = CommentParser()
        comments = parser.parse_template(sample_template_simple)

        assert len(comments) >= 3
        var_comments = [c for c in comments if c.kind == "var"]

        assert len(var_comments) >= 1

    def test_parse_template_with_imports(self, sample_template_with_imports):
        parser = CommentParser()
        comments = parser.parse_template(sample_template_with_imports)
        import_comments = [c for c in comments if c.kind in ("import", "from_import")]

        assert len(import_comments) >= 1

    def test_parse_template_with_union_types(self, sample_template_union_types):
        parser = CommentParser()
        comments = parser.parse_template(sample_template_union_types)
        var_comments = [c for c in comments if c.kind == "var"]

        assert len(var_comments) >= 1

    def test_parse_invalid_missing_colon(self, invalid_templates_dir):
        parser = CommentParser()
        template = (invalid_templates_dir / "missing_colon.html").read_text()

        with pytest.raises(TypjaParseError):
            parser.parse_template(template)

    def test_parse_invalid_import(self, invalid_templates_dir):
        parser = CommentParser()
        template = (invalid_templates_dir / "invalid_import.html").read_text()

        with pytest.raises(TypjaParseError):
            parser.parse_template(template)

    def test_parse_invalid_from_import(self, invalid_templates_dir):
        parser = CommentParser()
        template = (invalid_templates_dir / "invalid_from_import.html").read_text()

        with pytest.raises(TypjaParseError):
            parser.parse_template(template)

    def test_parse_unknown_directive(self):
        parser = CommentParser()
        with pytest.raises(TypjaParseError):
            parser.parse_template("{# typja:unknown directive #}")

    def test_parse_empty_comment(self):
        parser = CommentParser()

        template = "{# typja: #}"
        with pytest.raises(TypjaParseError):
            parser.parse_template(template)

    def test_parse_with_line_numbers(self):
        parser = CommentParser()
        template = """line 1
{# typja:var name: str #}
line 3
{# typja:var age: int #}"""
        comments = parser.parse_template(template)
        assert len(comments) == 2
        assert comments[0].line == 2
        assert comments[1].line == 4

    def test_parse_complex_generic(self):
        parser = CommentParser()
        comments = parser.parse_template("{# typja:var data: Dict[str, List[int]] #}")

        assert len(comments) == 1

        decl = comments[0].declarations[0]
        assert decl.type_annotation.name == "Dict"  # type: ignore[union-attr]
