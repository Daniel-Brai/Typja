class User:
    """User type from user.py"""

    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

    def get_display_name(self) -> str:
        return f"{self.name} ({self.email})"
