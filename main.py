import pyxel as px
import pyxelgrid as pg
from dataclasses import dataclass
from typing import Literal
from point import Point
from typing import TypeVar
from time import sleep

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

    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W']):
        self.pos = pos
        self.facing = facing
    
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
    
class Tank(Entity):
    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W']):
        self.powerups: list[int] = []
        self.ammo: int = 3
        super().__init__(pos, facing)

class Bullet(Entity):

    def __init__(self, pos: Point, facing: str):
        self.speed: int = 1
        self.pos = pos
        self.facing = facing
        self.is_alive: bool = True
        self.test = 0
        print('test')

    def forward(self):
        if self.facing == 'N':
            self.move(1, 0)
        elif self.facing == 'S':
            self.move(-1, 0)
        elif self.facing == 'W':
            self.move(0, -1)
        elif self.facing == 'E':
            self.move(0, 1)
        print(self.pos)

    def update(self):
        if self.test > 300:
            self.forward()
            self.test = 0
        else:
            self.test += 1
            print(self.test)
    
    def draw(self):
        px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 11)

@dataclass
class Tile:
    type: Literal['Empty', 'Wall']
    health: int | None = None

@dataclass
class State:
    content: Bullet | Tank | Tile

movable: list[State] = [State(Tile('Empty'))]

class MyGame(pg.PyxelGrid[State]):

    def __init__(self):
        self.stage = stage
        super().__init__(r=ROWS, c=COLS, dim=DIM, layerc=2)  # 5 rows, 7 columns, cell side length 10 pixels

    def init(self) -> None:
        self.new_game()
        px.mouse(True)
        px.load("main.pyxres")
        # called once at initialization time

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
            print(self.mouse_cell())

        if px.btnp(px.KEY_SPACE):
            self.shoot()


    def walkable(self, point: Point) -> bool:
        return self.in_bounds(point.x, point.y) and self[point.x, point.y] in movable
    
    def shoot(self) -> None:
        if self.walkable(self.player.front()):
            self.bullet = Bullet(self.player.front(), self.player.facing)
            while True:
                if not self.in_bounds(self.bullet.front().x, self.bullet.front().y):
                    self[self.bullet.pos.x, self.bullet.pos.y] = State(Tile('Empty'))
                    self.bullet = None
                    break
                elif self[self.bullet.front().x, self.bullet.front().y] == State(Tile('Wall')):
                    self[self.bullet.pos.x, self.bullet.pos.y] = State(Tile('Empty'))
                    self[self.bullet.front().x, self.bullet.front().y] = State(Tile('Empty'))
                    self.bullet = None
                    break
                elif self.walkable(self.bullet.front()):
                    self[self.bullet.pos.x, self.bullet.pos.y] = State(Tile('Empty'))
                    self.bullet.update()
                    self[self.bullet.pos.x, self.bullet.pos.y] = State(self.bullet)
                    self.draw_cell(self.bullet.pos.x, self.bullet.pos.y, self.x(self.bullet.pos.x), self.y(self.bullet.pos.y))
                    print("s",self[self.bullet.pos.x, self.bullet.pos.y])

    def moves(self, y: int, x: int) -> None:

        new_pos_x, new_pos_y = self.player.pos.x - x, self.player.pos.y + y

        if self.walkable(Point(new_pos_x, new_pos_y)):
            self[self.player.pos.x, self.player.pos.y] = State(Tile('Empty'))          
            self.player.move(x, y)
            self[self.player.pos.x, self.player.pos.y] = State(self.player)

    def new_game(self) -> None:

        self.frame_start = px.frame_count

        self.bullet = None

        for i in range(len(self.stage)):
            for j in range(len(self.stage)):
                if self.stage[i][j] == 0:
                    self[i, j] = State(Tile('Empty'))
                if self.stage[i][j] == 1:
                    self.player = Tank(Point(i, j), 'N')
                    self[i, j] = State(self.player)
                if self.stage[i][j] == 2:
                    self[i, j] = State(Tile('Wall'))
        
    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:

        if self[i, j] == State(self.player): #PLAYER
            if self.player.facing == 'N':
                px.blt(x + 1, y + 1, 0, 0, 0, DIM, DIM, 11)
            if self.player.facing == 'S':
                px.blt(x + 1, y + 1, 0, 32, 0, DIM, DIM, 11)
            if self.player.facing == 'W':
                px.blt(x + 1, y + 1, 0, 16, 0, DIM, DIM, 11)
            if self.player.facing == 'E':
                px.blt(x + 1, y + 1, 0, 48, 0, DIM, DIM, 11)
            
        if self[i, j] == State(Tile('Wall')): #BLOCKAGE
            px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)

        if self[i, j] == State(self.bullet):
            px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 11)

    def pre_draw_grid(self) -> None:
        px.cls(0)

        # performs graphics drawing before the main grid is drawn
        # drawing the background image (e.g. via pyxel.cls) can be done here

    def post_draw_grid(self) -> None:
        # performs graphics drawing after the main grid is drawn
        ...

my_game = MyGame()

# The keyword arguments are passed directly to pyxel.init
my_game.run(title="My Game", fps=FPS)