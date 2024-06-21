import pyxel as px
import pyxelgrid as pg
from dataclasses import dataclass, field
from typing import Literal
from point import Point
from random import randint
import json

# Read the JSON file
with open('stage_data.json', 'r') as file:
    TRY_STAGE = json.load(file)

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

SCENE_TITLE = 0
SCENE_PLAY = 1
SCENE_GAMEOVER = 2
SCENE_STAGE_CLEAR = 3

CURR_SCORE = 0
CURR_LIVES = 3
CURR_STAGE = 1

ROWS = 11
COLS = 11
DIM = 16
FPS = 60

STAGE: list[list[int]] = TRY_STAGE['STAGE'][CURR_STAGE - 1]['stage']


class Entity:

    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W'], health: int = 1):
        self.pos: Point = pos
        self.facing: Literal['N', 'E', 'S', 'W'] = facing
        self.health: int = health
        self.alive: bool = True
        self.is_invulnerable_counter: int = 0

    @property
    def _pos(self) -> tuple[int, int]:
        return (self.pos.x, self.pos.y)
    
    def rotate(self, direction: Literal['N', 'E', 'S', 'W', 'CW', 'CCW']) -> None:
        dirs: list[Literal['N', 'E', 'S', 'W']] = ['N', 'E', 'S', 'W']

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
            if not self.is_invulnerable_counter:

                self.health -= damage
                if self.health < 1:
                    self.alive = False
  
class Tank(Entity):
    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W'], health: int = 3, ammo: int = 10):
        self.ammo: int = ammo
        super().__init__(pos, facing, health)

    def __repr__(self) -> str:
        return f'Tank with {self.health} health, {self.ammo} ammo, {self.alive} alive, {self.__hash__}'

class Bullet(Entity):

    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W']):
        self.counter: int = 0
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

@dataclass
class Powerup:
    type: Literal['health', 'bullet', 'shield', 'win']
    intensity: int = 1

@dataclass
class CellState:
    content: Entity | Tile = field(default_factory=Tile)
    powerup: Powerup | None = None

MOVABLE: list[Tile] = [Tile()]

