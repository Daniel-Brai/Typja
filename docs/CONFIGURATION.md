# Typja Configuration Guide

This guide covers all configuration options available in Typja via the `typja.toml` file.

## Configuration File Location

Place `typja.toml` in the root directory of your project:

```text
your-project/
├── typja.toml
├── src/
├── templates/
└── models/
```

## Configuration Sections

### Project Configuration

The `[project]` section defines basic project settings:

```toml
[project]
root = "."
paths = ["./models/**/*.py", "./types/**/*.py"]
fail_on_warning = false
```

#### Options

- **`root`** (string)
  - Root directory of the project
  - Default: `"."`
  - Used as the base path for resolving imports and paths

- **`paths`** (list of strings)
  - Paths where Typja looks for type definitions
  - Supports glob patterns: `**/*.py`, `src/**/*.py`
  - These paths are searched when resolving imports in templates
  - Default: `["./src/**/*.py"]`

- **`fail_on_warning`** (boolean)
  - Exit with non-zero code if warnings are found
  - Default: `false`
  - Set to `true` for strict CI/CD pipelines

### Environment Configuration

The `[environment]` section configures the Jinja2 environment:

```toml
[environment]
template_dirs = ["./templates"]
include_patterns = ["*.html", "*.jinja", "*.jinja2", "*.j2"]
exclude_patterns = ["**/node_modules/**", "**/.git/**", "**/dist/**"]
```

#### Environment Options

- **`template_dirs`** (list of strings)
  - Directories where Typja scans for templates
  - Can be multiple directories
  - Default: `["./templates"]`

- **`include_patterns`** (list of strings)
  - File patterns to include in scanning
  - Examples: `*.html`, `*.jinja`, `*.jinja2`
  - Default: `["*.html", "*.jinja", "*.jinja2", "*.j2"]`

- **`exclude_patterns`** (list of strings)
  - File patterns to exclude from scanning
  - Useful for ignoring node_modules, build output, etc.
  - Common patterns:
    - `**/node_modules/**`
    - `**/.git/**`
    - `**/dist/**`
    - `**/build/**`
    - `**/__pycache__/**`
  - Default: `[]`

### Linting Configuration

The `[linting]` section controls type checking behavior:

```toml
[linting]
strict = false
prefer_pep604_unions = true
union_style = "warning"
fix_union_syntax = true
warn_unused_imports = true
warn_undefined_variables = true
warn_type_mismatches = true
validate_imports = true
validate_variables = true
```

#### Linting Options

- **`strict`** (boolean)
  - Enable strict mode: all variables must be typed
  - Default: `false`
  - When enabled, accessing undefined or untyped variables produces errors

- **`prefer_pep604_unions`** (boolean)
  - Recommend PEP 604 union syntax (`X | Y` instead of `Union[X, Y]`)
  - Default: `true`

- **`union_style`** (string: `"error"`, `"warning"`, `"ignore"`)
  - Severity level for union style violations
  - Default: `"warning"`

- **`fix_union_syntax`** (boolean)
  - Auto-fix union syntax to PEP 604 style when running with `--fix`
  - Default: `true`

- **`warn_unused_imports`** (boolean)
  - Warn about unused type imports in templates
  - Default: `true`

- **`warn_undefined_variables`** (boolean)
  - Warn when template uses undefined variables
  - Default: `true`

- **`warn_type_mismatches`** (boolean)
  - Warn when variable usage doesn't match declared type
  - Default: `true`

- **`validate_imports`** (boolean)
  - Validate that imported types exist in type definitions
  - Default: `true`

- **`validate_variables`** (boolean)
  - Validate that variable usage matches declared types
  - Default: `true`

### Error Reporting Configuration

The `[errors]` section controls output formatting:

```toml
[errors]
verbosity = "normal"
show_snippets = true
show_hints = true
color = "auto"
```

#### Error Reporting Options

- **`verbosity`** (string: `"minimal"`, `"normal"`, `"verbose"`)
  - Error message verbosity level
  - `"minimal"`: Only file, line, and message
  - `"normal"`: Includes context and suggestions
  - `"verbose"`: Includes all available debugging information
  - Default: `"normal"`

- **`show_snippets`** (boolean)
  - Show code snippets in error messages
  - Default: `true`

- **`show_hints`** (boolean)
  - Show hints and suggestions in error messages
  - Default: `true`

- **`color`** (string: `"auto"`, `"always"`, `"never"`)
  - Colorized output in terminal
  - `"auto"`: Auto-detect based on terminal capabilities
  - `"always"`: Force colors even in non-TTY environments
  - `"never"`: No colors
  - Default: `"auto"`

## Example Configurations

### Minimal Setup

```toml
[project]
root = "."

[environment]
template_dirs = ["./templates"]
```

### Strict Development

```toml
[project]
root = "."
paths = ["./src/**/*.py"]
fail_on_warning = true

[environment]
template_dirs = ["./templates", "./email_templates"]
include_patterns = ["*.html", "*.jinja2"]
exclude_patterns = ["**/node_modules/**"]

[linting]
strict = true
validate_imports = true
validate_variables = true
warn_type_mismatches = true

[errors]
verbosity = "verbose"
show_snippets = true
show_hints = true
color = "auto"
```

### Production

```toml
[project]
root = "."
paths = ["./models/**/*.py", "./types/**/*.py"]
fail_on_warning = true

[environment]
template_dirs = ["./templates"]
include_patterns = ["*.html"]
exclude_patterns = ["**/node_modules/**", "**/dist/**", "**/__pycache__/**"]

[linting]
strict = false
validate_imports = true
validate_variables = true
warn_type_mismatches = true

[errors]
verbosity = "normal"
show_snippets = true
show_hints = true
color = "never"
```

### FastAPI Project

```toml
[project]
root = "."
paths = ["./app/models/**/*.py", "./app/schemas/**/*.py"]

[environment]
template_dirs = ["./app/templates"]
include_patterns = ["*.html", "*.jinja2"]
exclude_patterns = ["**/node_modules/**"]

[linting]
strict = false
prefer_pep604_unions = true
validate_imports = true
validate_variables = true
warn_type_mismatches = true

[errors]
verbosity = "normal"
show_snippets = true
show_hints = true
```

## Using Configuration in CI/CD

### GitHub Actions

```yaml
name: Typja Check

on: [push, pull_request]

jobs:
  typja:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install typja
      - run: typja check
```

### Pre-commit

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/your-org/typja
    rev: v0.1.0
    hooks:
      - id: typja-check
```

## Troubleshooting Configuration

### Paths Not Found

If Typja can't find your type definitions:

1. Check that paths in `typja.toml` use correct glob patterns
2. Verify paths are relative to project `root`
3. Try with absolute patterns: `src/**/*.py`

### Templates Not Scanned

If your templates aren't being scanned:

1. Verify `template_dirs` points to correct directories
2. Check `include_patterns` matches your file extensions
3. Ensure `exclude_patterns` aren't filtering your templates

### Type Resolution Issues

If Typja can't resolve custom types:

1. Ensure custom types are in the `paths` configured
2. Check that imports in templates match actual type locations
3. Set `validate_imports = true` to debug import issues
