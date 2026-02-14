import re
from typing import Any

from typja.exceptions import TypjaParseError
from typja.parser.ast import (
    FilterDeclaration,
    FromImportStatement,
    ImportStatement,
    MacroDeclaration,
    TypeAnnotation,
    TypjaComment,
    VariableDeclaration,
)
from typja.parser.imports import ImportParser
from typja.parser.type import TypeParser


class CommentParser:
    """
    Parser for extracting and interpreting typja comments from Jinja templates
    """

    # Regex to find typja comments
    TYPJA_COMMENT_PATTERN = re.compile(r"\{#\s*typja:([^#]+?)#\}", re.MULTILINE | re.DOTALL)

    # Multi-line block pattern
    TYPJA_BLOCK_PATTERN = re.compile(r"\{#\s*typja:([^#]+?)#\}", re.MULTILINE | re.DOTALL)

    def __init__(self):
        self.import_parser = ImportParser()
        self.type_parser = TypeParser()

    def parse_template(self, content: str, filename: str = "<unknown>") -> list[TypjaComment]:
        comments: list[TypjaComment] = []

        for match in self.TYPJA_COMMENT_PATTERN.finditer(content):
            line = content[: match.start()].count("\n") + 1
            col = match.start() - content.rfind("\n", 0, match.start())
            raw = match.group(0)
            body = match.group(1).strip()

            try:
                comment = self._parse_comment_body(body, line, col, raw)
                comments.append(comment)
            except TypjaParseError as e:
                e.filename = filename
                e.line = line
                e.col = col
                raise

        return comments

    def _parse_comment_body(self, body: str, line: int, col: int, raw: str) -> TypjaComment:

        if body.startswith("import "):
            return self._parse_import(body, line, col, raw)
        elif body.startswith("from "):
            return self._parse_from_import(body, line, col, raw)
        elif body.startswith("var"):
            return self._parse_variables(body, line, col, raw)
        elif body.startswith("filter "):
            return self._parse_filter(body, line, col, raw)
        elif body.startswith("macro "):
            return self._parse_macro(body, line, col, raw)
        elif body == "ignore" or body.startswith("ignore "):
            return TypjaComment(kind="ignore", declarations=[], line=line, col=col, raw=raw)
        else:
            raise TypjaParseError(f"Unknown typja directive: {body[:20]}...", line=line, col=col)

    def _parse_import(self, body: str, line: int, col: int, raw: str) -> TypjaComment:
        stmt = self.import_parser.parse_import(body, line, col)
        return TypjaComment(kind="import", declarations=[stmt], line=line, col=col, raw=raw)

    def _parse_from_import(self, body: str, line: int, col: int, raw: str) -> TypjaComment:
        stmt = self.import_parser.parse_from_import(body, line, col)
        return TypjaComment(kind="from_import", declarations=[stmt], line=line, col=col, raw=raw)

    def _parse_variables(self, body: str, line: int, col: int, raw: str) -> TypjaComment:
        body = body[3:].strip()

        declarations: list[
            ImportStatement | FromImportStatement | VariableDeclaration | FilterDeclaration | MacroDeclaration
        ] = []

        var_parts = self._split_preserving_brackets(body, ",")

        for part in var_parts:
            part = part.strip()
            if not part:
                continue

            if ":" not in part:
                raise TypjaParseError(f"Invalid variable declaration: {part}", line=line, col=col)

            name, type_str = part.split(":", 1)
            name = name.strip()
            type_str = type_str.strip()

            if not name:
                raise TypjaParseError("Variable name cannot be empty", line=line, col=col)

            type_annotation = self.type_parser.parse_type(type_str, line, col)

            declarations.append(VariableDeclaration(name=name, type_annotation=type_annotation, line=line, col=col))

        return TypjaComment(kind="var", declarations=declarations, line=line, col=col, raw=raw)

    def _parse_filter(self, body: str, line: int, col: int, raw: str) -> TypjaComment:
        body = body[7:].strip()

        if ":" not in body:
            raise TypjaParseError(f"Invalid filter declaration: {body}", line=line, col=col)

        name, type_str = body.split(":", 1)
        name = name.strip()
        type_str = type_str.strip()

        type_annotation = self.type_parser.parse_type(type_str, line, col)

        return TypjaComment(
            kind="filter",
            declarations=[FilterDeclaration(name=name, type_annotation=type_annotation, line=line, col=col)],
            line=line,
            col=col,
            raw=raw,
        )

    def _parse_macro(self, body: str, line: int, col: int, raw: str) -> TypjaComment:
        body = body[6:].strip()

        if "(" not in body or ")" not in body:
            raise TypjaParseError(f"Invalid macro declaration: {body}", line=line, col=col)

        name = body[: body.index("(")].strip()
        params_end = body.rindex(")")
        params_str = body[body.index("(") + 1 : params_end].strip()

        return_type_str = None
        if "->" in body[params_end:]:
            return_type_str = body[body.index("->") + 2 :].strip()

        if not return_type_str:
            raise TypjaParseError(f"Macro must specify return type: {body}", line=line, col=col)

        params: list[tuple[str, TypeAnnotation, bool, Any]] = []
        if params_str:
            for param in self._split_preserving_brackets(params_str, ","):
                param = param.strip()
                if not param:
                    continue

                default: str | None = None
                has_default = False
                if "=" in param:
                    param, default_str = param.split("=", 1)
                    param = param.strip()
                    default = default_str.strip()
                    has_default = True

                if ":" not in param:
                    raise TypjaParseError(
                        f"Parameter must have type annotation: {param}",
                        line=line,
                        col=col,
                    )

                param_name, param_type_str = param.split(":", 1)
                param_name = param_name.strip()
                param_type_str = param_type_str.strip()

                param_type = self.type_parser.parse_type(param_type_str, line, col)
                params.append(
                    (
                        param_name,
                        param_type,
                        has_default,
                        default if has_default else None,
                    )
                )

        return_type = self.type_parser.parse_type(return_type_str, line, col)

        return TypjaComment(
            kind="macro",
            declarations=[
                MacroDeclaration(
                    name=name,
                    params=params,
                    return_type=return_type,
                    line=line,
                    col=col,
                )
            ],
            line=line,
            col=col,
            raw=raw,
        )

    @staticmethod
    def _split_preserving_brackets(text: str, delimiter: str) -> list[str]:
        parts: list[str] = []
        current: list[str] = []
        depth = 0

        for char in text:
            if char in "[({":
                depth += 1
                current.append(char)
            elif char in "])}":
                depth -= 1
                current.append(char)
            elif char == delimiter and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append("".join(current))

        return parts
