class User:

    def __init__(self, id: int, name: str, email: str, is_active: bool = True):
        self.id = id
        self.name = name
        self.email = email
        self.is_active = is_active

    def get_display_name(self) -> str:
        return f"{self.name} ({self.email})"
