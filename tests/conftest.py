from pathlib import Path


import pytest

@pytest.fixture
def test_data_dir():
    """Return path to test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture
def templates_dir(test_data_dir):
    """Return path to test templates directory"""
    return test_data_dir / "templates"


@pytest.fixture
def configs_dir(test_data_dir):
    """Return path to test configs directory"""
    return test_data_dir / "configs"


@pytest.fixture
def valid_templates_dir(templates_dir):
    """Return path to valid templates directory"""
    return templates_dir / "valid"


@pytest.fixture
def invalid_templates_dir(templates_dir):
    """Return path to invalid templates directory"""
    return templates_dir / "invalid"


@pytest.fixture
def sample_template_simple(valid_templates_dir):
    """Load simple template with basic type annotations"""
    template_path = valid_templates_dir / "simple_vars.html"
    return template_path.read_text()


@pytest.fixture
def sample_template_with_imports(valid_templates_dir):
    """Load template with import statements"""
    template_path = valid_templates_dir / "with_imports.html"
    return template_path.read_text()


@pytest.fixture
def sample_template_union_types(valid_templates_dir):
    """Load template with union types"""
    template_path = valid_templates_dir / "union_types.html"
    return template_path.read_text()


@pytest.fixture
def basic_config(configs_dir):
    """Return path to basic config"""
    return configs_dir / "basic_config.toml"


@pytest.fixture
def full_config(configs_dir):
    """Return path to full config"""
    return configs_dir / "full_config.toml"


@pytest.fixture
def minimal_config(configs_dir):
    """Return path to minimal config"""
    return configs_dir / "minimal_config.toml"
