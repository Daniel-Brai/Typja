from typing import NotRequired, TypedDict


class UserDict(TypedDict):

    id: int
    name: str
    email: str
    active: bool


class ProductDict(TypedDict, total=False):

    id: int
    name: str
    price: float


class PersonDict(TypedDict):

    name: str
    age: int
    email: NotRequired[str]
