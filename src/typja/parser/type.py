from typja.exceptions import TypjaParseError
from typja.parser.ast import TypeAnnotation


class TypeParser:
    """
    Parse Python-style type annotations
    """

    def parse_type(self, type_str: str, line: int, col: int) -> TypeAnnotation:
        type_str = type_str.strip()

        if " | " in type_str:
            return self._parse_union(type_str, line, col)

        if type_str.startswith("Union["):
            return self._parse_union_old(type_str, line, col)

        if type_str.startswith("Optional["):
            return self._parse_optional(type_str, line, col)

        if "[" in type_str:
            return self._parse_generic(type_str, line, col)

        if "." in type_str:
            return self._parse_qualified(type_str)

        return TypeAnnotation(raw=type_str, name=type_str, module=None)

    def _parse_union(self, type_str: str, line: int, col: int) -> TypeAnnotation:
        parts = [part.strip() for part in type_str.split(" | ")]
        union_types = [self.parse_type(part, line, col) for part in parts]

        return TypeAnnotation(
            raw=type_str,
            name="Union",
            module=None,
            is_union=True,
            union_types=union_types,
        )

    def _parse_union_old(self, type_str: str, line: int, col: int) -> TypeAnnotation:
        if not type_str.endswith("]"):
            raise TypjaParseError(f"Invalid Union syntax: {type_str}", line=line, col=col)

        inner = type_str[6:-1].strip()
        parts = self._split_args(inner)
        union_types = [self.parse_type(part, line, col) for part in parts]

        return TypeAnnotation(
            raw=type_str,
            name="Union",
            module="typing",
            is_union=True,
            union_types=union_types,
        )

    def _parse_optional(self, type_str: str, line: int, col: int) -> TypeAnnotation:
        if not type_str.endswith("]"):
            raise TypjaParseError(f"Invalid Optional syntax: {type_str}", line=line, col=col)

        inner = type_str[9:-1].strip()
        inner_type = self.parse_type(inner, line, col)
        none_type = TypeAnnotation(raw="None", name="None", module=None)

        return TypeAnnotation(
            raw=type_str,
            name="Optional",
            module="typing",
            is_union=True,
            union_types=[inner_type, none_type],
        )

    def _parse_generic(self, type_str: str, line: int, col: int) -> TypeAnnotation:
        bracket_start = type_str.index("[")
        base = type_str[:bracket_start].strip()

        if not type_str.endswith("]"):
            raise TypjaParseError(f"Invalid generic syntax: {type_str}", line=line, col=col)

        inner = type_str[bracket_start + 1 : -1].strip()

        if base in ("Callable", "typing.Callable"):
            return self._parse_callable(base, inner, type_str, line, col)

        args_strs = self._split_args(inner)
        args = [self.parse_type(arg, line, col) for arg in args_strs]

        module = None
        name = base
        if "." in base:
            module, name = base.rsplit(".", 1)

        return TypeAnnotation(raw=type_str, name=name, module=module, args=args)

    def _parse_callable(self, base: str, inner: str, raw: str, line: int, col: int) -> TypeAnnotation:
        if "], " not in inner:
            raise TypjaParseError(f"Invalid Callable syntax: {raw}", line=line, col=col)

        args_part, return_part = inner.split("], ", 1)
        args_part = args_part.strip()

        if not args_part.startswith("["):
            raise TypjaParseError(f"Invalid Callable syntax: {raw}", line=line, col=col)
        args_part = args_part[1:].strip()

        arg_types = []
        if args_part:
            args_strs = self._split_args(args_part)
            arg_types = [self.parse_type(arg, line, col) for arg in args_strs]

        return_type = self.parse_type(return_part, line, col)

        all_args = arg_types + [return_type]

        module = None
        name = base
        if "." in base:
            module, name = base.rsplit(".", 1)

        return TypeAnnotation(raw=raw, name=name, module=module, args=all_args)

    def _parse_qualified(self, type_str: str) -> TypeAnnotation:
        module, name = type_str.rsplit(".", 1)

        return TypeAnnotation(raw=type_str, name=name, module=module)

    @staticmethod
    def _split_args(args_str: str) -> list[str]:
        args = []
        current = []
        depth = 0

        for char in args_str:
            if char in "[({":
                depth += 1
                current.append(char)
            elif char in "])}":
                depth -= 1
                current.append(char)
            elif char == "," and depth == 0:
                args.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            args.append("".join(current).strip())

        return [arg for arg in args if arg]
