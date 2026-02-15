class User:

    def __init__(self, id: int, name: str, email: str, is_active: bool = True, profile: Profile | None = None):
        self.id = id
        self.name = name
        self.email = email
        self.is_active = is_active
        self.profile = profile

    def get_display_name(self) -> str:
        return f"{self.name} ({self.email})"



class Profile:

    def __init__(self, bio: str, website: str | None = None):
        self.bio = bio
        self.website = website
