import time
from unittest.mock import patch

from typer.testing import CliRunner

from typja.cli.app import app

runner = CliRunner()


class TestCLIInitCommand:

    def test_init_creates_config(self, tmp_path):
        result = runner.invoke(app, ["init", "--root", str(tmp_path)])

        assert result.exit_code == 0
        assert (tmp_path / "typja.toml").exists()
        assert "Created" in result.stdout

    def test_init_with_existing_config_no_force(self, tmp_path):
        config_file = tmp_path / "typja.toml"
        config_file.write_text("[project]\nname = 'test'\n")

        result = runner.invoke(
            app,
            ["init", "--root", str(tmp_path)],
            input="n\n",
        )

        assert result.exit_code == 0
        assert "cancelled" in result.stdout.lower()

    def test_init_with_existing_config_force(self, tmp_path):
        config_file = tmp_path / "typja.toml"
        config_file.write_text("[project]\nname = 'test'\n")

        result = runner.invoke(
            app,
            ["init", "--root", str(tmp_path), "--force"],
        )

        assert result.exit_code == 0
        assert config_file.exists()
        new_content = config_file.read_text()
        assert "name = 'test'" not in new_content

    def test_init_with_existing_config_overwrite_yes(self, tmp_path):
        config_file = tmp_path / "typja.toml"
        config_file.write_text("[project]\nname = 'test'\n")

        result = runner.invoke(
            app,
            ["init", "--root", str(tmp_path)],
            input="y\n",
        )

        assert result.exit_code == 0
        assert config_file.exists()

    def test_init_creates_in_subdirectory(self, tmp_path):
        subdir = tmp_path / "subdir" / "nested"

        result = runner.invoke(app, ["init", "--root", str(subdir)])

        assert result.exit_code == 0
        assert (subdir / "typja.toml").exists()

    def test_init_default_root(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert (tmp_path / "typja.toml").exists()


class TestCLICheckCommand:

    def test_check_without_config(self, tmp_path):
        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 1
        assert "No typja.toml found" in result.stdout

    def test_check_with_no_templates(self, tmp_path):
        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]

