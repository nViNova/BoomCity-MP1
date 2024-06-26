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

DIM = 16
FPS = 60

STAGE: list[list[int]] = TRY_STAGE['STAGE'][CURR_STAGE - 1]['stage']


class Entity:

    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W'] = 'N', health: int = 1):
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
    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W'] = 'N', health: int = 3, ammo: int = 10, attack_dmg: int = 1, speed: int = 2, type: Literal['Health', 'Attack', 'Speed', 'Normie'] = 'Normie'):
        self.ammo: int = ammo
        self.attack_dmg: int = attack_dmg
        self.speed: int = speed
        self.type: Literal['Health', 'Attack', 'Speed', 'Normie'] = type
        super().__init__(pos, facing, health)

    def __repr__(self) -> str:
        return f'Tank with {self.health} health, {self.ammo} ammo, {self.alive} alive, {self.speed} speed, {self.attack_dmg} attack, {self.__hash__}'

class Bullet(Entity):

    def __init__(self, pos: Point, facing: Literal['N', 'E', 'S', 'W'], intensity: int = 1):
        self.intensity: int = intensity
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

    def behind(self) -> Literal['N', 'E', 'S', 'W']:
        dirs: list[Literal['N', 'E', 'S', 'W']] = ['N', 'E', 'S', 'W']
        return dirs[(dirs.index(self.facing) + 2) % 4]

@dataclass
class Powerup:
    type: Literal['health', 'bullet', 'shield', 'win']
    intensity: int = 1
      
@dataclass
class Tile:
    # 11 12 13 14 15 16 17 18 19
    type: Literal['Forest', 'Home', 'Water', 'Stone', 'Brick', 'Mirror', 'EnemySpawner', 'PowerupSpawner', None] = None
    enemy_type: Literal['Health', 'Attack', 'Speed', 'Normie', None] = None
    powerup_type: Powerup | None = None
    rotation: Literal['\\', '/', None] = None
    dir_broke: Literal['N', 'E', 'W', 'S', None] =  None
    health: int = 0

    def damage(self, damage: int = 1, dir_broke: Literal['N', 'E', 'W', 'S', None] = None) -> None | bool:
        if self.type == 'Brick':
            self.health -= damage
            self.dir_broke = dir_broke
            if self.health < 1:
                self.type = None
                self.dir_broke = None
        elif self.type == 'Home':
            return True

@dataclass
class CellState:
    tile: Tile = field(default_factory=Tile)
    entity: Entity | None = None
    projectile: Bullet | None = None
    powerup: Powerup | None = None

MOVABLE: list[Literal['Forest', 'EnemySpawner', 'PowerupSpawner', None]] = [None, 'Forest', 'EnemySpawner', 'PowerupSpawner']

