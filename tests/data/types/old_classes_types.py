class OldStyleClass:
    def __init__(self, name):
        self.name = name
        self.count = 0

    def increment(self):
        self.count += 1
        return self.count
