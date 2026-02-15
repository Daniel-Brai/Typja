# Contributing to Typja

Thank you for your interest in contributing to Typja. This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in your interactions with other contributors.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/Daniel-Brai/Typja.git typja
cd typja
```

1. Add the upstream repository as a remote:

```bash
git remote add upstream https://github.com/Daniel-Brai/Typja.git
```

## Development Setup

### Using uv (Recommended)

```bash
# Install development dependencies
make install-dev

# Or manually
uv sync --all-groups
```

### Using pip

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Run tests to ensure everything is set up correctly
make test

# Or
pytest
```

## Project Structure

```text
typja/
├── src/typja/           # Main package source code
│   ├── __init__.py
│   ├── analyzer.py      # Template analysis and validation
│   ├── linter.py        # Linting rules and auto-fixes
│   ├── registry.py      # Type registry for managing types
│   ├── reporter.py      # Error reporting and formatting
│   ├── resolver.py      # Type resolution from Python files
│   ├── cli/             # Command-line interface
│   │   ├── app.py
│   │   ├── check.py
│   │   ├── init.py
│   │   └── watch.py
│   ├── config/          # Configuration handling
│   │   ├── defaults.py
│   │   ├── loader.py
│   │   └── schema.py
│   └── parser/          # Jinja2 template parsing
│       ├── ast.py
│       ├── comment.py
│       ├── imports.py
│       └── type.py
├── tests/               # Test suite
│   ├── test_analyzer.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_linter.py
│   ├── test_parser.py
│   ├── test_registry.py
│   ├── test_reporter.py
│   ├── test_resolver.py
│   └── data/            # Test fixtures
├── examples/            # Example projects
│   └── fastapi/
├── docs/                # Documentation
├── scripts/             # Build and release scripts
└── pyproject.toml       # Project configuration
```

## Development Workflow

### Creating a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a new feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes in the appropriate files
2. Add tests for any new functionality
3. Update documentation as needed
4. Run tests to ensure nothing breaks
5. Commit your changes with clear, descriptive messages

### Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, missing semicolons, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Examples:**

```bash
feat(resolver): add support for TypedDict types
fix(linter): handle union syntax in nested types
docs(readme): update installation instructions
test(cli): add e2e tests for watch command
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test_cov

# Run specific test file
pytest tests/test_resolver.py

# Run specific test
pytest tests/test_resolver.py::TestTypeResolver::test_resolve_enum

# Run tests in verbose mode
pytest -v

# Run tests and stop at first failure
pytest -x
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Use descriptive test names that explain what is being tested
- Group related tests in classes
- Use fixtures for common setup (see `tests/conftest.py`)

**Test Structure Example:**

```python
class TestFeatureName:

    def test_basic_functionality(self):
        # Arrange
        input_data = ...

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_output

    def test_edge_case(self):
        # Test implementation
```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for all function signatures
- Maximum line length: 120 characters
- Use docstrings for all public modules, classes, and functions

### Type Hints

```python
def process_template(
    content: str,
    template_path: Path,
    strict: bool = False
) -> list[ValidationIssue]:
    """
    Process a template and return validation issues

    Args:
        content (str): Template content as string
        template_path (Path): Path to the template file
        strict (bool): Whether to enable strict mode (defaults to False)

    Returns:
        List[ValidationIssue]: List of validation issues found
    """
    ...
```

### Docstring Format

Use Google-style docstrings:

```python
class TypeRegistry:
    """
    Registry for managing type definitions and imports

    This class maintains a mapping of type names to their definitions and handles import resolution for templates
    """
```

### Code Formatting

The project uses standard Python formatting. Before committing:

1. Ensure your code follows PEP 8
2. Remove unused imports
3. Keep functions focused and concise
4. Add comments for complex logic

## Submitting Changes

### Pull Request Process

1. **Update your branch** with the latest upstream changes:

```bash
git fetch upstream
git rebase upstream/main
```

1. **Push your changes** to your fork:

```bash
git push origin feature/your-feature-name
```

1. **Create a Pull Request** on GitHub:
   - Go to the main repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template
   - Submit the PR

### PR Requirements

Before submitting, ensure:

- ✅ All tests pass (`make test`)
- ✅ Code follows project style guidelines
- ✅ New features have tests
- ✅ Documentation is updated
- ✅ Commit messages are clear and descriptive
- ✅ PR description explains the changes

### Review Process

1. A maintainer will review your PR
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR
4. Your changes will be included in the next release

## Reporting Bugs

### Before Reporting

- Check existing issues to avoid duplicates
- Test with the latest version
- Gather relevant information:
  - Typja version (`typja --version`)
  - Python version
  - Operating system
  - Minimal reproduction example

### Bug Report Template

```markdown
**Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Create template with '...'
2. Run command '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- Typja version: X.Y.Z
- Python version: 3.X.Y
- OS: [e.g., Ubuntu 22.04, macOS 13, Windows 11]

**Additional Context**
Any other relevant information.
```

## Suggesting Enhancements

### Enhancement Proposal Template

```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches you've considered.

**Additional Context**
Any other relevant information.
```

## Development Tips

### Debugging

```python
# Use pytest's -s flag to see print statements
pytest -s tests/test_file.py

# Use breakpoint() for debugging
def my_function():
    breakpoint()  # Execution will pause here
    ...
```

### Testing Templates

Create test templates in `tests/data/templates/`:

```jinja2
{# typja:var user: User #}
<h1>{{ user.name }}</h1>
```

### Working with AST

When working with Python AST parsing:

```python
import ast

tree = ast.parse(source_code)
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        print(f"Found class: {node.name}")
```

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/Daniel-Brai/Typja/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/Daniel-Brai/Typja/issues)

## License

By contributing to Typja, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Typja!
