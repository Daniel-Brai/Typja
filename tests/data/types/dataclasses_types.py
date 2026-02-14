from dataclasses import dataclass, field


@dataclass
class Product:
    id: int
    name: str
    price: float
    description: str = ""
    tags: list[str] = field(default_factory=list)

    def discount(self, percent: float) -> float:
        return self.price * (1 - percent / 100)


@dataclass
class Order:

    order_id: int
    product: Product
    quantity: int = 1

    def total(self) -> float:
        return self.product.price * self.quantity


@dataclass(frozen=True)
class Point:
    x: float
    y: float
