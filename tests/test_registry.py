import pytest

from typja.exceptions import TypjaValidationError
from typja.parser.ast import TypeAnnotation
from typja.registry import TypeDefinition, TypeRegistry


class TestTypeDefinition:

    def test_create_type_definition(self):
        type_def = TypeDefinition(
            name="User", fields={"id": "int", "name": "str"}, module="models"
        )

        assert type_def.name == "User"
        assert type_def.fields == {"id": "int", "name": "str"}
        assert type_def.module == "models"

    def test_type_definition_has_field(self):
        type_def = TypeDefinition(name="User", fields={"id": "int", "name": "str"})

        assert type_def.has_field("id") is True
        assert type_def.has_field("name") is True
        assert type_def.has_field("email") is False

    def test_type_definition_get_field_type(self):
        type_def = TypeDefinition(name="User", fields={"id": "int", "name": "str"})

        assert type_def.get_field_type("id") == "int"
        assert type_def.get_field_type("name") == "str"
        assert type_def.get_field_type("email") is None

    def test_type_definition_with_methods(self):
        type_def = TypeDefinition(
            name="User",
            fields={"id": "int"},
            methods={"greet": "def greet(self) -> str"},
        )

        assert type_def.has_method("greet") is True
        assert type_def.get_method_signature("greet") == "def greet(self) -> str"

    def test_type_definition_has_method(self):
        type_def = TypeDefinition(
            name="User", fields={}, methods={"save": "def save(self) -> None"}
        )

        assert type_def.has_method("save") is True
        assert type_def.has_method("delete") is False

    def test_type_definition_no_methods(self):
        type_def = TypeDefinition(name="User", fields={"id": "int"})

        assert type_def.methods is None
        assert type_def.has_method("anything") is False

    def test_type_definition_no_module(self):
        type_def = TypeDefinition(name="User", fields={"id": "int"})

        assert type_def.module is None


