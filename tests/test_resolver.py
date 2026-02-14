from typja.parser.ast import TypeAnnotation
from typja.registry import TypeRegistry
from typja.resolver import TypeResolver


class TestTypeResolver:

    def test_create_resolver(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        assert resolver.root == test_data_dir
        assert len(resolver.resolved_types) == 0

    def test_resolve_single_file(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"

        resolver.resolve_paths([user_file])

        assert "User" in resolver.resolved_types
        user_type = resolver.resolved_types["User"]
        assert user_type.name == "User"
        assert "id" in user_type.fields
        assert "name" in user_type.fields
        assert "greet" in user_type.methods

    def test_resolve_directory(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        types_dir = test_data_dir / "types"

        resolver.resolve_paths([types_dir])

        assert "User" in resolver.resolved_types
        assert "Post" in resolver.resolved_types
        assert "Comment" in resolver.resolved_types

    def test_resolve_nested_directory(self, test_data_dir):
        """Test resolving types from nested directories"""
        resolver = TypeResolver(test_data_dir)
        types_dir = test_data_dir / "types"

        resolver.resolve_paths([types_dir])

        assert "NestedClass" in resolver.resolved_types

    def test_resolved_type_fields(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"

        resolver.resolve_paths([user_file])

        user_type = resolver.resolved_types["User"]
        assert user_type.fields["id"] == "int"
        assert user_type.fields["name"] == "str"
        assert user_type.fields["email"] == "str"
        assert "active" in user_type.fields

    def test_resolved_type_methods(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"

        resolver.resolve_paths([user_file])

        user_type = resolver.resolved_types["User"]
        assert "greet" in user_type.methods
        assert "save" in user_type.methods
        assert "-> str" in user_type.methods["greet"]
        assert "-> None" in user_type.methods["save"]

    def test_resolved_type_module_path(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"

        resolver.resolve_paths([user_file])

        user_type = resolver.resolved_types["User"]
        assert (
            "types.classes_types" in user_type.module_path
            or user_type.module_path == "types.classes_types"
        )

    def test_resolve_class_with_annotations(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        classes_file = test_data_dir / "types" / "classes_types.py"

        resolver.resolve_paths([classes_file])

        post_type = resolver.resolved_types["Post"]
        assert "title" in post_type.fields
        assert post_type.fields["title"] == "str"
        assert "tags" in post_type.fields

    def test_resolve_class_without_annotations(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        no_ann_file = test_data_dir / "types" / "old_classes_types.py"

        resolver.resolve_paths([no_ann_file])

        old_style = resolver.resolved_types["OldStyleClass"]
        assert "name" in old_style.fields
        assert old_style.fields["name"] == "Any"

    def test_resolve_multiple_classes_same_file(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        classes_file = test_data_dir / "types" / "classes_types.py"

        resolver.resolve_paths([classes_file])

        assert "Post" in resolver.resolved_types
        assert "Comment" in resolver.resolved_types
        assert "BaseModel" in resolver.resolved_types

    def test_resolve_with_exclude_patterns(self, test_data_dir):
        resolver = TypeResolver(test_data_dir, exclude_patterns=["**/subdir/**"])
        types_dir = test_data_dir / "types"

        resolver.resolve_paths([types_dir])

        assert "NestedClass" not in resolver.resolved_types
        assert "User" in resolver.resolved_types

    def test_validate_type_exists(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        assert resolver.validate_type_exists("User") is True
        assert resolver.validate_type_exists("NonExistent") is False

    def test_validate_attribute_exists(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        is_valid, error = resolver.validate_attribute("User", "name")
        assert is_valid is True
        assert error is None

    def test_validate_attribute_not_exists(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        is_valid, error = resolver.validate_attribute("User", "nonexistent")
        assert is_valid is False

        if error:
            assert "not found" in error.lower()

    def test_validate_attribute_type_not_exists(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        is_valid, error = resolver.validate_attribute("NonExistent", "field")
        assert is_valid is False

        if error:
            assert "not found" in error.lower()

    def test_validate_method_as_attribute(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        is_valid, error = resolver.validate_attribute("User", "greet")
        assert is_valid is True

    def test_get_attribute_type(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        attr_type = resolver.get_attribute_type("User", "name")
        assert attr_type == "str"

    def test_get_attribute_type_not_found(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        attr_type = resolver.get_attribute_type("User", "nonexistent")
        assert attr_type is None

    def test_get_attribute_type_nonexistent_class(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        attr_type = resolver.get_attribute_type("NonExistent", "field")
        assert attr_type is None

    def test_populate_registry(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        registry = TypeRegistry()
        resolver.populate_registry(registry)

        user_type = registry.get_type("User")
        assert user_type is not None
        assert user_type.name == "User"
        assert user_type.has_field("name")

    def test_populate_registry_multiple_types(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        types_dir = test_data_dir / "types"
        resolver.resolve_paths([types_dir])

        registry = TypeRegistry()
        resolver.populate_registry(registry)

        assert registry.get_type("User") is not None
        assert registry.get_type("Post") is not None
        assert registry.get_type("Comment") is not None

    def test_resolve_nonexistent_path(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        nonexistent = test_data_dir / "nonexistent.py"

        resolver.resolve_paths([nonexistent])

        assert len(resolver.resolved_types) == 0

    def test_resolve_invalid_python_file(self, tmp_path):
        resolver = TypeResolver(tmp_path)
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("this is not valid python {{{")

        resolver.resolve_paths([invalid_file])

        assert len(resolver.resolved_types) == 0

    def test_resolve_empty_file(self, tmp_path):
        resolver = TypeResolver(tmp_path)
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        resolver.resolve_paths([empty_file])

        assert len(resolver.resolved_types) == 0

    def test_resolve_file_without_classes(self, tmp_path):
        resolver = TypeResolver(tmp_path)
        no_class_file = tmp_path / "noclass.py"
        no_class_file.write_text("def function():\n    pass\n")

        resolver.resolve_paths([no_class_file])

        assert len(resolver.resolved_types) == 0

    def test_resolved_type_qualified_name(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        assert "User" in resolver.resolved_types

        qualified_names = [
            key
            for key in resolver.resolved_types.keys()
            if "." in key and "User" in key
        ]
        assert len(qualified_names) > 0

    def test_resolve_class_with_inheritance(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        classes_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([classes_file])

        base_model = resolver.resolved_types.get("BaseModel")
        if base_model:
            assert base_model.name == "BaseModel"

    def test_validate_common_attributes(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        user_file = test_data_dir / "types" / "classes_types.py"
        resolver.resolve_paths([user_file])

        is_valid, _ = resolver.validate_attribute("User", "__class__")
        assert is_valid is True

        is_valid, _ = resolver.validate_attribute("User", "__dict__")
        assert is_valid is True

    def test_should_skip_file(self, test_data_dir):
        resolver = TypeResolver(
            test_data_dir, exclude_patterns=["**/subdir/**", "**/__pycache__/**"]
        )

        subdir_file = test_data_dir / "types" / "subdir" / "nested.py"
        assert resolver._should_skip_file(subdir_file) is True

        user_file = test_data_dir / "types" / "classes_types.py"
        assert resolver._should_skip_file(user_file) is False

    def test_resolve_str_enum(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        enum_file = test_data_dir / "types" / "enum_types.py"

        resolver.resolve_paths([enum_file])

        assert "Status" in resolver.resolved_types
        status_type = resolver.resolved_types["Status"]
        assert status_type.name == "Status"
        assert "Enum" in status_type.bases or "str" in status_type.bases

    def test_resolve_int_enum(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        enum_file = test_data_dir / "types" / "enum_types.py"

        resolver.resolve_paths([enum_file])

        assert "Priority" in resolver.resolved_types
        priority_type = resolver.resolved_types["Priority"]
        assert priority_type.name == "Priority"
        assert "IntEnum" in priority_type.bases

    def test_enum_has_members_as_fields(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        enum_file = test_data_dir / "types" / "enum_types.py"

        resolver.resolve_paths([enum_file])

        status_type = resolver.resolved_types["Status"]
        assert "ACTIVE" in status_type.fields
        assert "INACTIVE" in status_type.fields
        assert "PENDING" in status_type.fields

    def test_enum_member_values(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        enum_file = test_data_dir / "types" / "enum_types.py"

        resolver.resolve_paths([enum_file])

        status_type = resolver.resolved_types["Status"]
        assert status_type.fields["ACTIVE"] in ['"active"', "'active'"]

        priority_type = resolver.resolved_types["Priority"]
        assert priority_type.fields["LOW"] == "1"

    def test_resolve_multiple_enum_types(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        enum_file = test_data_dir / "types" / "enum_types.py"

        resolver.resolve_paths([enum_file])

        assert "Status" in resolver.resolved_types
        assert "Priority" in resolver.resolved_types
        assert "Color" in resolver.resolved_types

    def test_resolve_dataclass(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        dataclass_file = test_data_dir / "types" / "dataclasses_types.py"

        resolver.resolve_paths([dataclass_file])

        assert "Product" in resolver.resolved_types
        product_type = resolver.resolved_types["Product"]
        assert product_type.name == "Product"

    def test_dataclass_fields(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        dataclass_file = test_data_dir / "types" / "dataclasses_types.py"

        resolver.resolve_paths([dataclass_file])

        product_type = resolver.resolved_types["Product"]
        assert "id" in product_type.fields
        assert "name" in product_type.fields
        assert "price" in product_type.fields
        assert "description" in product_type.fields
        assert "tags" in product_type.fields

        assert product_type.fields["id"] == "int"
        assert product_type.fields["name"] == "str"
        assert product_type.fields["price"] == "float"

    def test_dataclass_with_methods(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        dataclass_file = test_data_dir / "types" / "dataclasses_types.py"

        resolver.resolve_paths([dataclass_file])

        product_type = resolver.resolved_types["Product"]
        assert "discount" in product_type.methods
        assert "-> float" in product_type.methods["discount"]

    def test_dataclass_with_defaults(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        dataclass_file = test_data_dir / "types" / "dataclasses_types.py"

        resolver.resolve_paths([dataclass_file])

        product_type = resolver.resolved_types["Product"]
        assert "description" in product_type.fields
        assert product_type.fields["description"] == "str"

    def test_frozen_dataclass(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        dataclass_file = test_data_dir / "types" / "dataclasses_types.py"

        resolver.resolve_paths([dataclass_file])

        assert "Point" in resolver.resolved_types
        point_type = resolver.resolved_types["Point"]
        assert "x" in point_type.fields
        assert "y" in point_type.fields

    def test_nested_dataclass(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        dataclass_file = test_data_dir / "types" / "dataclasses_types.py"

        resolver.resolve_paths([dataclass_file])

        order_type = resolver.resolved_types["Order"]
        assert "product" in order_type.fields
        assert "Product" in order_type.fields["product"]

    def test_resolve_typeddict(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        typeddict_file = test_data_dir / "types" / "typeddict_types.py"

        resolver.resolve_paths([typeddict_file])

        assert "UserDict" in resolver.resolved_types
        user_dict_type = resolver.resolved_types["UserDict"]
        assert user_dict_type.name == "UserDict"

    def test_typeddict_fields(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        typeddict_file = test_data_dir / "types" / "typeddict_types.py"

        resolver.resolve_paths([typeddict_file])

        user_dict_type = resolver.resolved_types["UserDict"]
        assert "id" in user_dict_type.fields
        assert "name" in user_dict_type.fields
        assert "email" in user_dict_type.fields
        assert "active" in user_dict_type.fields

        assert user_dict_type.fields["id"] == "int"
        assert user_dict_type.fields["name"] == "str"

    def test_typeddict_with_total_false(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        typeddict_file = test_data_dir / "types" / "typeddict_types.py"

        resolver.resolve_paths([typeddict_file])

        assert "ProductDict" in resolver.resolved_types
        product_dict_type = resolver.resolved_types["ProductDict"]
        assert "id" in product_dict_type.fields
        assert "name" in product_dict_type.fields
        assert "price" in product_dict_type.fields

    def test_typeddict_with_notrequired(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        typeddict_file = test_data_dir / "types" / "typeddict_types.py"

        resolver.resolve_paths([typeddict_file])

        person_dict_type = resolver.resolved_types["PersonDict"]
        assert "name" in person_dict_type.fields
        assert "age" in person_dict_type.fields
        assert "email" in person_dict_type.fields

    def test_multiple_typeddicts(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        typeddict_file = test_data_dir / "types" / "typeddict_types.py"

        resolver.resolve_paths([typeddict_file])

        assert "UserDict" in resolver.resolved_types
        assert "ProductDict" in resolver.resolved_types
        assert "PersonDict" in resolver.resolved_types

    def test_resolve_pydantic_model(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        pydantic_file = test_data_dir / "types" / "pydantic_types.py"

        resolver.resolve_paths([pydantic_file])

        assert "Account" in resolver.resolved_types
        account_type = resolver.resolved_types["Account"]
        assert account_type.name == "Account"

    def test_pydantic_model_fields(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        pydantic_file = test_data_dir / "types" / "pydantic_types.py"

        resolver.resolve_paths([pydantic_file])

        account_type = resolver.resolved_types["Account"]
        assert "id" in account_type.fields
        assert "username" in account_type.fields
        assert "email" in account_type.fields
        assert "balance" in account_type.fields
        assert "is_active" in account_type.fields

        assert account_type.fields["id"] == "int"
        assert account_type.fields["username"] == "str"

    def test_pydantic_model_with_methods(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        pydantic_file = test_data_dir / "types" / "pydantic_types.py"

        resolver.resolve_paths([pydantic_file])

        account_type = resolver.resolved_types["Account"]
        assert "deposit" in account_type.methods

    def test_pydantic_model_inheritance(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        pydantic_file = test_data_dir / "types" / "pydantic_types.py"

        resolver.resolve_paths([pydantic_file])

        account_type = resolver.resolved_types["Account"]
        assert "BaseModel" in account_type.bases

    def test_multiple_pydantic_types(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        pydantic_file = test_data_dir / "types" / "pydantic_types.py"

        resolver.resolve_paths([pydantic_file])

        assert "Account" in resolver.resolved_types
        assert "Person" in resolver.resolved_types

    def test_pydantic_with_field_validators(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        pydantic_file = test_data_dir / "types" / "pydantic_types.py"

        resolver.resolve_paths([pydantic_file])

        person_type = resolver.resolved_types["Person"]
        assert "name" in person_type.fields
        assert "age" in person_type.fields
        assert "email" in person_type.fields

    def test_resolve_all_type_variants(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        types_dir = test_data_dir / "types"

        resolver.resolve_paths([types_dir])

        assert "User" in resolver.resolved_types

        assert "Status" in resolver.resolved_types
        assert "Priority" in resolver.resolved_types

        assert "Product" in resolver.resolved_types
        assert "Order" in resolver.resolved_types

        assert "UserDict" in resolver.resolved_types

        assert "Account" in resolver.resolved_types

    def test_populate_registry_with_all_types(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        types_dir = test_data_dir / "types"
        resolver.resolve_paths([types_dir])

        registry = TypeRegistry()
        resolver.populate_registry(registry)

        assert registry.get_type("User") is not None
        assert registry.get_type("Status") is not None
        assert registry.get_type("Product") is not None
        assert registry.get_type("UserDict") is not None
        assert registry.get_type("Account") is not None

    def test_validate_enum_member(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        enum_file = test_data_dir / "types" / "enum_types.py"
        resolver.resolve_paths([enum_file])

        is_valid, error = resolver.validate_attribute("Status", "ACTIVE")
        assert is_valid is True
        assert error is None

    def test_get_enum_member_type(self, test_data_dir):
        resolver = TypeResolver(test_data_dir)
        enum_file = test_data_dir / "types" / "enum_types.py"
        resolver.resolve_paths([enum_file])

        attr_type = resolver.get_attribute_type("Status", "ACTIVE")
        assert attr_type is not None

    def test_resolve_init_imports(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        user_file = models_dir / "user.py"
        user_file.write_text(
            """
class User:
    id: int
    name: str

class Profile:
    bio: str
    user_id: int
"""
        )

        init_file = models_dir / "__init__.py"
        init_file.write_text("from .user import User, Profile\n")

        resolver = TypeResolver(tmp_path)
        resolver.resolve_paths([models_dir])

        assert "User" in resolver.resolved_types
        assert "Profile" in resolver.resolved_types

        assert "models.user.User" in resolver.resolved_types
        assert "models.User" in resolver.resolved_types

        models_user = resolver.resolved_types["models.User"]
        assert models_user.module_path == "models"
        assert models_user.name == "User"

    def test_resolve_init_imports_in_registry(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        user_file = models_dir / "user.py"
        user_file.write_text(
            """
class User:
    id: int
    name: str
"""
        )

        init_file = models_dir / "__init__.py"
        init_file.write_text("from .user import User\n")

        resolver = TypeResolver(tmp_path)
        resolver.resolve_paths([models_dir])

        registry = TypeRegistry()
        resolver.populate_registry(registry)

        registry.import_from_module("models", [("User", None)])

        assert "User" in registry._imported_names

    def test_auto_import_from_top_level_module(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        user_file = models_dir / "user.py"
        user_file.write_text(
            """
class User:
    id: int
    name: str
"""
        )

        init_file = models_dir / "__init__.py"
        init_file.write_text("from .user import User\n")

        resolver = TypeResolver(tmp_path)
        resolver.resolve_paths([models_dir])

        registry = TypeRegistry()
        resolver.populate_registry(registry)

        user_annotation = TypeAnnotation(raw="User", name="User")

        assert "User" in registry._imported_names
        assert registry._imported_names["User"] is not None
        assert registry._imported_names["User"].name == "User"

        resolved = registry.resolve_type(user_annotation)
        assert resolved is not None or "User" in registry._imported_names
