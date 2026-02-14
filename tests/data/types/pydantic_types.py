from pydantic import BaseModel, EmailStr, Field


class Account(BaseModel):

    id: int
    username: str
    email: str
    balance: float = 0.0
    is_active: bool = True

    def deposit(self, amount: float) -> None:
        pass


class Person(BaseModel):

    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: EmailStr
