from functools import lru_cache

PACKAGE_NAME = "typja"


@lru_cache(maxsize=1)
def get_builtins() -> set[str]:
    """
    Get a set of all Python builtin types
    """

    import builtins

    public_attrs = [name for name in dir(builtins) if not name.startswith("_")]
    return set(public_attrs)


@lru_cache(maxsize=1)
def get_typing_types() -> set[str]:
    """
    Get a set of all types from the typing module
    """

    import typing

    public_attrs = [name for name in dir(typing) if not name.startswith("_")]
    return set(public_attrs)


PYTHON_BUILTINS = get_builtins()

TYPING_TYPES = get_typing_types()
