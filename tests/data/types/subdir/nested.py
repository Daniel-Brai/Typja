class NestedClass:
    value: str

    def __init__(self, value: str):
        self.value = value

    def process(self) -> str:
        return self.value.upper()
