from dataclasses import dataclass
from typing import Literal

from jinja2 import Environment, nodes
from jinja2.exceptions import TemplateError
from jinja2.visitor import NodeVisitor

from typja.constants import PYTHON_BUILTINS, TYPING_TYPES
from typja.exceptions import TypjaValidationError
from typja.parser import CommentParser
from typja.parser.ast import (
    FilterDeclaration,
    FromImportStatement,
    ImportStatement,
    MacroDeclaration,
    TypeAnnotation,
    TypjaComment,
    VariableDeclaration,
)
from typja.registry import TypeRegistry
from typja.resolver import TypeResolver


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found in a template

    Attributes:
        severity (Literal['error', 'warning']): The severity of the issue ('error' or 'warning')
        message (str): A descriptive message about the issue
        filename (str): The name of the file where the issue was found
        line (int): The line number where the issue was found
        col (int): The column number where the issue was found (default is 0)
        end_col (int | None): The end column number for the problematic text (default is None)
        hint (str | None): An optional hint to help fix the issue (default is None)
    """

    severity: Literal["error", "warning"]
    message: str
    filename: str
    line: int
    col: int = 0
    end_col: int | None = None
    hint: str | None = None

    def __str__(self) -> str:
        location = f"{self.filename}:{self.line}"
        if self.col:
            location += f":{self.col}"

        result = f"{location}: {self.severity}: {self.message}"
        if self.hint:
            result += f"\nHint: {self.hint}"
        return result


class TemplateAnalyzer:
    """
    Analyze and validate Jinja templates with type annotations
    """

    def __init__(
        self,
        registry: TypeRegistry,
        jinja_env: Environment | None = None,
        resolver: TypeResolver | None = None,
    ):
        self.registry = registry
        self.jinja_env = jinja_env or Environment(autoescape=True, extensions=["jinja2.ext.do"])

        if self.jinja_env.autoescape is False:
            self.jinja_env.autoescape = True

        self.comment_parser = CommentParser()
        self.resolver = resolver

        self.variables: dict[str, VariableDeclaration] = {}
        self.filters: dict[str, FilterDeclaration] = {}
        self.macros: dict[str, MacroDeclaration] = {}
        self.ignored_lines: set[int] = set()
        self.issues: list[ValidationIssue] = []
        self._content_lines: list[str] = []

    def analyze_template(self, content: str, filename: str = "<unknown>") -> list[ValidationIssue]:

        self.registry.clear_imports()
        self._content_lines = content.splitlines()

        try:
            comments = self.comment_parser.parse_template(content, filename)

            for comment in comments:
                self._process_comment(comment, filename)

            try:
                ast = self.jinja_env.parse(content, filename=filename)
                self._validate_ast(ast, filename)
            except TemplateError as e:
                self.issues.append(
                    ValidationIssue(
                        severity="error",
                        message=f"Jinja2 syntax error: {e.message}",
                        filename=filename,
                        line=getattr(e, "lineno", 0),
                    )
                )

        except TypjaValidationError as e:
            self.issues.append(
                ValidationIssue(
                    severity="error",
                    message=str(e),
                    filename=filename,
                    line=getattr(e, "line", 0),
                    col=getattr(e, "col", 0),
                )
            )

        return self.issues

    def _process_comment(self, comment: TypjaComment, filename: str) -> None:

        if comment.kind == "ignore":
            self.ignored_lines.add(comment.line)
            return

        for decl in comment.declarations:
            if isinstance(decl, ImportStatement):
                self.registry.import_module(decl.module)

            elif isinstance(decl, FromImportStatement):
                self.registry.import_from_module(decl.module, decl.names)

            elif isinstance(decl, VariableDeclaration):
                if self.resolver:
                    self._validate_type_declaration(decl, filename)
                else:
                    try:
                        self.registry.resolve_type(decl.type_annotation)
                    except TypjaValidationError as e:
                        self.issues.append(
                            ValidationIssue(
                                severity="error",
                                message=str(e),
                                filename=filename,
                                line=decl.line,
                                col=decl.col,
                            )
                        )

                self.variables[decl.name] = decl

            elif isinstance(decl, FilterDeclaration):
                if decl.type_annotation.name != "Callable":
                    self.issues.append(
                        ValidationIssue(
                            severity="error",
                            message=f"Filter '{decl.name}' must have Callable type",
                            filename=filename,
                            line=decl.line,
                            col=decl.col,
                        )
                    )

                self.filters[decl.name] = decl

            elif isinstance(decl, MacroDeclaration):

                for param_name, param_type, _, _ in decl.params:
                    try:
                        self.registry.resolve_type(param_type)
                    except TypjaValidationError as e:
                        self.issues.append(
                            ValidationIssue(
                                severity="error",
                                message=f"Invalid type for parameter '{param_name}': {str(e)}",
                                filename=filename,
                                line=decl.line,
                                col=decl.col,
                            )
                        )

                try:
                    self.registry.resolve_type(decl.return_type)
                except TypjaValidationError as e:
                    self.issues.append(
                        ValidationIssue(
                            severity="error",
                            message=f"Invalid return type: {str(e)}",
                            filename=filename,
                            line=decl.line,
                            col=decl.col,
                        )
                    )

                self.macros[decl.name] = decl

    def _validate_ast(self, ast: nodes.Template, filename: str) -> None:

        visitor = ValidationVisitor(self, filename)
        visitor.visit(ast)

    def add_issue(
        self,
        severity: Literal["error", "warning"],
        message: str,
        filename: str,
        line: int,
        col: int = 0,
        end_col: int | None = None,
        hint: str | None = None,
    ) -> None:

        self.issues.append(
            ValidationIssue(
                severity=severity,
                message=message,
                filename=filename,
                line=line,
                col=col,
                end_col=end_col,
                hint=hint,
            )
        )

    def _validate_type_declaration(self, decl: VariableDeclaration, filename: str) -> None:
        """
        Validate that a type declaration references a known type

        Args:
            decl (VariableDeclaration): The variable declaration to validate
            filename (str): The filename for error reporting
        """

        if not self.resolver:
            return

        type_annotation = decl.type_annotation

        if type_annotation.is_union and type_annotation.union_types:
            for union_type in type_annotation.union_types:
                self._validate_single_type(union_type, decl, filename)
        else:
            self._validate_single_type(type_annotation, decl, filename)

    def _validate_single_type(self, type_annotation: TypeAnnotation, decl: VariableDeclaration, filename: str) -> None:
        """
        Validate a single type annotation

        Args:
            type_annotation (TypeAnnotation): The type annotation to validate
            decl (VariableDeclaration): The variable declaration
            filename (str): The filename for error reporting
        """

        if not self.resolver:
            return

        type_name = type_annotation.name

        if type_name in PYTHON_BUILTINS or type_name in TYPING_TYPES:
            return

        base_type_name = type_name
        if type_annotation.module:
            base_type_name = type_name

        if type_name in self.registry._imported_names:
            return

        conflicts = self.resolver.get_type_conflicts()
        if type_name in conflicts and not type_annotation.module:
            conflicting_types = conflicts[type_name]
            qualified_names = [f"{rt.qualified_name}" for rt in conflicting_types]
            self.add_issue(
                severity="error",
                message=f"Ambiguous type '{type_name}' found in multiple files",
                filename=filename,
                line=decl.line,
                col=decl.col,
                hint=f"Use qualified name: {', '.join(qualified_names)} or import explicitly with {{# typja:from <module> import {type_name} #}}",
            )
            return

        if not self.resolver.validate_type_exists(base_type_name):
            self.add_issue(
                severity="error",
                message=f"Type '{type_name}' not found in configured paths",
                filename=filename,
                line=decl.line,
                col=decl.col,
                hint=f"Make sure '{type_name}' is defined in files under the 'paths' configuration",
            )

        if type_annotation.args:
            for arg in type_annotation.args:
                self._validate_single_type(arg, decl, filename)

    def _get_column_position(self, line_no: int, text: str) -> tuple[int, int | None]:
        """
        Get the column position of text in a specific line

        Args:
            line_no (int): Line number (1-based)
            text (str): Text to find in the line

        Returns:
            tuple[int, int | None]: (start_col, end_col) or (0, None) if not found
        """

        if line_no <= 0 or line_no > len(self._content_lines):
            return 0, None

        line_content = self._content_lines[line_no - 1]
        start_pos = line_content.find(text)

        if start_pos == -1:
            return 0, None

        end_pos = start_pos + len(text)
        return start_pos, end_pos


class ValidationVisitor(NodeVisitor):

    def __init__(self, analyzer: TemplateAnalyzer, filename: str):
        self.analyzer = analyzer
        self.filename = filename
        self.loop_vars: dict[str, TypeAnnotation] = {}

    def visit_Name(self, node: nodes.Name) -> None:
        # skip checks for lines marked with `{# typja: ignore #}`
        if node.lineno in self.analyzer.ignored_lines:
            return

        if node.ctx == "load":
            var_name = node.name

            if var_name in self.loop_vars:
                return

            if var_name not in self.analyzer.variables:
                col_start, col_end = self.analyzer._get_column_position(node.lineno, var_name)
                self.analyzer.add_issue(
                    severity="warning",
                    message=f"Variable '{var_name}' is not declared",
                    filename=self.filename,
                    line=node.lineno,
                    col=col_start,
                    end_col=col_end,
                    hint=f"Add declaration: {{# typja:var {var_name}: <type> #}}",
                )

    def visit_Filter(self, node: nodes.Filter) -> None:
        # skip checks for lines marked with `{# typja: ignore #}`
        if node.lineno in self.analyzer.ignored_lines:
            return

        filter_name = node.name

        if filter_name in self.analyzer.filters:
            filter_decl = self.analyzer.filters[filter_name]

            if filter_decl.type_annotation.name == "Callable" and filter_decl.type_annotation.args:
                if len(filter_decl.type_annotation.args) >= 2:
                    arg_types_annotation = filter_decl.type_annotation.args[0]

                    expected_count = 1
                    if arg_types_annotation.args:
                        expected_count = len(arg_types_annotation.args)

                    actual_count = 1
                    if node.args:
                        actual_count += len(node.args)
                    if node.kwargs:
                        actual_count += len(node.kwargs)
                    if node.dyn_args:
                        actual_count = -1  # I can't validate with dynamic args for now, so I just skip it
                    if node.dyn_kwargs:
                        actual_count = -1  # I can't validate with dynamic kwargs for now, so I just skip it

                    if actual_count != -1 and actual_count != expected_count:
                        self.analyzer.add_issue(
                            severity="error",
                            message=f"Filter '{filter_name}' expects {expected_count} argument(s) but got {actual_count}",
                            filename=self.filename,
                            line=node.lineno,
                        )

        self.generic_visit(node)

    def visit_Getattr(self, node: nodes.Getattr) -> None:
        # skip checks for lines marked with `{# typja: ignore #}`
        if node.lineno in self.analyzer.ignored_lines:
            return

        base_type_annotation = self._resolve_node_type(node.node)

        if base_type_annotation and self.analyzer.resolver:
            base_type_name = self._get_base_type_name(base_type_annotation)

            # Special handling for explicitly imported types - use the registry to get the correct type
            if base_type_annotation.name in self.analyzer.registry._imported_names and not base_type_annotation.module:
                imported_type_def = self.analyzer.registry._imported_names[base_type_annotation.name]
                if imported_type_def and imported_type_def.module:
                    base_type_name = f"{imported_type_def.module}.{base_type_annotation.name}"

            if base_type_name:
                is_valid, error_msg = self.analyzer.resolver.validate_attribute(base_type_name, node.attr)

                if not is_valid:
                    # Get column position for the attribute
                    col_start, col_end = self.analyzer._get_column_position(node.lineno, node.attr)

                    self.analyzer.add_issue(
                        severity="error",
                        message=f"Type '{base_type_name}' has no attribute '{node.attr}'",
                        filename=self.filename,
                        line=node.lineno,
                        col=col_start,
                        end_col=col_end,
                        hint=f"Check the definition of '{base_type_name}' for available attributes",
                    )

        self.generic_visit(node)

    def _resolve_node_type(self, node: nodes.Node) -> TypeAnnotation | None:
        """
        Recursively resolve the type of a node (Name, Getattr, or Getitem)

        Args:
            node (nodes.Node): The AST node to resolve

        Returns:
            TypeAnnotation | None: The resolved type annotation or None
        """

        if isinstance(node, nodes.Name):
            var_name = node.name

            if var_name in self.analyzer.variables:
                return self.analyzer.variables[var_name].type_annotation
            elif var_name in self.loop_vars:
                return self.loop_vars[var_name]

            return None

        elif isinstance(node, nodes.Getattr):
            base_type = self._resolve_node_type(node.node)

            if not base_type or not self.analyzer.resolver:
                return None

            base_type_name = self._get_base_type_name(base_type)
            if not base_type_name:
                return None

            attr_type_str = self.analyzer.resolver.get_attribute_type(base_type_name, node.attr)

            if attr_type_str:
                try:
                    from typja.parser.type import TypeParser

                    type_parser = TypeParser()
                    return type_parser.parse_type(attr_type_str, node.lineno, 0)
                except Exception:
                    return None

            return None

        elif isinstance(node, nodes.Getitem):
            base_type = self._resolve_node_type(node.node)

            if not base_type:
                return None

            if isinstance(node.arg, nodes.Const) and isinstance(node.arg.value, str):
                if self.analyzer.resolver:
                    base_type_name = self._get_base_type_name(base_type)
                    if base_type_name:
                        attr_type_str = self.analyzer.resolver.get_attribute_type(base_type_name, node.arg.value)
                        if attr_type_str:
                            try:
                                from typja.parser.type import TypeParser

                                type_parser = TypeParser()
                                return type_parser.parse_type(attr_type_str, node.lineno, 0)
                            except Exception:
                                return None

            if base_type.args and len(base_type.args) > 0:
                return base_type.args[0]

            return None

        return None

    def _get_base_type_name(self, type_annotation: TypeAnnotation) -> str | None:
        """
        Extract the base type name from a type annotation

        Args:
            type_annotation (TypeAnnotation): The type annotation

        Returns:
            str | None: The base type name or None
        """

        if type_annotation.args and len(type_annotation.args) > 0:
            return type_annotation.args[0].name

        if type_annotation.is_union and type_annotation.union_types:
            for union_type in type_annotation.union_types:
                if union_type.name != "None":
                    return self._get_base_type_name(union_type)

        # Handle qualified names - return the full qualified name
        if type_annotation.module:
            return f"{type_annotation.module}.{type_annotation.name}"

        return type_annotation.name

    def _original_visit_Getattr(self, node: nodes.Getattr) -> None:
        if isinstance(node.node, nodes.Name):
            var_name = node.node.name
            attr_name = node.attr

            if var_name in self.analyzer.variables:
                var_decl = self.analyzer.variables[var_name]

                try:
                    type_def = self.analyzer.registry.resolve_type(var_decl.type_annotation)

                    if type_def:
                        if not type_def.has_field(attr_name) and not type_def.has_method(attr_name):
                            self.analyzer.add_issue(
                                severity="error",
                                message=f"Type '{type_def.name}' has no attribute '{attr_name}'",
                                filename=self.filename,
                                line=node.lineno,
                            )
                except TypjaValidationError:
                    pass

        self.generic_visit(node)

    def visit_For(self, node: nodes.For) -> None:
        loop_var_name = None
        loop_var_type = None

        # Extract the loop variable name
        if isinstance(node.target, nodes.Name):
            loop_var_name = node.target.name

            if isinstance(node.iter, nodes.Name):
                iterable_name = node.iter.name

                if iterable_name in self.analyzer.variables:
                    var_decl = self.analyzer.variables[iterable_name]
                    iterable_type = var_decl.type_annotation

                    if iterable_type.args and len(iterable_type.args) > 0:
                        loop_var_type = iterable_type.args[0]

            if loop_var_type:
                self.loop_vars[loop_var_name] = loop_var_type

        for child in node.body:
            self.visit(child)

        if loop_var_name and loop_var_name in self.loop_vars:
            del self.loop_vars[loop_var_name]

        if node.else_:
            for child in node.else_:
                self.visit(child)

    def visit_Getitem(self, node: nodes.Getitem) -> None:
        # skip checks for lines marked with `{# typja: ignore #}`
        if node.lineno in self.analyzer.ignored_lines:
            return

        base_type = self._resolve_node_type(node.node)

        if base_type and self.analyzer.resolver:
            if isinstance(node.arg, nodes.Const) and isinstance(node.arg.value, str):
                base_type_name = self._get_base_type_name(base_type)

                if base_type_name:
                    is_valid, error_msg = self.analyzer.resolver.validate_attribute(base_type_name, node.arg.value)

                    if not is_valid:
                        col_start, col_end = self.analyzer._get_column_position(node.lineno, node.arg.value)
                        self.analyzer.add_issue(
                            severity="error",
                            message=error_msg or f"Type '{base_type_name}' has no attribute '{node.arg.value}'",
                            filename=self.filename,
                            line=node.lineno,
                            col=col_start,
                            end_col=col_end,
                            hint=f"Dictionary-style access user['{node.arg.value}'] requires the attribute to exist",
                        )

        self.generic_visit(node)

    def visit_Call(self, node: nodes.Call) -> None:
        # skip checks for lines marked with `{# typja: ignore #}`
        if node.lineno in self.analyzer.ignored_lines:
            return

        if isinstance(node.node, nodes.Name):
            func_name = node.node.name

            if func_name in self.analyzer.macros:
                macro_decl = self.analyzer.macros[func_name]

                required_params = [p for p in macro_decl.params if not p[2]]
                total_params = len(macro_decl.params)
                min_params = len(required_params)
                max_params = total_params

                actual_positional = len(node.args) if node.args else 0
                actual_keyword = len(node.kwargs) if node.kwargs else 0
                actual_total = actual_positional + actual_keyword

                # I can't validate with dynamic args and kwargs for now, so just skip it
                if node.dyn_args or node.dyn_kwargs:
                    self.generic_visit(node)
                    return

                if actual_total < min_params:
                    self.analyzer.add_issue(
                        severity="error",
                        message=f"Macro '{func_name}' requires at least {min_params} argument(s) but got {actual_total}",
                        filename=self.filename,
                        line=node.lineno,
                        hint=f"Required parameters: {', '.join(p[0] for p in required_params)}",
                    )

                elif actual_total > max_params:
                    self.analyzer.add_issue(
                        severity="error",
                        message=f"Macro '{func_name}' accepts at most {max_params} argument(s) but got {actual_total}",
                        filename=self.filename,
                        line=node.lineno,
                    )

                if node.kwargs:
                    param_names = {p[0] for p in macro_decl.params}
                    for kwarg in node.kwargs:
                        if kwarg.key not in param_names:
                            self.analyzer.add_issue(
                                severity="error",
                                message=f"Macro '{func_name}' has no parameter named '{kwarg.key}'",
                                filename=self.filename,
                                line=node.lineno,
                                hint=f"Valid parameters: {', '.join(param_names)}",
                            )

        self.generic_visit(node)
