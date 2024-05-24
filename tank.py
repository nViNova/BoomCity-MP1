from dataclasses import dataclass, field
from entity import Entity

@dataclass
class Tank(Entity):
    powerups: list[int] = field(default_factory=list)