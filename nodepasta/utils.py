

class Vec:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other: 'Vec') -> 'Vec':
        return Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vec') -> 'Vec':
        return Vec(self.x - other.x, self.y - other.y)

    def move(self, x, y):
        self.x += x
        self.y += y

    def __str__(self) -> str:
        return f'<{self.x}, {self.y}>'