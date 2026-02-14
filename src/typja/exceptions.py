class TypjaException(Exception):
    """
    Base exception for typja
    """

    pass


class TypjaParseError(TypjaException):
    """
    Raised when there is an error parsing a type definition or a type annotation
    """

    def __init__(self, message: str, filename: str = "<unknown>", line: int | None = None, col: int | None = None):
        self.message = message
        self.filename = filename
        self.line = line
        self.col = col
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        location = f"{self.filename}"

        if self.line is not None:
            location += f":{self.line}"
            if self.col is not None:
                location += f":{self.col}"

        return f"{location}: {self.message}"


class TypjaValidationError(TypjaException):
    """
    Raised when there is an error validating a value against a type definition
    """

    pass


class TypjaConfigError(TypjaException):
    """
    Raised when there is an error in the configuration of typja
    """

    pass
