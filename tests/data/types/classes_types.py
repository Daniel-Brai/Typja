from typing import List


class Post:
    title: str
    content: str
    author_id: int
    tags: List[str]

    def __init__(self, title: str, content: str, author_id: int):
        self.title = title
        self.content = content
        self.author_id = author_id
        self.tags = []

    def add_tag(self, tag: str) -> None:
        self.tags.append(tag)


class Comment:

    text: str
    author_id: int

    def __init__(self, text: str, author_id: int):
        self.text = text
        self.author_id = author_id


class User:

    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email
        self.active = True 

    def greet(self) -> str:
        return f"Hello, {self.name}"

    def save(self) -> None:
        pass



class BaseModel:

    id: int
    created_at: str

    def save(self):
        pass
