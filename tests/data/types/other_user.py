class User:

    def __init__(self, user_id: str, full_name: str, status: str):
        self.user_id = user_id
        self.full_name = full_name
        self.status = status

    def is_active(self) -> bool:
        return self.status == "active"
