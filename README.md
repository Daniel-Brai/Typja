# Typja

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Build and Test Typja](https://github.com/Daniel-Brai/Typja/actions/workflows/ci.yml/badge.svg)](https://github.com/Daniel-Brai/Typja/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Daniel-Brai/Typja/branch/main/graph/badge.svg)](https://codecov.io/gh/Daniel-Brai/Typja)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An experimental tool to check Jinja templates for type errors using Python's type hints. It parses Jinja templates, extracts variable usage, and checks them against provided type information.

## Features

- **Type Checking for Jinja2 Templates**: Validate that variables in your Jinja2 templates match their declared types
- **Python Type Hints Integration**: Leverage your existing Python type annotations to catch template errors early
- **Pre-commit Integration**: Built-in pre-commit hook for automated checking
- **Flexible Configuration**: Customize checking behavior with `typja.toml`
- **Rich Error Reports**: Detailed error messages with code snippets and suggestions
- **Watch Mode**: Monitor templates for changes and run checks automatically

## Quick Start

### Installation

```bash
pip install typja
```

### Basic Usage

```bash
# Check all templates in current directory
typja check

# Run in watch mode
typja watch

# Initialize a new typja.toml configuration
typja init
```

### Configuration

Create a `typja.toml` file in your project root with `typja init` or manually:

```toml
[project]
root = "."
paths = ["./models/**/*.py"]
fail_on_warning = false

[environment]
template_dirs = ["./templates"]
include_patterns = ["*.html", "*.jinja", "*.jinja2"]

[linting]
strict = false
prefer_pep604_unions = true
validate_imports = true
validate_variables = true

[errors]
verbosity = "normal"
show_snippets = true
show_hints = true
color = "auto"
```

## Type Annotations in Templates

Use special Jinja2 comments to declare variable types:

```jinja2
{# typja:var user: User #}
{# typja:var items: list[str] #}
{# typja:var count: int #}

<h1>{{ user.name }}</h1>
<ul>
  {% for item in items %}
    <li>{{ item }}</li>
  {% endfor %}
</ul>
```

## Examples

See the [examples/fastapi/](examples/fastapi/) directory for a complete FastAPI application with Jinja2 template type checking.

## Pre-commit Integration

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Daniel-Brai/Typja
    rev: v0.1.0
    hooks:
      - id: typja-check
        # With args
        # args: ["--strict", "--fix"]
```

## Documentation

- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration options
- [Syntax Guide](docs/SYNTAX.md) - Template syntax and type annotations

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development instructions.

## License

See [LICENSE](LICENSE) for details.
