import ast
import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

from typja.registry import TypeDefinition, TypeRegistry


@dataclass(frozen=True)
class ResolvedType:
    """
    Represents a discovered type from Python source files

    Attributes:
        name (str): The type name
        module_path (str): The module path (e.g., 'models.user')
        file_path (Path): The file where the type is defined
        fields (dict[str, str]): Dictionary of field names to their type annotations
        methods (dict[str, str]): Dictionary of method names to their signatures
        bases (list[str]): List of base class names
        qualified_name (str): The fully qualified name (module.Type)
    """

    name: str
    module_path: str
    file_path: Path
    fields: dict[str, str] = field(default_factory=dict)
    methods: dict[str, str] = field(default_factory=dict)
    bases: list[str] = field(default_factory=list)
    qualified_name: str = field(init=False)

    def __post_init__(self):
        module_name = self.file_path.stem
        object.__setattr__(self, "qualified_name", f"{module_name}.{self.name}")


class TypeResolver:
    """
    Resolves types from Python source files and validates their usage
    """

    def __init__(self, root: Path, exclude_patterns: list[str] | None = None):
        self.root = root
        self.exclude_patterns: list[str] = exclude_patterns or []
        self.resolved_types: dict[str, ResolvedType] = {}
        self.type_conflicts: dict[str, list[ResolvedType]] = {}

    def resolve_paths(self, paths: list[Path]) -> dict[str, ResolvedType]:
        """
        Resolve types from a list of paths (files or directories)

        Args:
            paths (list[Path]): List of paths to scan for types

        Returns:
            dict[str, ResolvedType]: Dictionary mapping type names to their definitions
        """

        self.resolved_types = {}
        init_files: list[tuple[Path, ast.AST, str]] = []

        for path in paths:
            if not path.exists():
                continue

            if path.is_file() and path.suffix == ".py":
                self._resolve_file(path, collect_init=True, init_files=init_files)
            elif path.is_dir():
                for py_file in path.rglob("*.py"):
                    if not self._should_skip_file(py_file):
                        self._resolve_file(py_file, collect_init=True, init_files=init_files)

        for init_file, tree, module_path in init_files:
            self._process_init_imports(tree, module_path, init_file)

        return self.resolved_types

    def _should_skip_file(self, path: Path) -> bool:
        if not self.exclude_patterns:
            return False

        try:
            relative = path.relative_to(self.root)
            path_str = relative.as_posix()
        except ValueError:
            path_str = path.as_posix()

        normalized = path_str.lstrip("./")

        for pattern in self.exclude_patterns:
            cleaned_pattern = pattern.lstrip("./")
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(normalized, cleaned_pattern):
                return True

        return False

    def _resolve_file(
        self,
        file_path: Path,
        collect_init: bool = False,
        init_files: list[tuple[Path, ast.AST, str]] | None = None,
    ) -> None:
        """
        Extract type definitions from a single Python file

        Args:
            file_path (Path): Path to the Python file
            collect_init (bool): Whether to collect __init__.py files for later processing
            init_files (list): List to collect (file_path, tree, module_path) tuples for __init__.py files
        """

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))

            relative = file_path.relative_to(self.root)
            if relative.name == "__init__.py":
                module_parts = relative.parent.parts
            else:
                module_parts = relative.parent.parts + (relative.stem,)

            module_path = ".".join(module_parts) if module_parts else ""

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    resolved = self._extract_class_definition(node, module_path, file_path)
                    if resolved:
                        self.resolved_types[resolved.name] = resolved
                        if module_path:
                            qualified_name = f"{module_path}.{resolved.name}"
                            self.resolved_types[qualified_name] = resolved

            # If this is __init__.py and we're collecting, save it for second pass
            if relative.name == "__init__.py" and module_path and collect_init and init_files is not None:
                init_files.append((file_path, tree, module_path))

            # If we're not in collect mode and this is __init__.py, process imports immediately
            elif relative.name == "__init__.py" and module_path and not collect_init:
                self._process_init_imports(tree, module_path, file_path)

        except Exception:
            return

    def _process_init_imports(self, tree: ast.AST, module_path: str, init_file: Path) -> None:
        """
        Process imports in __init__.py to make imported types available at the module level

        Args:
            tree (ast.AST): The parsed AST of __init__.py
            module_path (str): The module path (e.g., 'models')
            init_file (Path): Path to the __init__.py file
        """

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue

                if node.level > 0:
                    if node.module:
                        imported_module = f"{module_path}.{node.module}"
                    else:
                        imported_module = module_path
                else:
                    imported_module = node.module

                for alias in node.names:
                    if alias.name == "*":
                        for key, resolved in list(self.resolved_types.items()):
                            if resolved.module_path == imported_module:
                                if "." not in key:
                                    new_resolved = ResolvedType(
                                        name=resolved.name,
                                        module_path=module_path,
                                        file_path=resolved.file_path,
                                        fields=resolved.fields,
                                        methods=resolved.methods,
                                        bases=resolved.bases,
                                    )
                                    module_level_key = f"{module_path}.{key}"
                                    if module_level_key not in self.resolved_types:
                                        self.resolved_types[module_level_key] = new_resolved
                                        if key not in self.resolved_types:
                                            self.resolved_types[key] = new_resolved
                    else:
                        imported_name = alias.name
                        qualified_imported = f"{imported_module}.{imported_name}"

                        resolved = None
                        if qualified_imported in self.resolved_types:
                            resolved = self.resolved_types[qualified_imported]
                        elif imported_name in self.resolved_types:
                            resolved = self.resolved_types[imported_name]

                        if resolved:
                            new_resolved = ResolvedType(
                                name=resolved.name,
                                module_path=module_path,
                                file_path=resolved.file_path,
                                fields=resolved.fields,
                                methods=resolved.methods,
                                bases=resolved.bases,
                            )
                            module_level_key = f"{module_path}.{imported_name}"
                            if module_level_key not in self.resolved_types:
                                self.resolved_types[module_level_key] = new_resolved

    def _extract_class_definition(self, node: ast.ClassDef, module_path: str, file_path: Path) -> ResolvedType | None:
        """
        Extract class definition from AST node

        Args:
            node (ast.ClassDef): The class definition node
            module_path (str): The module path
            file_path (Path): The file path

        Returns:
            ResolvedType | None: The resolved type or None if extraction fails
        """

        fields: dict[str, str] = {}
        methods: dict[str, str] = {}
        bases: list[str] = []

        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        is_enum = self._is_enum_class(bases)

        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    if item.annotation:
                        fields[field_name] = ast.unparse(item.annotation)

            elif isinstance(item, ast.Assign):
                if is_enum:
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            member_name = target.id
                            if not member_name.startswith("_"):
                                member_value = ast.unparse(item.value)
                                fields[member_name] = member_value

            elif isinstance(item, ast.FunctionDef):
                method_sig = self._extract_method_signature(item)
                methods[item.name] = method_sig

                if item.name == "__init__":
                    for arg in item.args.args[1:]:  # Skip 'self'
                        arg_name = arg.arg
                        if arg.annotation:
                            fields[arg_name] = ast.unparse(arg.annotation)
                        else:
                            fields[arg_name] = "Any"

                    # Also look for self.x = y assignments in __init__
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute):
                                    if isinstance(target.value, ast.Name) and target.value.id == "self":
                                        field_name = target.attr
                                        if field_name not in fields:
                                            fields[field_name] = "Any"

        return ResolvedType(
            name=node.name,
            module_path=module_path,
            file_path=file_path,
            fields=fields,
            methods=methods,
            bases=bases,
        )

    def _is_enum_class(self, bases: list[str]) -> bool:
        """
        Check if a class is an Enum based on its base classes

        Args:
            bases (list[str]): List of base class names

        Returns:
            bool: True if the class is an Enum, False otherwise
        """

        enum_types = {"Enum", "IntEnum", "Flag", "IntFlag", "StrEnum"}
        return any(base in enum_types or "Enum" in base for base in bases)

    def _extract_method_signature(self, node: ast.FunctionDef) -> str:
        """
        Extract method signature as a string

        Args:
            node (ast.FunctionDef): The function definition node

        Returns:
            str: The method signature
        """

        args = []
        for arg in node.args.args:
            if arg.annotation:
                args.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
            else:
                args.append(arg.arg)

        args_str = ", ".join(args)

        if node.returns:
            return_type = ast.unparse(node.returns)
            return f"def {node.name}({args_str}) -> {return_type}"
        else:
            return f"def {node.name}({args_str})"

    def populate_registry(self, registry: TypeRegistry) -> None:
        """
        Populate the registry with resolved types

        Args:
            registry (TypeRegistry): The registry to populate
        """

        # First pass: detect conflicts
        self._detect_type_conflicts()

        # Second pass: register types
        top_level_modules: dict[str, dict[str, TypeDefinition]] = {}

        for _, resolved in self.resolved_types.items():
            type_def = TypeDefinition(
                name=resolved.name,
                fields=resolved.fields,
                methods=resolved.methods,
                module=resolved.module_path if resolved.module_path else None,
            )

            registry.register_type(type_def)

            # Register with module for qualified access
            module_name = resolved.file_path.stem
            if module_name not in top_level_modules:
                top_level_modules[module_name] = {}
            top_level_modules[module_name][resolved.name] = type_def

            if resolved.module_path and "." not in resolved.module_path:
                if resolved.module_path not in top_level_modules:
                    top_level_modules[resolved.module_path] = {}
                top_level_modules[resolved.module_path][resolved.name] = type_def

        # Register module types
        for module_name, types in top_level_modules.items():
            registry.register_module_types(module_name, types)

        # Auto-import types that were imported in __init__.py files
        for resolved_key, resolved in self.resolved_types.items():
            # Check for top-level imports from __init__.py
            # These have a shortened module_path compared to their file location
            parts = resolved.module_path.split(".")
            if len(parts) == 1 and resolved_key == f"{resolved.module_path}.{resolved.name}":
                # This indicates a top-level import from __init__.py
                # Example: "models.User" with module_path "models" indicates it was imported in models/__init__.py
                type_def = TypeDefinition(
                    name=resolved.name,
                    fields=resolved.fields,
                    methods=resolved.methods,
                    module=resolved.module_path,
                )
                registry._imported_names[resolved.name] = type_def

        # Store conflicts in registry for later reporting
        registry.set_type_conflicts(self.type_conflicts)

    def validate_type_exists(self, type_name: str) -> bool:
        """
        Validate if a type exists in the resolved types

        Args:
            type_name (str): Name of the type to validate (can be qualified)

        Returns:
            bool: True if the type exists, False otherwise
        """

        # Always allow builtin types
        from typja.constants import PYTHON_BUILTINS, TYPING_TYPES

        if type_name in PYTHON_BUILTINS or type_name in TYPING_TYPES:
            return True

        # Handle qualified names
        if "." in type_name:
            # Look for qualified type
            for resolved_type in self.resolved_types.values():
                if resolved_type.qualified_name == type_name:
                    return True
            return False

        return type_name in self.resolved_types

    def validate_attribute(self, type_name: str, attribute: str) -> tuple[bool, str | None]:
        """
        Validate if an attribute exists on a type

        Args:
            type_name (str): Name of the type (can be qualified like 'user.User')
            attribute (str): Name of the attribute

        Returns:
            tuple[bool, str | None]: (is_valid, error_message)
        """

        # Allow access to any builtin type attributes
        if type_name in ["str", "int", "float", "bool", "list", "dict", "set", "tuple"]:
            return True, None

        resolved_type = None

        if "." in type_name:
            for rt in self.resolved_types.values():
                if rt.qualified_name == type_name:
                    resolved_type = rt
                    break
        else:
            resolved_type = self.resolved_types.get(type_name)

        if not resolved_type:
            # Check if this is a conflict case and suggest qualified names
            if type_name in self.type_conflicts:
                conflicting_types = self.type_conflicts[type_name]
                qualified_names = [rt.qualified_name for rt in conflicting_types]
                return False, (
                    f"Ambiguous type '{type_name}' found in multiple files. "
                    f"Use qualified name: {', '.join(qualified_names)} "
                    f"or import explicitly with {{# typja:from <module> import {type_name} #}}"
                )
            return False, f"Type '{type_name}' not found"

        # Check if it's a field or method
        if attribute in resolved_type.fields or attribute in resolved_type.methods:
            return True, None

        # Check common attributes that might be available on all objects
        common_attrs = {
            "__class__",
            "__dict__",
            "__doc__",
            "__module__",
            "__str__",
            "__repr__",
            "__hash__",
        }
        if attribute in common_attrs:
            return True, None

        return (
            False,
            f"Attribute '{attribute}' not found on type '{resolved_type.qualified_name}'",
        )

    def get_attribute_type(self, type_name: str, attribute: str) -> str | None:
        """
        Get the type of an attribute for a given type

        Args:
            type_name (str): Name of the type (can be qualified like 'user.User')
            attribute (str): Name of the attribute

        Returns:
            str | None: Type annotation of the attribute or None if not found
        """

        # Handle qualified names with their types first
        if "." in type_name:
            for rt in self.resolved_types.values():
                if rt.qualified_name == type_name:
                    return rt.fields.get(attribute)

        resolved_type: ResolvedType | None = self.resolved_types.get(type_name)
        if not resolved_type:
            return None

        return resolved_type.fields.get(attribute)

    def _detect_type_conflicts(self) -> None:
        """
        Detect types with the same name from different files
        """

        name_to_types: dict[str, list[ResolvedType]] = {}

        for resolved_type in self.resolved_types.values():
            if resolved_type.name not in name_to_types:
                name_to_types[resolved_type.name] = []
            name_to_types[resolved_type.name].append(resolved_type)

        # For conflicts with same name and different files, set them to be type conflicts
        for type_name, types in name_to_types.items():
            if len(types) > 1:
                file_paths = {t.file_path for t in types}
                if len(file_paths) > 1:
                    self.type_conflicts[type_name] = types

    def get_type_conflicts(self) -> dict[str, list[ResolvedType]]:
        """
        Get detected type conflicts

        Returns:
            dict[str, list[ResolvedType]]: Mapping of type names to conflicting types
        """
        return self.type_conflicts
