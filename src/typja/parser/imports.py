import re

from typja.exceptions import TypjaParseError
from typja.parser.ast import FromImportStatement, ImportStatement


class ImportParser:
    """
    Parse import and from-import statements into Typja AST nodes
    """

    # For the pattern: "import module"
    IMPORT_PATTERN = re.compile(r"^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*$")

    # For the pattern: "from module import name1, name2 as alias"
    # Supports relative imports: from .module or from ..module
    FROM_IMPORT_PATTERN = re.compile(r"^from\s+(\.+[a-zA-Z_][a-zA-Z0-9_.]*|[a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+(.+)$")

    def parse_import(self, text: str, line: int, col: int) -> ImportStatement:
        match = self.IMPORT_PATTERN.match(text.strip())

        if not match:
            raise TypjaParseError(f"Invalid import statement: {text}", line=line, col=col)

        module = match.group(1)
        return ImportStatement(module=module, line=line, col=col)

    def parse_from_import(self, text: str, line: int, col: int) -> FromImportStatement:
        match = self.FROM_IMPORT_PATTERN.match(text.strip())

        if not match:
            raise TypjaParseError(f"Invalid from-import statement: {text}", line=line, col=col)

        module = match.group(1)
        imports_str = match.group(2)

        names = []
        for import_part in imports_str.split(","):
            import_part = import_part.strip()

            if " as " in import_part:
                name, alias = import_part.split(" as ", 1)
                names.append((name.strip(), alias.strip()))
            else:
                names.append((import_part, None))

        return FromImportStatement(module=module, names=names, line=line, col=col)
