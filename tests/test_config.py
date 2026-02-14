from pathlib import Path

import pytest

from typja.config.loader import ConfigLoader, load_config
from typja.config.schema import (
    EnvironmentConfig,
    ErrorsConfig,
    FormattingConfig,
    LintingConfig,
    ProjectConfig,
    TypjaConfig,
)
from typja.exceptions import TypjaConfigError


class TestConfigSchema:

    def test_project_config_defaults(self):
        config = ProjectConfig()

        assert config.root == "."
        assert config.paths == []
        assert config.fail_on_warning is False

    def test_project_config_custom(self):
        config = ProjectConfig(
            root="/custom/root", paths=["./types", "./models"], fail_on_warning=True
        )
        assert config.root == "/custom/root"
        assert len(config.paths) == 2
        assert config.fail_on_warning is True

    def test_environment_config_defaults(self):
        config = EnvironmentConfig()

        assert config.jinja_env is None
        assert "./templates" in config.template_dirs
        assert "*.html" in config.include_patterns
        assert "**/node_modules/**" in config.exclude_patterns

    def test_environment_config_custom(self):

        config = EnvironmentConfig(
            jinja_env="myapp.jinja_env",
            template_dirs=["./templates", "./emails"],
            include_patterns=["*.jinja"],
            exclude_patterns=["**/dist/**"],
        )

        assert config.jinja_env == "myapp.jinja_env"
        assert len(config.template_dirs) == 2
        assert "*.jinja" in config.include_patterns

    def test_linting_config_defaults(self):
        config = LintingConfig()

        assert config.strict is False
        assert config.prefer_pep604_unions is True

    def test_typja_config_complete(self):

        project = ProjectConfig(root=".", paths=["./types"])
        environment = EnvironmentConfig()
        linting = LintingConfig()
        formatting = FormattingConfig()
        errors = ErrorsConfig()

        config = TypjaConfig(
            project=project,
            environment=environment,
            linting=linting,
            formatting=formatting,
            errors=errors,
        )

        assert config.project.root == "."
        assert config.environment.jinja_env is None
        assert config.linting.strict is False


class TestConfigLoader:

    def test_load_basic_config(self, basic_config):
        config = ConfigLoader.load(basic_config)

        assert isinstance(config, TypjaConfig)
        assert config.project.root == "."
        assert "./types" in config.project.paths
        assert config.project.fail_on_warning is False

    def test_load_full_config(self, full_config):
        config = ConfigLoader.load(full_config)

        assert config.project.root == "/custom/root"
        assert config.project.fail_on_warning is True
        assert config.environment.jinja_env == "myapp.jinja_env"
        assert len(config.environment.template_dirs) == 2
        assert config.linting.strict is True
        assert config.linting.union_style == "error"

    def test_load_minimal_config(self, minimal_config):
        config = ConfigLoader.load(minimal_config)

        assert config.project.root == "."
        assert config.linting.prefer_pep604_unions is False
        assert config.linting.union_style == "ignore"

    def test_load_nonexistent_config(self):
        with pytest.raises(TypjaConfigError):
            ConfigLoader.load("/path/that/does/not/exist.toml")

    def test_load_invalid_syntax_config(self, configs_dir):
        invalid_config = configs_dir / "invalid_syntax.toml"
        with pytest.raises(TypjaConfigError):
            ConfigLoader.load(invalid_config)

    def test_find_config_current_dir(self, tmp_path):
        config_path = tmp_path / "typja.toml"
        config_path.write_text(
            """
[project]
root = "."
"""
        )

        found = ConfigLoader.find_config(tmp_path)
        assert found == config_path

    def test_find_config_parent_dir(self, tmp_path):
        config_path = tmp_path / "typja.toml"
        config_path.write_text(
            """
[project]
root = "."
"""
        )

        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)

        found = ConfigLoader.find_config(subdir)
        assert found == config_path

    def test_find_config_not_found(self, tmp_path):

        with pytest.raises(TypjaConfigError) as exc_info:
            ConfigLoader.find_config(tmp_path)

        assert "not found" in str(exc_info.value).lower()

    def test_parse_config_dict(self):
        data = {
            "project": {"root": ".", "paths": ["./types"], "fail_on_warning": True},
            "environment": {
                "template_dirs": ["./templates"],
                "include_patterns": ["*.html"],
            },
            "linting": {"strict": True, "prefer_pep604_unions": True},
        }

        config = ConfigLoader.parse_config(data)

        assert config.project.root == "."
        assert config.project.fail_on_warning is True
        assert config.linting.strict is True

    def test_parse_config_empty_dict(self):

        config = ConfigLoader.parse_config({})
        assert config.project.root == "."
        assert config.linting.prefer_pep604_unions is True

    def test_parse_config_partial(self):
        data = {
            "project": {"root": "/custom"},
        }

        config = ConfigLoader.parse_config(data)

        assert config.project.root == "/custom"
        assert config.environment.template_dirs == ["./templates"]

    def test_load_config_helper_function(self, basic_config):
        config = load_config(basic_config)
        assert isinstance(config, TypjaConfig)
        assert config.project.root == "."

    def test_load_config_no_path(self, tmp_path, monkeypatch):
        config_path = tmp_path / "typja.toml"
        config_path.write_text(
            """
[project]
root = "."
paths = ["./types"]
"""
        )

        monkeypatch.chdir(tmp_path)
        config = load_config()
        assert config.project.root == "."

    def test_config_with_all_sections(self):
        data = {
            "project": {
                "root": ".",
                "paths": ["./types", "./models"],
                "fail_on_warning": True,
            },
            "environment": {
                "jinja_env": "app.jinja_env",
                "template_dirs": ["./templates", "./emails"],
                "include_patterns": ["*.html", "*.jinja"],
                "exclude_patterns": ["**/dist/**"],
            },
            "linting": {
                "strict": True,
                "prefer_pep604_unions": True,
                "union_style": "error",
                "fix_union_syntax": True,
                "warn_unused_imports": True,
                "warn_undefined_variables": True,
                "warn_type_mismatches": True,
                "validate_imports": True,
                "validate_filters": True,
                "validate_macros": True,
                "validate_variables": True,
                "check_missing_annotations": True,
            },
            "formatting": {"indent_size": 4, "use_tabs": False},
            "errors": {"exit_on_error": True, "max_errors": 50},
        }

        config = ConfigLoader.parse_config(data)
        assert config.project.paths == ["./types", "./models"]
        assert config.environment.jinja_env == "app.jinja_env"
        assert config.linting.strict is True
        assert config.linting.union_style == "error"

    def test_config_string_path_conversion(self, basic_config):
        config = ConfigLoader.load(str(basic_config))
        assert isinstance(config, TypjaConfig)

    def test_config_path_object(self, basic_config):
        config = ConfigLoader.load(Path(basic_config))
        assert isinstance(config, TypjaConfig)
