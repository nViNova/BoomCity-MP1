from dataclasses import dataclass
from typing import Literal
from point import Point

@dataclass
class Entity:
    pos: Point
    facing: str
    
    def rotate(self, direction: Literal['N', 'E', 'S', 'W', 'CW', 'CCW']) -> None:
        dirs = ['N', 'E', 'S', 'W']

        if direction == 'CW':
            self.facing = dirs[(dirs.index(self.facing) + 1) % 4]
        elif direction == 'CCW':
            self.facing = dirs[(dirs.index(self.facing) - 1) % 4]
        elif direction in dirs:
            self.facing = direction
    
    def move(self, x: int, y: int):
        self.pos.x, self.pos.y = self.pos.x - x, self.pos.y + y
        if x > 0:
            self.rotate('N')
        elif x < 0:
            self.rotate('S')
        elif y > 0:
            self.rotate('E')
        elif y < 0:
            self.rotate('W')