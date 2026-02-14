from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class TypeAnnotation:
    """
    Schema representing a type annotation in jinja templates in typja comments

    Attributes:
        raw (str): The original type string
        name (str): The type name (e.g., 'list', 'admin', 'Callable')
        module (str | None): The module path (e.g., 'typing', 'types')
        args (list[TypeAnnotation] | None): The generic arguments
        is_union (bool): Whether the type is a union type
        union_types (list[TypeAnnotation] | None): The types in the union if is_union is True

    Examples:

        {# typja:var name: type #}
    """

    raw: str
    name: str
    module: str | None = None
    args: list["TypeAnnotation"] | None = None
    is_union: bool = False
    union_types: list["TypeAnnotation"] | None = None

    def __str__(self) -> str:
        if self.is_union and self.union_types:
            return " | ".join(str(t) for t in self.union_types)

        if self.module:
            base = f"{self.module}.{self.name}"
        else:
            base = self.name

        if self.args:
            args_str = ", ".join(str(arg) for arg in self.args)
            return f"{base}[{args_str}]"

        return base


@dataclass
class ImportStatement:
    """
    Schema representing an import statement in jinja templates in typja comments

    Attributes:
        module (str): The module being imported
        line (int): The line number where the import statement is located in the source code
        col (int): The column number where the import statement starts in the source code (default is 0)

    Examples:

        {# typja:import module #}
    """

    module: str
    line: int
    col: int = 0

    def __str__(self) -> str:
        return f"import {self.module}"


@dataclass
class FromImportStatement:
    """
    Schema representing a from-import statement in jinja templates in typja comments

    Attributes:
        module (str): The module being imported from
        names (list[tuple[str, str | None]]): A list of tuples representing the names being imported and their optional aliases
        line (int): The line number where the from-import statement is located in the source code
        col (int): The column number where the from-import statement starts in the source code (default is 0)

    Examples:

        {# typja:from module import name1, name2 as alias #}
    """

    module: str
    names: list[tuple[str, str | None]]  # [(name, alias), ...]
    line: int
    col: int = 0

    def __str__(self) -> str:
        imports = ", ".join(f"{name} as {alias}" if alias else name for name, alias in self.names)
        return f"from {self.module} import {imports}"


@dataclass
class VariableDeclaration:
    """
    Schema representing a variable declaration in jinja templates in typja comments

    Attributes:
        name (str): The name of the variable.
        type_annotation (TypeAnnotation): The type annotation of the variable.
        line (int): The line number where the variable declaration is located in the source code.
        col (int): The column number where the variable declaration starts in the source code (default is 0)

    Examples:

        {# typja:var name: type #}
    """

    name: str
    type_annotation: TypeAnnotation
    line: int
    col: int = 0

    def __str__(self) -> str:
        return f"{self.name}: {self.type_annotation}"


@dataclass
class FilterDeclaration:
    """
    Schema representing a filter declaration in jinja templates in typja comments

    Attributes:
        name (str): The name of the filter
        type_annotation (TypeAnnotation): The type annotation of the filter, which should be a Callable
        line (int): The line number where the filter declaration is located in the source code
        col (int): The column number where the filter declaration starts in the source code (default is 0)

    Examples:

        {# typja:filter name: Callable[[...], ...] #}
    """

    name: str
    type_annotation: TypeAnnotation
    line: int
    col: int = 0

    def __str__(self) -> str:
        return f"filter {self.name}: {self.type_annotation}"


@dataclass
class MacroDeclaration:
    """
    Schema for representing Macro Declarations in jinja templates in typja comments

    Attributes:
        name (str): The name of the macro
        params (list[tuple[str, TypeAnnotation, bool, Any]]): A list of parameters, where each parameter is represented as a tuple containing:
                                                               - parameter name (str)
                                                               - type annotation (TypeAnnotation)
                                                               - has_default flag (bool) - True if parameter has a default value
                                                               - default value (Any) - the default value if has_default is True, None otherwise
        return_type (TypeAnnotation): The return type annotation of the macro
        line (int): The line number where the macro declaration is located in the source code
        col (int): The column number where the macro declaration starts in the source code (default is 0)

    Examples:

        {# typja:macro name(arg: type, ...) -> return_type #}
    """

    name: str
    params: list[tuple[str, TypeAnnotation, bool, Any]]
    return_type: TypeAnnotation
    line: int
    col: int = 0

    def __str__(self) -> str:
        params_str = ", ".join(
            f"{name}: {typ}" + (f" = {default}" if has_default else "")
            for name, typ, has_default, default in self.params
        )
        return f"macro {self.name}({params_str}) -> {self.return_type}"


@dataclass
class TypjaComment:
    """
    Schema for all declarations or directives in a single typja comment

    Attributes:
        kind (Literal["import", "from_import", "var", "filter", "macro", "ignore"]): The type of declaration or directive contained in the comment
        declarations (list[ImportStatement | FromImportStatement | VariableDeclaration | FilterDeclaration | MacroDeclaration]): A list of declarations parsed from the comment (empty for directives such as `ignore`)
        line (int): The line number where the typja comment is located in the source code
        col (int): The column number where the typja comment starts in the source code (default is 0)
        raw (str): The original text of the typja comment, useful for error reporting and debugging (default is an empty string)
    """

    kind: Literal["import", "from_import", "var", "filter", "macro", "ignore"]
    declarations: list[
        ImportStatement | FromImportStatement | VariableDeclaration | FilterDeclaration | MacroDeclaration
    ]
    line: int
    col: int = 0
    raw: str = ""