class MyGame(pg.PyxelGrid[CellState]):

    def __init__(self):
        self.current_stage = CURR_STAGE
        self.score = CURR_SCORE
        self.stage: list[list[int]] = TRY_STAGE['STAGE'][self.current_stage - 1]['stage']
        self.scene = SCENE_TITLE
        self.enemy_spawn_rate = 10
        self.powerup_spawn_rate = 6
        
        super().__init__(r=len(self.stage), c=len(self.stage[0]), dim=DIM, layerc=3)

    def init(self) -> None:
        self.new_game(self.stage)
        px.mouse(True)
        px.load("main.pyxres")

    def update(self) -> None:

        if not px.frame_count % (FPS * self.enemy_spawn_rate):
            self.spawn_enemies()
        if not px.frame_count % (FPS * self.powerup_spawn_rate):
            self.spawn_powerups()
    
        if self.scene == SCENE_TITLE:
            self.update_title_scene()

        if self.player.health == 0 or not self.is_home_active:
            self.scene = SCENE_GAMEOVER
            self.update_gameover_scene()

        if len(self.enemies) == 0:
            self.scene = SCENE_STAGE_CLEAR
            self.update_next_stage()


        if px.btnp(px.KEY_W, hold=12, repeat=12) or px.btnp(px.KEY_UP, repeat=12):
            self.attempt_move(0, 1, self.player)
        if px.btnp(px.KEY_S, repeat=12) or px.btnp(px.KEY_DOWN, repeat=12):
            self.attempt_move(0, -1, self.player)
        if px.btnp(px.KEY_D, repeat=12) or px.btnp(px.KEY_RIGHT, repeat=12):
            self.attempt_move(1, 0, self.player)
        if px.btnp(px.KEY_A, repeat=12) or px.btnp(px.KEY_LEFT, repeat=12):
            self.attempt_move(-1, 0, self.player)

        if px.btnp(px.KEY_Q):
            print(self[self.mouse_cell()], self.mouse_cell())
        if px.btnp(px.KEY_P):
            print(len(self.enemies), ' enemies left')
            print(self.enemies)
        if px.btnp(px.KEY_1):
            for enemy in self.enemies:
                self.enemy_shoot(enemy)
        if px.btnp(px.KEY_2):
            self.enemies = []

        if px.btnp(px.KEY_SPACE, repeat=10):
            self.shoot()
            
        self.update_projectiles()
        self.update_player()
        self.update_enemies()

        


    def is_walkable(self, point: Point) -> bool:
        return self.in_bounds(point.x, point.y) and self[point.x, point.y].tile.type in MOVABLE and self[point.x, point.y].entity is None
    
    def shoot(self) -> None:
        if not self.bullet and self.player.ammo > 0:           
            if self.in_bounds(self.player.front().x, self.player.front().y):
                self.bullet = Bullet(self.player.front(), self.player.facing)
                self[self.bullet.pos.x, self.bullet.pos.y].projectile = self.bullet

            self.player.ammo -= 1

    
    def enemy_shoot(self, enemy: Tank) -> None:
        if enemy.ammo > 0:
            if self.in_bounds(enemy.front().x, enemy.front().y):
                self.projectiles.append(bullet := Bullet(enemy.front(), enemy.facing))
                self[bullet.pos.x, bullet.pos.y].projectile = bullet
            
            enemy.ammo -= 1
    
    def move_bullet(self) -> None:
        if self.bullet:

            Current = self.bullet.pos.x, self.bullet.pos.y
            Front = self.bullet.front().x, self.bullet.front().y


            if ((tile := self[Current].tile).type) == 'Mirror':
                if tile.rotation == '\\':
                    if self.bullet.facing in ['N', 'S']:
                        self.bullet.rotate('CCW')
                    else:
                        self.bullet.rotate('CW')
                elif tile.rotation == '/':
                    if self.bullet.facing in ['N', 'S']:
                        self.bullet.rotate('CW')
                    else:
                        self.bullet.rotate('CCW')
                    
            if self[Current].tile.health:
                self.is_home_active = not self[Current].tile.damage(dir_broke=self.bullet.behind())
                self[Current].projectile = None
                self.bullet = None
            elif not self.in_bounds(*Front):
                self[Current].projectile = None
                self.bullet = None
            else:
                self[Current].projectile = None
                self.bullet.forward()
                self[self.bullet.pos.x, self.bullet.pos.y].projectile = self.bullet
    
    def move_projectile(self, projectile: Bullet) -> None:
        Current = (projectile.pos.x, projectile.pos.y)
        Front = projectile.front().x, projectile.front().y

        if ((tile := self[Current].tile).type) == 'Mirror':
            if tile.rotation == '\\':
                if projectile.facing in ['N', 'S']:
                    projectile.rotate('CCW')
                else:
                    projectile.rotate('CW')
            elif tile.rotation == '/':
                if projectile.facing in ['N', 'S']:
                    projectile.rotate('CW')
                else:
                    projectile.rotate('CCW')

        if self[Current].tile.health:
            self.is_home_active = not self[Current].tile.damage(dir_broke=projectile.behind())
            self[Current].projectile = None
            self.projectiles.remove(projectile)
        elif not self.in_bounds(*Front):
            self[Current].projectile = None
            self.projectiles.remove(projectile)
        else:
            self[Current].projectile = None
            projectile.forward()
            self[projectile.pos.x, projectile.pos.y].projectile = projectile


    def update_projectiles(self) -> None:
        for projectile in self.projectiles:
            if self.in_bounds(projectile.front().x, projectile.front().y):
                if bullet := self[projectile.front().x, projectile.front().y].projectile:
                    self[projectile.pos.x, projectile.pos.y].projectile = None
                    self[projectile.front().x, projectile.front().y].projectile = None

                    self.projectiles.remove(projectile)

                    if bullet is self.bullet:
                        self.bullet = None
                    else:
                        self.projectiles.remove(bullet)

        if not px.frame_count % (FPS // 10):
            if self.bullet:
                self.move_bullet()
            for projectile in self.projectiles:
                self.move_projectile(projectile)

    def update_enemies(self) -> None:
        if self.enemies:
            for enemy in self.enemies:

                if enemy.alive and (self[enemy.pos.x, enemy.pos.y].projectile is self.bullet):
                    if self.bullet:
                        enemy.damage(self.bullet.intensity)
                    self[enemy.pos.x, enemy.pos.y].projectile = None
                    self.bullet = None
                    
                if enemy.alive:
                    self.enemy_move(enemy)
                else:
                    self.enemies.remove(enemy)
                    self[enemy.pos.x, enemy.pos.y].entity = None
    
    def update_player(self) -> None:
    
        if projectile := self[self.player.pos.x, self.player.pos.y].projectile:
            self.player.damage(projectile.intensity)
            self[self.player.pos.x, self.player.pos.y].projectile = None

            if projectile is self.bullet:
                self.bullet = None
            else:
                self.projectiles.remove(projectile)

        if not px.frame_count % FPS:
            if self.player.is_invulnerable_counter:
                print(self.player.is_invulnerable_counter, "seconds left of shield")
                self.player.is_invulnerable_counter -= 1

    
    def enemy_move(self, enemy: Tank) -> None:
        if not px.frame_count % (FPS // enemy.speed):
            roll: int = randint(0, 6)
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
    
    def spawn_enemies(self):
        for spot in self.enemy_spawn_spots:
            if not self[spot].entity:
                if self.enemy_spawn_spots[spot] == 'Attack':
                    self.enemies.append(entity := Tank(Point(spot[0], spot[1]), attack_dmg=2, type='Attack'))
                elif self.enemy_spawn_spots[spot] == 'Health':
                    self.enemies.append(entity := Tank(Point(spot[0], spot[1]), health=6, type='Health'))
                elif self.enemy_spawn_spots[spot] == 'Speed':
                    self.enemies.append(entity := Tank(Point(spot[0], spot[1]),  speed=4, type='Speed'))
                else:
                    self.enemies.append(entity := Tank(Point(spot[0], spot[1])))
                
                self[spot].entity = entity
    
    def spawn_powerups(self):
        for spot in self.powerup_spawn_spots:
            if not self[spot].powerup:
                self.powerups.append(powerup := self.powerup_spawn_spots[spot])
                self[spot].powerup = powerup



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
            self[entity.pos.x, entity.pos.y].entity = None
            entity.move(x, y)
            self[entity.pos.x, entity.pos.y].entity = entity
        

    def new_game(self, stage: list[list[int]], player: Tank | None = None) -> None:

        self.bullet: Bullet | None = None
        self.enemies: list[Tank] = []
        self.enemy_spawn_spots: dict[tuple[int, int], Literal['Health', 'Attack', 'Speed', 'Normie']] = {}
        self.projectiles: list[Bullet] = []
        self.powerups: list[Powerup] = []
        self.powerup_spawn_spots: dict[tuple[int, int], Powerup] = {}
        self.is_home_active: bool = True

        for i in range(len(stage)):
            for j in range(len(stage)):
                if stage[i][j] == 0:
                    self[i, j] = CellState()
                elif stage[i][j] == 1:
                    if player:
                        self.player = Tank(Point(i, j), player.facing, player.health, player.ammo)
                    else:
                        self.player = Tank(Point(i, j), 'N')
                    self[i, j] = CellState(Tile(), self.player)
                elif stage[i][j] == 2:
                    self.enemy_spawn_spots.update({(i, j): 'Normie'})
                    self[i, j] = CellState(Tile('EnemySpawner', enemy_type='Normie'))
                elif stage[i][j] == 11:
                    self[i, j] = CellState(Tile('Forest'))
                elif stage[i][j] == 12:
                    self[i, j] = CellState(Tile('Home', health = 1))
                elif stage[i][j] == 13:
                    self[i, j] = CellState(Tile('Water'))
                elif stage[i][j] == 14:
                    self[i, j] = CellState(Tile('Stone', health = 1))
                elif stage[i][j] == 15:
                    self[i, j] = CellState(Tile('Brick', health = 2))
                elif stage[i][j] == 16:
                    self[i, j] = CellState(Tile('Mirror', rotation='\\'))
                elif stage[i][j] == 17:
                    self[i, j] = CellState(Tile('Mirror', rotation='/'))
                elif stage[i][j] == 18:
                    self.enemy_spawn_spots.update({(i, j): 'Health'})
                    self[i, j] = CellState(Tile('EnemySpawner', enemy_type='Health'))
                elif stage[i][j] == 19:
                    self.enemy_spawn_spots.update({(i, j): 'Attack'})
                    self[i, j] = CellState(Tile('EnemySpawner', enemy_type='Attack'))
                elif stage[i][j] == 20:
                    self.enemy_spawn_spots.update({(i, j): 'Speed'})
                    self[i, j] = CellState(Tile('EnemySpawner', enemy_type='Speed'))
                elif stage[i][j] == 21:
                    self.powerup_spawn_spots.update({(i, j): (powerup := Powerup('bullet', 3))})
                    self[i, j] = CellState(Tile('PowerupSpawner', powerup_type=powerup))
                elif stage[i][j] == 22:
                    self.powerup_spawn_spots.update({(i, j): (powerup := Powerup('shield', 7))})
                    self[i, j] = CellState(Tile('PowerupSpawner', powerup_type=powerup))
                elif stage[i][j] == 23:
                    self.powerup_spawn_spots.update({(i, j): (powerup := Powerup('health'))})
                    self[i, j] = CellState(Tile('PowerupSpawner', powerup_type=powerup))

        if px.frame_count > 0:
            self.spawn_powerups()
            self.spawn_enemies()
                

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
            self.current_stage = CURR_STAGE
            self.new_game(self.stage)

    def update_title_scene(self):
        if px.btnp(px.KEY_RETURN):
            self.scene = SCENE_PLAY
 
    def update_next_stage(self) -> None:
        if px.btnp(px.KEY_RETURN):
            self.current_stage += 1
            self.new_game(TRY_STAGE['STAGE'][self.current_stage - 1]['stage'], self.player)
            self.scene = SCENE_PLAY
    
    #this is where the game updates
    def draw_cell_layer(self, i: int, j: int, x: int, y: int, layeri: int) -> None:
        
        if self.scene == SCENE_TITLE:
            self.draw_title_scene()

        if self.scene == SCENE_GAMEOVER:
            self.draw_gameover_scene()

        if self.scene == SCENE_STAGE_CLEAR:
            self.draw_next_stage()

        elif self.scene == SCENE_PLAY:

            cell = self[i, j]

            if layeri == 0:
                if cell.entity is self.player: #PLAYER
                    if self.player.facing == 'N':
                        px.blt(x + 1, y + 1, 0, 0, 0, DIM, DIM, 0)
                    if self.player.facing == 'S':
                        px.blt(x + 1, y + 1, 0, 48, 0, DIM, DIM, 0)
                    if self.player.facing == 'W':
                        px.blt(x + 1, y + 1, 0, 16, 0, DIM, DIM, 0)
                    if self.player.facing == 'E':
                        px.blt(x + 1, y + 1, 0, 32, 0, DIM, DIM, 0)
                    px.text(x, y, str(self.player.ammo), 7)
                    px.text(x + 16, y, str(self.player.health), 7)
                    if self.player.is_invulnerable_counter:
                        px.text(x + 8, y + 8, str(self.player.is_invulnerable_counter), 7)
                
                elif (tile := cell.tile).type == 'Mirror':
                    if tile.rotation == '\\':
                        px.blt(x + 1, y + 1, 0, 16, 80, DIM, DIM, 0)
                        
                    elif tile.rotation == '/':
                        px.blt(x + 1, y + 1, 0, 0, 80, DIM, DIM, 0)
                        
                elif cell.tile.type == 'Water':
                    px.blt(x + 1, y + 1, 0, 32, 64, DIM, DIM, 0)

                elif cell.tile.type == 'Home':
                    px.blt(x + 1, y + 1, 0, 32, 80, DIM, DIM, 0)
            
                elif (enemy := cell.entity) in self.enemies:
                    if enemy.facing == 'N':
                        px.blt(x + 1, y + 1, 0, 0, 112, DIM, DIM, 0)
                    if enemy.facing == 'S':
                        px.blt(x + 1, y + 1, 0, 48, 112, DIM, DIM, 0)
                    if enemy.facing == 'W':
                        px.blt(x + 1, y + 1, 0, 16, 112, DIM, DIM, 0)
                    if enemy.facing == 'E':
                        px.blt(x + 1, y + 1, 0, 32, 112, DIM, DIM, 0)

            elif layeri == 1:
                if (projectile := cell.projectile) in self.projectiles:
                    if projectile.facing == 'N':
                        px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 0)
                    if projectile.facing == 'E':
                        px.blt(x + 1, y + 1, 0, 32, 16, DIM, DIM, 0)
                    if projectile.facing == 'W':
                        px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 0)
                    if projectile.facing == 'S':
                        px.blt(x + 1, y + 1, 0, 48, 16, DIM, DIM, 0)

                if self.bullet:
                    if cell.projectile is self.bullet:
                        if self.bullet.facing == 'N':
                            px.blt(x + 1, y + 1, 0, 0, 16, DIM, DIM, 0)
                        if self.bullet.facing == 'E':
                            px.blt(x + 1, y + 1, 0, 32, 16, DIM, DIM, 0)
                        if self.bullet.facing == 'W':
                            px.blt(x + 1, y + 1, 0, 16, 16, DIM, DIM, 0)
                        if self.bullet.facing == 'S':
                            px.blt(x + 1, y + 1, 0, 48, 16, DIM, DIM, 0)
                    
                if (powerup := cell.powerup) in self.powerups:
                    if powerup.type == 'bullet':
                        px.blt(x + 1, y + 1, 0, 32, 96, DIM, DIM, 0)
                    elif powerup.type == 'health':
                        px.blt(x + 1, y + 1, 0, 16, 96, DIM, DIM, 0)
                    elif powerup.type == 'shield':
                        px.blt(x + 1, y + 1, 0, 0, 96, DIM, DIM, 0)
                                            
            elif layeri == 2:
                if cell.tile.type == 'Forest':
                    px.blt(x + 1, y + 1, 0, 48, 64, DIM, DIM, 0)

                elif (tile := cell.tile) == Tile('Brick', health=2): #BLOCKAGE health 2
                    px.blt(x + 1, y + 1, 0, 0, 64, DIM, DIM, 0)

                elif tile.type == 'Brick' and tile.health == 1: #BLOCKAGE health 1
                    if tile.dir_broke == 'N':
                        px.blt(x + 1, y + 1, 0, 32, 48, DIM, DIM, 0)
                    if tile.dir_broke == 'S':
                        px.blt(x + 1, y + 1, 0, 16, 48, DIM, DIM, 0)
                    if tile.dir_broke == 'E':
                        px.blt(x + 1, y + 1, 0, 48, 48, DIM, DIM, 0)
                    if tile.dir_broke == 'W':
                        px.blt(x + 1, y + 1, 0, 0, 48, DIM, DIM, 0)
                        
                elif tile.type == 'Stone':
                    px.blt(x + 1, y + 1, 0, 16, 64, DIM, DIM, 0)
            
           




    def pre_draw_grid(self) -> None:
        px.cls(0)

        # performs graphics drawing before the main grid is drawn
        # drawing the background image (e.g. via pyxel.cls) can be done here

    def post_draw_grid(self) -> None:
        # performs graphics drawing after the main grid is drawn
        ...

my_game = MyGame()

my_game.run(title="Boom City", fps=FPS)