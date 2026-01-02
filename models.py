import config
import math

def sign(a):
    if a == 0: return 0
    else: return 1 if a > 0 else -1

class Vector2:
    def __init__(self, y: int, x: int):
        self.y = int(y)
        self.x = int(x)

    def copy(self):
        return Vector2(self.y, self.x)
    
    def normal(self):
        return Vector2(sign(self.y), sign(self.x))

    def add(self, y: int, x: int):
        return Vector2(self.y + y, self.x + x)

    def mul(self, multiplier: float):
        return Vector2(round(self.y * multiplier), round(self.x * multiplier))

    def __eq__(self, value):
        return self.y == value.y and self.x == value.x

    def __str__(self):
        return f"({self.y}; {self.x})"

class GameObject:
    def __init__(self, pos: Vector2, symbol: str, order: int = 0):
        self.pos = pos
        self.symbol = symbol
        self.hidden = False
        self.deleted = False
        self.order = order
    
    @property
    def type(self): return "GameObject"

class Wall(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "⬛", breakable: bool = False):
        GameObject.__init__(self, pos, symbol)
        self.breakable = breakable
    
    @property
    def type(self): return "Wall"

class Player(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "🐛"):
        GameObject.__init__(self, pos, symbol)
        self.health = 1
        self.has_dash = True
        self.dash_speed = 3
        self.invulnerable = False
        self.ammo_left = 0
        self.order = 100
    
    @property
    def type(self): return "Player"

class Spawn(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "🔅", breakable: bool = False):
        GameObject.__init__(self, pos, symbol)
    
    @property
    def type(self): return "Spawn"

class Flag(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "🚩", breakable: bool = False):
        GameObject.__init__(self, pos, symbol)

    @property
    def type(self): return "Flag"

class PlayerBullet(GameObject):
    def __init__(self, pos: Vector2, direction: Vector2, symbol: str = "+", speed: float = 5, pierce: int = 0):
        GameObject.__init__(self, pos, symbol)
        self.direction = direction
        self.speed = speed
        self.pierce = pierce
    
    @property
    def type(self): return "PlayerBullet"

class Event:
    def __init__(self, name: str, delay_seconds: float = 0, params = None):
        self.name = name
        self.params = params
        # delay is in ticks
        self.delay = math.ceil(delay_seconds * config.TICKRATE)
        self.initial_delay = self.delay

class GameLevel:
    def __init__(self, num: int, name: str, starting_ammo: int, objects: list[GameObject]):
        self.num = num
        self.name = name
        self.starting_ammo = starting_ammo
        self.objects = objects[:] # shallow copy
        self._spawn = [obj for obj in objects if obj.type == "Spawn"][0]
        self._flag = [obj for obj in objects if obj.type == "Flag"][0]
    
    @property
    def spawn(self):
        return self._spawn

    @property
    def flag(self):
        return self._flag
    
    @property
    def player(self):
        return self._player
    
    @player.setter
    def player(self, player):
        self._player = player
    
    def add_object(self, o: GameObject):
        self.objects.append(o)
        self.objects.sort(key = lambda x: x.order)

    def delete_object(self, o: GameObject):
        try:
            self.objects.remove(o)
        except:
            pass
        
        o.deleted = True
    
