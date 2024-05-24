from dataclasses import dataclass
from entity import Entity

@dataclass
class Tank(Entity):
    powerups: list[int]