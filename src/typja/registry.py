from dataclasses import dataclass

from typja.constants import PYTHON_BUILTINS, TYPING_TYPES
from typja.exceptions import TypjaValidationError
from typja.parser.ast import TypeAnnotation


@dataclass
class TypeDefinition:
    """
    Schema that represents type definition from typja.toml

    Attributes:
        name (str): The name of the type (e.g. "User")
        fields (dict[str, str]): A mapping of field names to their type annotations (e.g. {"id": "int", "name": "str"})
        methods (dict[str, str] | None): Optional mapping of method names to their signatures (e.g. {"greet": "def greet(self) -> str"})
        module (str | None): Optional module name if this type belongs to a specific module (e.g. "models")
    """

    name: str
    fields: dict[str, str]
    methods: dict[str, str] | None = None
    module: str | None = None

    def has_field(self, field_name: str) -> bool:
        """
        Check if type has a field
        """

        return field_name in self.fields

    def get_field_type(self, field_name: str) -> str | None:
        """
        Get the type of a field
        """

        return self.fields.get(field_name)

    def has_method(self, method_name: str) -> bool:
        """
        Check if type has a method
        """

        return self.methods is not None and method_name in self.methods

    def get_method_signature(self, method_name: str) -> str | None:
        """
        Get the signature of a method
        """

        if self.methods is None:
            return None

        return self.methods.get(method_name)


class TypeRegistry:
    """
    Registry for managing type definitions and imports
    """

    def __init__(self):
        self._types: dict[str, TypeDefinition] = {}
        self._modules: dict[str, dict[str, TypeDefinition]] = {}
        self._imported_names: dict[str, TypeDefinition] = {}
        self._auto_imported_names: dict[str, TypeDefinition] = {}
        self._imported_modules: set[str] = set()
        self._builtins = PYTHON_BUILTINS
        self._typing_types = TYPING_TYPES

    def register_type(self, type_def: TypeDefinition) -> None:
        self._types[type_def.name] = type_def

        if type_def.module:
            if type_def.module not in self._modules:
                self._modules[type_def.module] = {}

            self._modules[type_def.module][type_def.name] = type_def

    def register_module_types(self, module: str, types: dict[str, TypeDefinition]) -> None:
        self._modules[module] = types

        for type_def in types.values():
            type_def.module = module
            self._types[type_def.name] = type_def

    def import_module(self, module: str) -> None:
        """
        Import a module (makes it available via module.Type)

        Args:
            module (str): Module to import
        """

        if module not in self._modules and module not in ["typing", "builtins"]:
            raise TypjaValidationError(f"Module '{module}' not found")

        self._imported_modules.add(module)

    def import_from_module(self, module: str, names: list[tuple[str, str | None]]) -> None:
        """
        Import specific names from a module.

        Args:
            module (str): Module to import from
            names (list[tuple[str, str | None]]): List of (name, alias) tuples
        """

        if module == "typing":
            for name, alias in names:
                if name not in self._typing_types:
                    raise TypjaValidationError(f"'{name}' is not available in typing module")

                # typing imports don't need definitions, just mark as imported
                self._imported_names[alias or name] = None  # type: ignore
            return

        if module not in self._modules:
            raise TypjaValidationError(f"Module '{module}' not found")

        module_types = self._modules[module]
        for name, alias in names:
            if name not in module_types:
                raise TypjaValidationError(
                    f"Module '{module}' has no type '{name}'. " f"Available types: {', '.join(module_types.keys())}"
                )
            self._imported_names[alias or name] = module_types[name]

    def resolve_type(self, type_annotation: TypeAnnotation) -> TypeDefinition | None:
        """
        Resolve a type annotation to its definition

        Args:
            type_annotation (TypeAnnotation): The type annotation to resolve
        """

        if type_annotation.is_union:
            if type_annotation.union_types:
                for union_type in type_annotation.union_types:
                    self.resolve_type(union_type)

            return None

        if type_annotation.name in self._builtins:
            return None

        if type_annotation.name in self._typing_types:
            if type_annotation.module == "typing" or type_annotation.name in self._imported_names:
                return None

            raise TypjaValidationError(
                f"'{type_annotation.name}' is not defined. "
                f"Did you mean to import it from typing?\n"
                f"\nHint: {{# typja:from typing import {type_annotation.name} #}}"
            )

        if type_annotation.module:
            if type_annotation.module not in self._imported_modules:
                raise TypjaValidationError(
                    f"Module '{type_annotation.module}' is not imported.\n"
                    f"\nHint: {{# typja:import {type_annotation.module} #}}"
                )

            if type_annotation.module not in self._modules:
                raise TypjaValidationError(f"Module '{type_annotation.module}' not found")

            module_types = self._modules[type_annotation.module]
            if type_annotation.name not in module_types:
                raise TypjaValidationError(f"Module '{type_annotation.module}' has no type '{type_annotation.name}'")

            return module_types[type_annotation.name]

        if type_annotation.name in self._imported_names:
            return self._imported_names[type_annotation.name]

        raise TypjaValidationError(
            f"'{type_annotation.name}' is not defined.\n"
            f"\nHint: Import it with {{# typja:from <module> import {type_annotation.name} #}}"
        )

    def get_type(self, name: str) -> TypeDefinition | None:
        return self._types.get(name)

    def get_module_types(self, module: str) -> dict[str, TypeDefinition]:
        return self._modules.get(module, {})

    def is_builtin(self, type_name: str) -> bool:
        return type_name in self._builtins

    def clear_imports(self) -> None:
        self._imported_names.clear()
        self._imported_modules.clear()
        self._imported_names.update(self._auto_imported_names)
