import pyxel as px
import pyxelgrid as pg
from dataclasses import dataclass

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

ROWS = 11
COLS = 11
DIM = 16
movable: list[int] = [0]


stage: list[list[int]] = [[0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0],
                        [2, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2]]




class MyGame(pg.PyxelGrid[int]):

    def __init__(self):
        self.stage = stage
        super().__init__(r=ROWS, c=COLS, dim=DIM)  # 5 rows, 7 columns, cell side length 10 pixels

    def init(self) -> None:
        self.new_game()
        px.load("main.pyxres")
        # called once at initialization time

    def update(self) -> None:

        if px.btnp(px.KEY_W):
            self.move(-1, 0)
        if px.btnp(px.KEY_S):
            self.move(1, 0)
        if px.btnp(px.KEY_D):
            self.move(0, 1)
        if px.btnp(px.KEY_A):
            self.move(0, -1)
        if px.btnp(px.KEY_SPACE):
            self.bullet(self.dir)

    def bullet(self, dir: int):
        dy, dx = 0, 0
        if dir == 1:
            dx = -1
        if dir == 2:
            dx = 1
        if dir == 3:
            dy = -1
        if dir == 4:
            dy = 1 
        
        if (self.in_bounds(self.pos_x + dx, self.pos_y + dy)) and self[self.pos_x + dx, self.pos_y + dy] in movable:
            pos_x = self.pos_x + dx
            pos_y = self.pos_y + dy
            while (self.in_bounds(pos_x + dx, pos_y + dy)) and self[pos_x + dx, pos_y + dy] in movable:
                self[pos_x, pos_y] = 0
                self[pos_x + dx, pos_y + dy] = 3
                pos_x += dx
                pos_y += dy
        
        dx, dy = 0, 0
        

    def move(self, dx: int, dy: int) -> None:

        new_pos_x, new_pos_y = self.pos_x + dx, self.pos_y + dy

        if (self.in_bounds(new_pos_x, new_pos_y)) and (self[new_pos_x, new_pos_y] in movable) :
            self[self.pos_x, self.pos_y] = 0
            self[new_pos_x, new_pos_y] = 1
            self.pos_x += dx
            self.pos_y += dy
            if dx < 0:
                print("up")
                self.dir = 1 
            elif dx > 0:
                print("down")
                self.dir = 2
            elif dy < 0:
                print("left")
                self.dir = 3
            elif dy > 0:
                print("right")
                self.dir = 4
            # 1, 2, 3, 4, up down left right
            



    def new_game(self) -> None:

        self.dir: int = 1
        self.speed: int = 1

        for i in range(len(self.stage)):
            for j in range(len(self.stage)):
                if self.stage[i][j] == 0:
                    self[i, j] = 0
                if self.stage[i][j] == 1:
                    self.pos_x: int = i
                    self.pos_y: int = j
                    self[i, j] = 1
                if self.stage[i][j] == 2:
                    self[i, j] = 2
                
        
    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:

        if self[i, j] == 1: #PLAYER
            if self.dir == 1:
                px.blt(x + 1, y + 1, 0, 0, 0, DIM, DIM, 11)
            if self.dir == 2:
                px.blt(x + 1, y + 1, 0, 32, 0, DIM, DIM, 11)
            if self.dir == 3:
                px.blt(x + 1, y + 1, 0, 16, 0, DIM, DIM, 11)
            if self.dir == 4:
                px.blt(x + 1, y + 1, 0, 48, 0, DIM, DIM, 11)
            
        if self[i, j] == 2: #BLOCKAGE
            px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)
        
        if self[i, j] == 3: #BLOCKAGE
            px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 11)


    def pre_draw_grid(self) -> None:
        px.cls(0)
        # performs graphics drawing before the main grid is drawn
        # drawing the background image (e.g. via pyxel.cls) can be done here
        ...


    def post_draw_grid(self) -> None:
        # performs graphics drawing after the main grid is drawn
        ...

my_game = MyGame()

# The keyword arguments are passed directly to pyxel.init
my_game.run(title="My Game", fps=60)