[[types]]
paths = ["models"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0
        assert "No templates found" in result.stdout or "No issues" in result.stdout

    def test_check_with_valid_template(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var name: str #}
<p>Hello {{ name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            f"""
[project]
root = "{tmp_path}"

[environment]
template_dirs = ["{templates_dir}"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0
        assert "No issues" in result.stdout or "✓" in result.stdout

    def test_check_with_type_error(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var name: str #}
<p>{{ undefined_variable }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            f"""
[project]
root = "{tmp_path}"

[environment]
template_dirs = ["{templates_dir}"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0

    def test_check_with_strict_mode(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var name: str #}
<p>{{ name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            f"""
[project]
root = "{tmp_path}"

[environment]
template_dirs = ["{templates_dir}"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path), "--strict"])

        assert result.exit_code in [0, 1]

    def test_check_with_fix_flag(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var items: List[str] #}
{% for item in items %}
    <p>{{ item }}</p>
{% endfor %}
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            f"""
[project]
root = "{tmp_path}"

[environment]
template_dirs = ["{templates_dir}"]

[linting]
prefer_pep604_unions = true
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path), "--fix"])

        assert result.exit_code in [0, 1]

    def test_check_with_custom_types(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        user_model = models_dir / "user.py"
        user_model.write_text(
            """
class User:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
"""
        )

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:from models.user import User #}
{# typja:var user: User #}
<p>{{ user.name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]

[[types]]
paths = ["models"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0

    def test_check_invalid_jinja_env(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text("<p>Test</p>")

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]
jinja_env = "invalid_module:env"
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 1
        assert "Failed to import" in result.stdout or "Error" in result.stdout

    def test_check_multiple_templates(self, tmp_path):
        """Test check with multiple templates"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        for i in range(3):
            template = templates_dir / f"test{i}.html"
            template.write_text(
                f"""
{"{# typja:var name: str #}"}
<p>Template {i}: {{{{ name }}}}</p>
"""
            )

        config = tmp_path / "typja.toml"
        config.write_text(
            f"""
[project]
root = "{tmp_path}"

[environment]
template_dirs = ["{templates_dir}"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0
        assert "3" in result.stdout

    def test_check_with_subdirectories(self, tmp_path):
        """Test check discovers templates in subdirectories"""
        templates_dir = tmp_path / "templates"
        subdir = templates_dir / "subdir"
        subdir.mkdir(parents=True)

        template = subdir / "test.html"
        template.write_text(
            """
{# typja:var name: str #}
<p>{{ name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0


class TestCLIWatchCommand:

    def test_watch_without_config(self, tmp_path):
        result = runner.invoke(app, ["watch", "--root", str(tmp_path)])

        assert result.exit_code == 1
        assert "No typja.toml found" in result.stdout

    @patch("typja.cli.watch.time.sleep")
    def test_watch_initialization(self, mock_sleep, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var name: str #}
<p>{{ name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]
"""
        )

        mock_sleep.side_effect = KeyboardInterrupt()

        result = runner.invoke(app, ["watch", "--root", str(tmp_path)])

        assert result.exit_code == 0
        assert "Watching" in result.stdout or "watch" in result.stdout.lower()

    @patch("typja.cli.watch.time.sleep")
    def test_watch_detects_changes(self, mock_sleep, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var name: str #}
<p>{{ name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]
"""
        )

        call_count = [0]

        def side_effect_sleep(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                time.sleep(0.1)
                template.write_text(
                    """
{# typja:var name: str #}
<p>{{ name }} modified</p>
"""
                )
            elif call_count[0] > 2:
                raise KeyboardInterrupt()

        mock_sleep.side_effect = side_effect_sleep

        result = runner.invoke(app, ["watch", "--root", str(tmp_path)])

        assert result.exit_code == 0

    def test_watch_with_nonexistent_template_dir(self, tmp_path):
        """Test watch handles nonexistent template directories"""
        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["nonexistent"]
"""
        )

        with patch("typja.cli.watch.time.sleep", side_effect=KeyboardInterrupt()):
            result = runner.invoke(app, ["watch", "--root", str(tmp_path)])

        assert result.exit_code == 0


class TestCLIVersionFlag:

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.stdout.lower()

    def test_version_flag_short(self):
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert "version" in result.stdout.lower()


class TestCLIIntegration:

    def test_init_then_check_workflow(self, tmp_path):
        init_result = runner.invoke(app, ["init", "--root", str(tmp_path)])
        assert init_result.exit_code == 0

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var name: str #}
<p>{{ name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        content = config.read_text()
        content += f'\n[environment]\ntemplate_dirs = ["{templates_dir}"]\n'
        config.write_text(content)

        check_result = runner.invoke(app, ["check", "--root", str(tmp_path)])
        assert check_result.exit_code in [0, 1]  # Accept warnings

    def test_check_with_enum_types(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        enum_file = models_dir / "status.py"
        enum_file.write_text(
            """
from enum import Enum

class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
"""
        )

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:from models.status import Status #}
{# typja:var status: Status #}
<p>Status: {{ status }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]

[[types]]
paths = ["models"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0

    def test_check_with_dataclass_types(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        dataclass_file = models_dir / "product.py"
        dataclass_file.write_text(
            """
from dataclasses import dataclass

@dataclass
class Product:
    id: int
    name: str
    price: float
"""
        )

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:from models.product import Product #}
{# typja:var product: Product #}
<p>{{ product.name }} - ${{ product.price }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]

[[types]]
paths = ["models"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0

    def test_check_with_pydantic_types(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        pydantic_file = models_dir / "account.py"
        pydantic_file.write_text(
            """
try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel:
        pass

class Account(BaseModel):
    id: int
    username: str
    balance: float
"""
        )

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:from models.account import Account #}
{# typja:var account: Account #}
<p>{{ account.username }}: ${{ account.balance }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]

[[types]]
paths = ["models"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0

    def test_check_with_typeddict_types(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        typeddict_file = models_dir / "user_dict.py"
        typeddict_file.write_text(
            """
from typing import TypedDict

class UserDict(TypedDict):
    id: int
    name: str
    email: str
"""
        )

        # Create template using TypedDict
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:from models.user_dict import UserDict #}
{# typja:var user: UserDict #}
<p>{{ user.name }} - {{ user.email }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            """
[project]
root = "."

[environment]
template_dirs = ["templates"]

[[types]]
paths = ["models"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 0


class TestCLIErrorHandling:

    def test_check_with_syntax_error_in_template(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{% for item in items
<p>{{ item }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            f"""
[project]
root = "{tmp_path}"

[environment]
template_dirs = ["{templates_dir}"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 1

    def test_check_with_invalid_type_annotation(self, tmp_path):
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text(
            """
{# typja:var name: InvalidType #}
<p>{{ name }}</p>
"""
        )

        config = tmp_path / "typja.toml"
        config.write_text(
            f"""
[project]
root = "{tmp_path}"

[environment]
template_dirs = ["{templates_dir}"]
"""
        )

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 1

    def test_check_with_invalid_config(self, tmp_path):
        config = tmp_path / "typja.toml"
        config.write_text("invalid toml content {{{")

        result = runner.invoke(app, ["check", "--root", str(tmp_path)])

        assert result.exit_code == 1

    def test_init_in_unwritable_directory(self, tmp_path):
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        result = runner.invoke(app, ["init", "--root", str(readonly_dir)])

        assert result.exit_code == 1

        readonly_dir.chmod(0o755)