class TestTypeRegistry:

    def test_create_registry(self):
        registry = TypeRegistry()

        assert registry is not None
        assert len(registry._types) == 0

    def test_register_type(self):
        registry = TypeRegistry()
        type_def = TypeDefinition(name="User", fields={"id": "int", "name": "str"})

        registry.register_type(type_def)

        assert registry.get_type("User") == type_def

    def test_register_type_with_module(self):
        registry = TypeRegistry()
        type_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")

        registry.register_type(type_def)

        assert registry.get_type("User") == type_def
        module_types = registry.get_module_types("models")
        assert "User" in module_types

    def test_register_multiple_types(self):
        registry = TypeRegistry()

        user_def = TypeDefinition(name="User", fields={"id": "int"})
        post_def = TypeDefinition(name="Post", fields={"title": "str"})

        registry.register_type(user_def)
        registry.register_type(post_def)

        assert registry.get_type("User") == user_def
        assert registry.get_type("Post") == post_def

    def test_register_module_types(self):
        registry = TypeRegistry()

        user_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        post_def = TypeDefinition(name="Post", fields={"title": "str"}, module="models")

        registry.register_module_types("models", {"User": user_def, "Post": post_def})

        module_types = registry.get_module_types("models")
        assert "User" in module_types
        assert "Post" in module_types

    def test_import_module(self):
        registry = TypeRegistry()

        user_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_module_types("models", {"User": user_def})

        registry.import_module("models")

        assert "models" in registry._imported_modules

    def test_import_nonexistent_module(self):
        registry = TypeRegistry()

        with pytest.raises(TypjaValidationError):
            registry.import_module("nonexistent")

    def test_import_typing_module(self):
        registry = TypeRegistry()

        registry.import_module("typing")

        assert "typing" in registry._imported_modules

    def test_import_builtins_module(self):
        registry = TypeRegistry()

        registry.import_module("builtins")

        assert "builtins" in registry._imported_modules

    def test_import_from_module(self):
        registry = TypeRegistry()

        user_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_module_types("models", {"User": user_def})

        registry.import_from_module("models", [("User", None)])

        assert "User" in registry._imported_names
        assert registry._imported_names["User"] == user_def

    def test_import_from_module_with_alias(self):
        registry = TypeRegistry()

        user_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_module_types("models", {"User": user_def})

        registry.import_from_module("models", [("User", "U")])

        assert "U" in registry._imported_names
        assert registry._imported_names["U"] == user_def

    def test_import_from_typing(self):
        registry = TypeRegistry()

        registry.import_from_module("typing", [("List", None), ("Dict", None)])
        assert "List" in registry._imported_names
        assert "Dict" in registry._imported_names

    def test_resolve_type_simple(self):
        registry = TypeRegistry()
        type_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_module_types("models", {"User": type_def})
        registry.import_from_module("models", [("User", None)])

        type_annotation = TypeAnnotation(raw="User", name="User", module=None)
        resolved = registry.resolve_type(type_annotation)

        assert resolved == type_def

    def test_resolve_type_with_module(self):
        registry = TypeRegistry()
        type_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_type(type_def)
        registry.import_module("models")

        type_annotation = TypeAnnotation(
            raw="models.User", name="User", module="models"
        )
        resolved = registry.resolve_type(type_annotation)

        assert resolved == type_def

    def test_resolve_type_imported(self):
        registry = TypeRegistry()
        type_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_module_types("models", {"User": type_def})
        registry.import_from_module("models", [("User", None)])

        type_annotation = TypeAnnotation(raw="User", name="User", module=None)
        resolved = registry.resolve_type(type_annotation)

        assert resolved == type_def

    def test_resolve_type_aliased(self):
        registry = TypeRegistry()
        type_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_module_types("models", {"User": type_def})
        registry.import_from_module("models", [("User", "U")])

        type_annotation = TypeAnnotation(raw="U", name="U", module=None)
        resolved = registry.resolve_type(type_annotation)

        assert resolved == type_def

    def test_resolve_type_builtin(self):
        registry = TypeRegistry()

        type_annotation = TypeAnnotation(raw="str", name="str", module=None)
        resolved = registry.resolve_type(type_annotation)

        assert resolved is None

    def test_resolve_type_typing(self):
        registry = TypeRegistry()

        type_annotation = TypeAnnotation(raw="List", name="List", module="typing")
        resolved = registry.resolve_type(type_annotation)

        assert resolved is None

    def test_is_builtin(self):
        registry = TypeRegistry()

        assert registry.is_builtin("str") is True
        assert registry.is_builtin("int") is True
        assert registry.is_builtin("list") is True
        assert registry.is_builtin("User") is False

    def test_get_type_nonexistent(self):
        registry = TypeRegistry()

        assert registry.get_type("NonExistent") is None

    def test_get_module_types_nonexistent(self):
        registry = TypeRegistry()

        module_types = registry.get_module_types("nonexistent")
        assert module_types == {}

    def test_clear_imports(self):
        registry = TypeRegistry()

        user_def = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        registry.register_module_types("models", {"User": user_def})
        registry.import_from_module("models", [("User", None)])
        registry.import_module("models")

        assert len(registry._imported_names) > 0
        assert len(registry._imported_modules) > 0

        registry.clear_imports()

        assert len(registry._imported_names) == 0
        assert len(registry._imported_modules) == 0

    def test_multiple_imports_same_name(self):
        registry = TypeRegistry()

        user_def1 = TypeDefinition(name="User", fields={"id": "int"}, module="models")
        user_def2 = TypeDefinition(name="User", fields={"name": "str"}, module="admin")

        registry.register_module_types("models", {"User": user_def1})
        registry.register_module_types("admin", {"User": user_def2})

        registry.import_from_module("models", [("User", None)])
        registry.import_from_module("admin", [("User", None)])

        assert registry._imported_names["User"] == user_def2

    def test_registry_with_complex_types(self):
        registry = TypeRegistry()

        user_def = TypeDefinition(
            name="User",
            fields={
                "id": "int",
                "name": "str",
                "email": "str",
                "posts": "List[Post]",
            },
            methods={"save": "def save(self) -> None"},
            module="models",
        )

        registry.register_type(user_def)

        assert registry.get_type("User") == user_def
        assert user_def.has_field("posts")
        assert user_def.has_method("save")

    def test_registry_type_override(self):
        registry = TypeRegistry()

        user_def1 = TypeDefinition(name="User", fields={"id": "int"})
        user_def2 = TypeDefinition(name="User", fields={"name": "str"})

        registry.register_type(user_def1)
        registry.register_type(user_def2)

        assert registry.get_type("User") is not None
        assert registry.get_type("User") == user_def2
        assert registry.get_type("User").has_field("name")  # type: ignore
        assert not registry.get_type("User").has_field("id")  # type: ignore
