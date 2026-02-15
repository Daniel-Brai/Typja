# Typja Syntax Guide

This guide covers the syntax and features of Typja for adding type information to Jinja2 templates.

## Type Annotations

### Basic Variable Declaration

Declare variable types using special Jinja2 comments at the beginning of your template:

```jinja2
{# typja:var variable_name: type_name #}
```

### Examples

```jinja2
{# typja:var user: User #}
{# typja:var count: int #}
{# typja:var name: str #}
{# typja:var is_active: bool #}
{# typja:var items: list #}
{# typja:var emails: list[str] #}
{# typja:var tags: set[str] #}
{# typja:var mapping: dict[str, int] #}
```

### Standard Python Types

- `int` - Integer
- `str` - String
- `bool` - Boolean
- `float` - Floating-point number
- `bytes` - Byte string
- `None` - None type
- `list` - List (no element type specified)
- `dict` - Dictionary (no key/value types specified)
- `set` - Set (no element type specified)
- `tuple` - Tuple (no element types specified)

### Generic Types

Use square brackets to specify element types:

```jinja2
{# typja:var items: list[str] #}
{# typja:var mapping: dict[str, int] #}
{# typja:var ids: set[int] #}
{# typja:var pair: tuple[str, int] #}
```

### Custom Types

Reference your Python classes:

```jinja2
{# typja:var user: User #}
{# typja:var posts: list[Post] #}
{# typja:var author: User | None #}
```

### Handling Type Conflicts

When the same type name exists in multiple modules, Typja will report an ambiguous type error. You can resolve this in two ways:

#### Using Qualified Names

Use the full module path to specify which type you mean:

```jinja2
{# typja:var admin_user: admin.User #}
{# typja:var customer_user: customer.User #}
{# typja:var blog_post: blog.Post #}
```

#### Using Explicit Imports

Import the specific type you want to use:

```jinja2
{# typja:from user import User #}
{# typja:from admin import Role #}
{# typja:var current_user: User #}
{# typja:var user_role: Role #}
```

The imported type will take precedence over conflicting types from other modules.

### Union Types

Use the pipe operator for union types (PEP 604):

```jinja2
{# typja:var value: str | int #}
{# typja:var user: User | None #}
{# typja:var result: list[str] | dict[str, int] #}
```

### Optional Types

Use `Optional` or the `| None` syntax:

```jinja2
{# typja:var description: Optional[str] #}
{# typja:var user: User | None #}
```

## Imports

### Importing Modules

Import entire modules to access their types:

```jinja2
{# typja:import models #}
{# typja:var user: models.User #}
{# typja:var post: models.Post #}
```

### Importing Specific Types

Import specific types from modules:

```jinja2
{# typja:from models import User, Post #}
{# typja:from typing import Optional, List #}
{# typja:var user: User #}
{# typja:var posts: List[Post] #}
{# typja:var description: Optional[str] #}
```

### Import with Aliases

Import types with different names:

```jinja2
{# typja:from models import User as ModelUser #}
{# typja:from admin import User as AdminUser #}
{# typja:var customer: ModelUser #}
{# typja:var administrator: AdminUser #}
```

## Variable Usage

### Simple Variable Access

```jinja2
{# typja:var user: User #}

<h1>{{ user.name }}</h1>
<p>{{ user.email }}</p>
```

### Object Attribute Access

```jinja2
{# typja:var user: User #}

{{ user.profile.bio }}
{{ user.get_display_name() }}
```

### List Iteration

```jinja2
{# typja:var items: list[str] #}

{% for item in items %}
  <li>{{ item }}</li>
{% endfor %}
```

### Dictionary Access

```jinja2
{# typja:var mapping: dict[str, int] #}

{% for key, value in mapping.items() %}
  <p>{{ key }}: {{ value }}</p>
{% endfor %}
```

### Conditional Checks

```jinja2
{# typja:var user: User | None #}

{% if user %}
  <h1>{{ user.name }}</h1>
{% else %}
  <p>No user found</p>
{% endif %}
```

## Built-in Filters and Tests

### Common Filters

```jinja2
{# typja:var name: str #}

{{ name | upper }}
{{ name | lower }}
{{ name | title }}

{# typja:var items: list[str] #}
{{ items | join(", ") }}
{{ items | length }}
```

### Type Filters

```jinja2
{{ value | string }}
{{ value | int }}
{{ value | float }}
```

### Conditional Tests

```jinja2
{# typja:var value: str | None #}

{% if value is defined %}
{% if value is none %}
{% if value is string %}
{% if value is number %}
{% if value %}
```

## Advanced Patterns

### Nested Types

```jinja2
{# typja:var data: dict[str, list[User]] #}

{% for group_name, users in data.items() %}
  <h2>{{ group_name }}</h2>
  {% for user in users %}
    <p>{{ user.name }}</p>
  {% endfor %}
{% endfor %}
```

### Multiple Variables

You can declare several variables in a single `typja:var` comment by separating declarations with commas.

```jinja2
{# typja:var name: str, count: int, active: bool #}
{# typja:var user: Admin, posts: list[Post], title: str #}
```

Or declare each variable with its own comment — both forms are supported.

### Class Methods

```jinja2
{# typja:var user: User #}

<p>{{ user.get_display_name() }}</p>
<p>{{ user.get_full_profile() }}</p>
```

## Comments and Ignoring

### Type Comments

```jinja2
{# typja:var user: User #}

{# This is a regular Jinja2 comment #}
{# The user variable is of type User #}
```

### Ignoring Lines

Use `typja: ignore` for specific lines or inline expressions to tell Typja to skip type checks on that line/expression.

```jinja2
{# typja:var user: User | None #}

{# This might raise an error without ignore; Typja will skip checking this line #}
{{ user.name }} {# typja: ignore #}
```

Notes:

- The `typja: ignore` directive applies to the template line where the comment appears.
- Useful for deliberate dynamic/unsafe template expressions or when you want to suppress a specific check.

## Error Messages

Typja provides clear error messages:

```text
Error: Type mismatch
File: templates/profile.html
Line: 15
Message: 'str' has no attribute 'count'
Variable 'name' is of type 'str', which does not have method 'count()'
Suggestion: Did you mean to use 'name.upper()' or similar?
```

## Quick Reference

| Type | Example |
| ------ | --------- |
| Basic type | `{# typja:var name: str #}` |
| Generic | `{# typja:var items: list[str] #}` |
| Union | `{# typja:var value: str \| int #}` |
| Optional | `{# typja:var user: User \| None #}` |
| Custom class | `{# typja:var user: User #}` |
| Nested | `{# typja:var data: dict[str, list[Post]] #}` |
