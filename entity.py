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