class MyGame(pg.PyxelGrid[CellState]):

    def __init__(self):
        self.current_stage = CURR_STAGE
        self.score = CURR_SCORE
        self.stage: list[list[int]] = TRY_STAGE['STAGE'][self.current_stage - 1]['stage']
        self.scene = SCENE_TITLE
        self.player = None
        
        super().__init__(r=ROWS, c=COLS, dim=DIM)

    def init(self) -> None:
        self.new_game(self.stage)
        px.mouse(True)
        px.load("main.pyxres")

    def update(self) -> None:
        if self.scene == SCENE_TITLE:
            self.update_title_scene()

        if self.player.health == 0:
            self.scene = SCENE_GAMEOVER
            self.update_gameover_scene()

        if len(self.enemies) == 0:
            self.scene = SCENE_STAGE_CLEAR
            self.update_next_stage()

        if px.btnp(px.KEY_W) or px.btnp(px.KEY_UP):
            self.attempt_move(0, 1, self.player)
        if px.btnp(px.KEY_S) or px.btnp(px.KEY_DOWN):
            self.attempt_move(0, -1, self.player)
        if px.btnp(px.KEY_D) or px.btnp(px.KEY_RIGHT):
            self.attempt_move(1, 0, self.player)
        if px.btnp(px.KEY_A) or px.btnp(px.KEY_LEFT):
            self.attempt_move(-1, 0, self.player)

        if px.btnp(px.KEY_Q):
            print(self[self.mouse_cell()], self.mouse_cell())
        if px.btnp(px.KEY_P):
            print(self.enemies)
        if px.btnp(px.KEY_1):
            for enemy in self.enemies:
                self.enemy_shoot(enemy)

        if px.btnp(px.KEY_SPACE):
            self.shoot()

        self.update_projectiles()
        self.update_enemies()
        self.update_player()

    def is_walkable(self, point: Point) -> bool:
        return self.in_bounds(point.x, point.y) and self[point.x, point.y].content in MOVABLE
    
    def shoot(self) -> None:
        if not self.bullet and self.player.ammo > 0:
            if self.is_walkable(self.player.front()):
                self.bullet = Bullet(self.player.front(), self.player.facing)
            elif self.in_bounds(self.player.front().x, self.player.front().y):
                self[self.player.front().x, self.player.front().y].content.damage()

            self.player.ammo -= 1

    
    def enemy_shoot(self, enemy: Tank) -> None:
        if enemy.ammo > 0:
            if self.is_walkable(enemy.front()):
                self.projectiles.append(Bullet(enemy.front(), enemy.facing))
            elif self.in_bounds(enemy.front().x, enemy.front().y):
                self[enemy.front().x, enemy.front().y].content.damage()
            
            enemy.ammo -= 1
    
    def move_bullet(self) -> None:
        if self.bullet:
            Current = (self.bullet.pos.x, self.bullet.pos.y)
            Front = (self.bullet.front().x, self.bullet.front().y)

            self[Current].content = Tile()

            if not self.in_bounds(*Front):
                self.bullet = None

            #check if bullet hits an enemy
            elif self[Front].content in self.enemies:
                self.score += 50
                self[Front].content.damage()
                self.bullet = None

            elif self[Front].content.health:
                self[Front].content.damage()
                self.bullet = None

            if self.bullet:  
                self.bullet.forward()
                self[Front].content = self.bullet
    
    def move_projectile(self, projectile: Bullet) -> None:
        Current = (projectile.pos.x, projectile.pos.y)
        Front = (projectile.front().x, projectile.front().y)

        self[Current].content = Tile()

        if not self.in_bounds(*Front):
            self.projectiles.remove(projectile)

        elif self[Front].content.health:
            self[Front].content.damage()
            self.projectiles.remove(projectile)

        elif projectile:  
            projectile.forward()
            self[Front].content = projectile


    def update_projectiles(self) -> None:
        if self.bullet:
            if self.bullet.counter >= 1:
                self.move_bullet()
                if self.bullet:
                    self.bullet.counter = 0
            else:
                self.bullet.counter += 1
        
        if self.projectiles:
            for projectile in self.projectiles:
                if projectile.counter >= 1:
                    self.move_projectile(projectile)
                    if projectile:
                        projectile.counter = 0
                else:
                    projectile.counter += 1
                

    def update_enemies(self) -> None:
        if self.enemies:
            for enemy in self.enemies:
                if enemy.alive:
                    self.enemy_move(enemy)
                else:
                    self.enemies.remove(enemy)
                    self[enemy.pos.x, enemy.pos.y].content = Tile()
    
    def update_player(self) -> None:
        if not px.frame_count % FPS:
            if self.player.is_invulnerable_counter:
                print(self.player.is_invulnerable_counter, "seconds left of shield")
                self.player.is_invulnerable_counter -= 1

    
    def enemy_move(self, enemy: Tank) -> None:
        if not px.frame_count % FPS // 2:
            roll: int = randint(0, 10)
            if roll == 0:
                self.attempt_move(1, 0, enemy)
            if roll == 1:
                self.attempt_move(-1, 0, enemy)
            if roll == 2:
                self.attempt_move(0, 1, enemy)
            if roll == 3:
                self.attempt_move(0, -1, enemy) 
            if roll == 4:
                self.enemy_shoot(enemy)


    def attempt_move(self, y: int, x: int, entity: Tank) -> None:

        new_pos_x, new_pos_y = entity.pos.x - x, entity.pos.y + y

        if self.is_walkable(Point(new_pos_x, new_pos_y)):
            if entity is self.player:
                if powerup := self[new_pos_x, new_pos_y].powerup:
                    if powerup.type == 'bullet':
                        entity.ammo += powerup.intensity
                    if powerup.type == 'health':
                        entity.health += powerup.intensity
                    if powerup.type == 'shield':
                        entity.is_invulnerable_counter += powerup.intensity
                    self[new_pos_x, new_pos_y].powerup = None
            self[entity.pos.x, entity.pos.y].content = Tile()     
            entity.move(x, y)
            self[entity.pos.x, entity.pos.y].content = entity
        

    def new_game(self, stage: list[list[int]]) -> None:

        self.bullet: Bullet | None = None
        self.enemies: list[Tank] = []
        self.projectiles: list[Bullet] = []
        self.powerups: list[Powerup] = []

        for i in range(len(stage)):
            for j in range(len(stage)):
                if stage[i][j] == 0:
                    self[i, j] = CellState()
                if stage[i][j] == 1:
                    if self.player:
                        self[i, j] = CellState(Tank(Point(i, j), 'N', self.player.health, self.player.ammo))
                    else:
                        self.player = Tank(Point(i, j), 'N')
                        self[i, j] = CellState(self.player)
                if stage[i][j] == 2:
                    self[i, j] = CellState(Tile('Wall', health = 3))
                if stage[i][j] == 3:
                    self.enemies.append(enemy := Tank(Point(i, j), 'N'))
                    self[i, j] = CellState(enemy)
                if stage[i][j] == 4:
                    self.powerups.append(powerup := Powerup('bullet', 3))
                    self[i, j] = CellState(Tile(), powerup)
                if stage[i][j] == 5:
                    self.powerups.append(powerup := Powerup('shield', 10))
                    self[i, j] = CellState(Tile(), powerup)
                if stage[i][j] == 6:
                    self.powerups.append(powerup := Powerup('health', 3))
                    self[i, j] = CellState(Tile(), powerup)

    #for title and gameover scenes
    def draw_next_stage(self) -> None:
        txt: str = f"STAGE {self.current_stage} CLEARED"
        px.text(64, 50, txt, 7)

        px.text(64, 70, f"SCORE: {self.score}", 7)
        px.text(40, 126, "PRESS --ENTER-- to CONTINUE", 15)

    def draw_title_scene(self) -> None:
        px.text(64, 50, "BATTLE CITY", 7)
        px.text(43, 126, "PRESS --ENTER-- to PLAY", 15,)
    
    def draw_gameover_scene(self) -> None:
        px.text(66, 50, "GAME OVER", 8)
        px.text(40, 126, "PRESS --N-- to PLAY AGAIN", 13)

    def update_gameover_scene(self) -> None:
        if px.btnp(px.KEY_N):
            self.scene = SCENE_TITLE
            self.new_game(self.stage)

    def update_title_scene(self):
        if px.btnp(px.KEY_RETURN):
            self.scene = SCENE_PLAY

    def update_next_stage(self) -> None:
        if px.btnp(px.KEY_RETURN):
            self.current_stage += 1
            self.new_game(TRY_STAGE['STAGE'][self.current_stage - 1]['stage'])
            self.scene = SCENE_PLAY
    
    #this is where the game updates
    def draw_cell(self, i: int, j: int, x: int, y: int) -> None:
        if self.scene == SCENE_TITLE:
            self.draw_title_scene()

        if self.scene == SCENE_GAMEOVER:
            self.current_stage += 1
            self.draw_gameover_scene()

        if self.scene == SCENE_STAGE_CLEAR:
            self.draw_next_stage()

        elif self.scene == SCENE_PLAY:
            if self[i, j].content == self.player: #PLAYER
                if self.player.facing == 'N':
                    px.blt(x + 1, y + 1, 0, 0, 0, DIM, DIM, 11)
                if self.player.facing == 'S':
                    px.blt(x + 1, y + 1, 0, 32, 0, DIM, DIM, 11)
                if self.player.facing == 'W':
                    px.blt(x + 1, y + 1, 0, 16, 0, DIM, DIM, 11)
                if self.player.facing == 'E':
                    px.blt(x + 1, y + 1, 0, 48, 0, DIM, DIM, 11)
                px.text(x, y, str(self.player.ammo), 7)
                px.text(x + 16, y, str(self.player.health), 7)
                if self.player.is_invulnerable_counter:
                    px.text(x + 8, y + 8, str(self.player.is_invulnerable_counter), 7)

            if (enemy := self[i, j].content) in self.enemies:
                if enemy.facing == 'N':
                    px.blt(x + 1, y + 1, 0, 0, 0, DIM, DIM, 11)
                if enemy.facing == 'S':
                    px.blt(x + 1, y + 1, 0, 32, 0, DIM, DIM, 11)
                if enemy.facing == 'W':
                    px.blt(x + 1, y + 1, 0, 16, 0, DIM, DIM, 11)
                if enemy.facing == 'E':
                    px.blt(x + 1, y + 1, 0, 48, 0, DIM, DIM, 11)
                
            if self[i, j] == CellState(Tile('Wall', health=3)): #BLOCKAGE health 3
                px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)
            
            if self[i, j] == CellState(Tile('Wall', health=2)): #BLOCKAGE health 2
                px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)

            if self[i, j] == CellState(Tile('Wall', health=1)): #BLOCKAGE health 1
                px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 11)

            if self.bullet:
                if self[i, j].content == self.bullet:
                    px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 11)
            
            if (projectile := self[i, j].content) in self.projectiles:
                px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 11)
            
            if (powerup := self[i, j].powerup) in self.powerups:
                if powerup.type == 'bullet':
                    px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 11)
                elif powerup.type == 'health':
                    px.rect(x + 1, y + 1, 8, 8, 17)
                elif powerup.type == 'shield':
                    px.rect(x + 1, y + 1, 8, 8, 10)





    def pre_draw_grid(self) -> None:
        px.cls(0)

        # performs graphics drawing before the main grid is drawn
        # drawing the background image (e.g. via pyxel.cls) can be done here

    def post_draw_grid(self) -> None:
        # performs graphics drawing after the main grid is drawn
        ...

my_game = MyGame()

my_game.run(title="Boom City", fps=FPS)