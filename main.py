import pyxel as px
import pyxelgrid as pg
from dataclasses import dataclass, field
from typing import Literal
from point import Point

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

ROWS = 11
COLS = 11
DIM = 16
FPS = 60

stage: list[list[int]] = [[2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0],
                        [2, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0],
                        [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
                        [2, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0],
                        [2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
                        [2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2]]

class Entity:

    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W'], health: int = 1):
        self.pos = pos
        self.facing = facing
        self.health = health
        self.alive: bool = True

    @property
    def _pos(self) -> tuple[int, int]:
        return (self.pos.x, self.pos.y)
    
    def rotate(self, direction: Literal['N', 'E', 'S', 'W', 'CW', 'CCW']) -> None:
        dirs = ['N', 'E', 'S', 'W']

        if direction == 'CW':
            self.facing = dirs[(dirs.index(self.facing) + 1) % 4]
        elif direction == 'CCW':
            self.facing = dirs[(dirs.index(self.facing) - 1) % 4]
        elif direction in dirs:
            self.facing = direction
    
    def move(self, x: int | float, y: int | float) -> None:
        x, y = int(x), int(y)
        self.pos.x, self.pos.y = self.pos.x - x, self.pos.y + y
        if x > 0:
            self.rotate('N')
        elif x < 0:
            self.rotate('S')
        elif y > 0:
            self.rotate('E')
        elif y < 0:
            self.rotate('W')

    def front(self):
        if self.facing == 'N':
            return Point(self.pos.x - 1, self.pos.y)
        if self.facing == 'S':
            return Point(self.pos.x + 1, self.pos.y)
        if self.facing == 'W':
            return Point(self.pos.x, self.pos.y - 1)
        if self.facing == 'E':
            return Point(self.pos.x, self.pos.y + 1)
        return self.pos

    def damage(self, damage: int = 1):
        if self.alive:
            self.health -= damage
            if self.health < 1:
                self.alive = False
  
class Tank(Entity):
    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W']):
        self.powerups: list[int] = field(default_factory=list)
        self.ammo: int = 10
        super().__init__(pos, facing)

class Bullet(Entity):

    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W']):
        self.counter = 0
        super().__init__(pos, facing)

    def forward(self):
        if self.facing == 'N':
            self.move(1, 0)
        elif self.facing == 'S':
            self.move(-1, 0)
        elif self.facing == 'W':
            self.move(0, -1)
        elif self.facing == 'E':
            self.move(0, 1)

@dataclass
class Tile:
    type: Literal['Wall'] | None = None
    health: int = 0

    def damage(self, damage: int = 1):
        if self.type == 'Wall':
            self.health -= damage
            if self.health < 1:
                self.type = None

class Powerup:
    type: Literal['speed', 'health', 'bullet']

@dataclass
class CellState:
    content: Entity | Tile = field(default_factory=Tile)
    powerup: Powerup | None = None

movable: list[CellState] = [CellState(Tile())]

class MyGame(pg.PyxelGrid[CellState]):

    def __init__(self):
        self.stage = stage
        super().__init__(r=ROWS, c=COLS, dim=DIM)

    def init(self) -> None:
        self.new_game()
        px.mouse(True)
        px.load("main.pyxres")

    def update(self) -> None:
        if px.btnp(px.KEY_W):
            self.moves(0, 1)
        if px.btnp(px.KEY_S):
            self.moves(0, -1)
        if px.btnp(px.KEY_D):
            self.moves(1, 0)
        if px.btnp(px.KEY_A):
            self.moves(-1, 0)

        if px.btnp(px.KEY_Q):
            print(self[self.mouse_cell()], self.mouse_cell())

        if px.btnp(px.KEY_SPACE):
            if not self.bullet and self.player.ammo > 0:
                if self.is_walkable(self.player.front()):
                    self.player.ammo -= 1
                    self.bullet = Bullet(self.player.front(), self.player.facing)

        self.update_bullet()

        


    def is_walkable(self, point: Point) -> bool:
        return self.in_bounds(point.x, point.y) and self[point.x, point.y] in movable
    
    def shoot(self) -> None:
        if self.bullet:
            Current = (self.bullet.pos.x, self.bullet.pos.y)
            Front = (self.bullet.front().x, self.bullet.front().y)

            self[Current].content = Tile()


            if not self.in_bounds(*Front):
                self.bullet = None

            elif self[Front].content.health:
                self[Front].content.damage()
                self.bullet = None

            if self.bullet:  
                self.bullet.forward()
                self[Front].content = self.bullet


            # if not self.in_bounds(*FrontTile):
            #     self[self.bullet.pos.x, self.bullet.pos.y] = CellState(Tile('Empty'))
            #     self.bullet = None
            # elif self[FrontTile] == CellState(Tile('Wall', 3)) or self[FrontTile] == CellState(Tile('Wall', 2)):
            #     self[self.bullet.pos.x, self.bullet.pos.y] = CellState(Tile('Empty'))
            #     wall = self[FrontTile]
            #     self[FrontTile].content.damage()
            #     self.bullet = None
            # elif self[FrontTile] == CellState(Tile('Wall', 1)):
            #     self[self.bullet.pos.x, self.bullet.pos.y] = CellState(Tile('Empty'))
            #     self[FrontTile] = CellState(Tile('Empty'))
            #     self.bullet = None
            # elif self.is_walkable(self.bullet.front()):
            #     self[self.bullet.pos.x, self.bullet.pos.y] = CellState(Tile('Empty'))
            #     self.bullet.forward()
            #     self[self.bullet.pos.x, self.bullet.pos.y] = CellState(self.bullet)

    def update_bullet(self):
        if self.bullet:
            if self.bullet.counter >= 1:
                self.shoot()
                if self.bullet:
                    self.bullet.counter = 0
            else:
                self.bullet.counter += 1



    def moves(self, y: int, x: int) -> None:

        new_pos_x, new_pos_y = self.player.pos.x - x, self.player.pos.y + y

        if self.is_walkable(Point(new_pos_x, new_pos_y)):
            self[self.player.pos.x, self.player.pos.y] = CellState()          
            self.player.move(x, y)
            self[self.player.pos.x, self.player.pos.y] = CellState(self.player)

    def new_game(self) -> None:

        self.frame_start = px.frame_count

        self.bullet = None

        for i in range(len(self.stage)):
            for j in range(len(self.stage)):
                if self.stage[i][j] == 0:
                    self[i, j] = CellState()
                if self.stage[i][j] == 1:
                    self.player = Tank(Point(i, j), 'N')
                    self[i, j] = CellState(self.player)
                if self.stage[i][j] == 2:
                    self[i, j] = CellState(Tile('Wall', health = 3))
        
    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:

        if self[i, j] == CellState(self.player): #PLAYER
            if self.player.facing == 'N':
                px.blt(x + 1, y + 1, 0, 0, 0, DIM, DIM, 11)
            if self.player.facing == 'S':
                px.blt(x + 1, y + 1, 0, 32, 0, DIM, DIM, 11)
            if self.player.facing == 'W':
                px.blt(x + 1, y + 1, 0, 16, 0, DIM, DIM, 11)
            if self.player.facing == 'E':
                px.blt(x + 1, y + 1, 0, 48, 0, DIM, DIM, 11)
            px.text(x, y, str(self.player.ammo), 7)
            
        if self[i, j] == CellState(Tile('Wall', health=3)): #BLOCKAGE health 3
            px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)
        
        if self[i, j] == CellState(Tile('Wall', health=2)): #BLOCKAGE health 2
            px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)

        if self[i, j] == CellState(Tile('Wall', health=1)): #BLOCKAGE health 1
            px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)

        if self.bullet:
            if self[i, j] == CellState(self.bullet):
                px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 11)

    def pre_draw_grid(self) -> None:
        px.cls(0)

        # performs graphics drawing before the main grid is drawn
        # drawing the background image (e.g. via pyxel.cls) can be done here

    def post_draw_grid(self) -> None:
        # performs graphics drawing after the main grid is drawn
        ...

my_game = MyGame()

my_game.run(title="Boom City", fps=FPS)