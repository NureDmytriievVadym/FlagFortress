import config
import math
import builtins

def sign(a):
    if a == 0: return 0
    else: return 1 if a > 0 else -1

class Vector2:
    def __init__(self, y: int, x: int):
        self.y = int(y)
        self.x = int(x)

    def copy(self):
        return Vector2(self.y, self.x)
    
    def length(self):
        return math.sqrt(self.y * self.y + self.x * self.x)

    def normalize(self):
        l = self.length()
        return Vector2(round(self.y / l), round(self.x / l))

    def add(self, y: int, x: int):
        return Vector2(self.y + y, self.x + x)

    def mul(self, multiplier: float):
        return Vector2(round(self.y * multiplier), round(self.x * multiplier))

    def __eq__(self, value):
        return self.y == value.y and self.x == value.x

    def __str__(self):
        return f"({self.y}; {self.x})"

    def serialize(self) -> dict:
        return {
            "y": self.y,
            "x": self.x
        }

    @staticmethod
    def deserialize(data: dict) -> "Vector2":
        return Vector2(data["y"], data["x"])
    
    @staticmethod
    def from_Vector2F(v2: "Vector2F") -> "Vector2":
        return Vector2(v2.y, v2.x)

class Vector2F(Vector2):
    def __init__(self, y: float, x: float):
        self.y = float(y)
        self.x = float(x)

    def copy(self):
        return Vector2F(self.y, self.x)
    
    def length(self):
        return math.sqrt(self.y * self.y + self.x * self.x)

    def normalize(self):
        l = self.length()
        return Vector2(self.y / l, self.x / l)

    def add(self, y: float, x: float):
        return Vector2F(self.y + y, self.x + x)

    def mul(self, multiplier: float):
        return Vector2F(self.y * multiplier, self.x * multiplier)

    def __eq__(self, value):
        return self.y == value.y and self.x == value.x

    def __str__(self):
        return f"({self.y}; {self.x})"

    def serialize(self) -> dict:
        return {
            "y": self.y,
            "x": self.x
        }

    @staticmethod
    def deserialize(data: dict) -> "Vector2F":
        return Vector2F(data["y"], data["x"])
    
    @staticmethod
    def from_Vector2(v2: Vector2) -> "Vector2F":
        return Vector2F(v2.y, v2.x)

class GameObject:
    def __init__(self, pos: Vector2, symbol: str, order: int = 0):
        if(type(pos) != Vector2): raise Exception("GameObject initialized incorrectly")
        self.pos = pos
        self.symbol = symbol
        self.hidden = False
        self.order = order

        self.deleted = False
    
    @property
    def type(self): return type(self).__name__

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "pos": self.pos.serialize(),
            "symbol": self.symbol,
            "hidden": self.hidden,
            "order": self.order
        }

    @staticmethod
    def deserialize(data: dict) -> "GameObject":
        pos = Vector2.deserialize(data["pos"])
        obj = GameObject(pos, data["symbol"], data["order"])
        obj.hidden = data["hidden"]
        return obj

class Wall(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "⬛", breakable: bool = False):
        GameObject.__init__(self, pos, symbol)
        self.breakable = breakable

    @staticmethod
    def from_parent(obj: GameObject, breakable: bool = False) -> "Wall":
        return Wall(pos=obj.pos, symbol=obj.symbol, breakable=breakable)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data["breakable"] = self.breakable
        return data

    @staticmethod
    def deserialize(data: dict) -> "Wall":
        obj = Wall.from_parent(GameObject.deserialize(data))
        obj.breakable = data["breakable"]
        return obj

class Label(GameObject):
    def __init__(self, pos: Vector2, text: str = "Label", text_attr: int = 0):
        GameObject.__init__(self, pos, 'L')
        self.order = -1
        self.text = text
        self.text_attr = text_attr

    @staticmethod
    def from_parent(obj: GameObject, text: str = "Label", text_attr: int = 0) -> "Label":
        return Label(pos=obj.pos, text=text, text_attr=text_attr)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data["text"] = self.text
        data["text_attr"] = self.text_attr
        return data

    @staticmethod
    def deserialize(data: dict) -> "Label":
        obj = Label.from_parent(GameObject.deserialize(data))
        obj.text = data["text"]
        obj.text_attr = data["text_attr"]
        return obj

class Entity(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "🐏"):
        GameObject.__init__(self, pos, symbol)
        self.health = 3
        self.armor = 0
        self._direction = Vector2F(0, 1)
        self.invulnerable = False
        self.selected_weapon_index = 0
        self.weapons = []
        self.weapons_to_load = None
    
    @property
    def direction(self) -> Vector2:
        return self._direction.normalize()
    
    @direction.setter
    def direction(self, value: Vector2F):
        if not type(value) is Vector2F: raise Exception("Entity direction set incorrectly")
        self._direction = value

    @staticmethod
    def from_parent(obj: GameObject) -> "Entity":
        return Entity(pos=obj.pos, symbol=obj.symbol)

    def serialize(self) -> dict:
        data = super().serialize()
        data["health"] = self.health
        data["armor"] = self.armor
        data["direction"] = self.direction.serialize()
        data["invulnerable"] = self.invulnerable
        data["selected_weapon_index"] = self.selected_weapon_index
        data["weapons"] = [weapon.serialize() for weapon in self.weapons]
        return data

    @staticmethod
    def deserialize(data: dict) -> "Entity":
        obj = Entity.from_parent(GameObject.deserialize(data))
        obj.health = data["health"]
        obj.armor = data["armor"]
        obj.direction = Vector2F.deserialize(data["direction"])
        obj.invulnerable = data["invulnerable"]
        obj.selected_weapon_index = data["selected_weapon_index"]
        obj.weapons = []
        obj.weapons_to_load = [weapon for weapon in data["weapons"]]
        return obj

class Player(Entity):
    def __init__(self, pos: Vector2, symbol: str = "🐛"):
        Entity.__init__(self, pos, symbol)
        self.has_dash = True
        self.dash_speed = 3
        self.dash_cooldown = 0
        self.order = 100

    @staticmethod
    def from_parent(obj: Entity) -> "Player":
        return Player(pos=obj.pos, symbol=obj.symbol)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data["has_dash"] = self.has_dash
        data["dash_speed"] = self.dash_speed
        data["dash_cooldown"] = self.dash_cooldown
        return data

    @staticmethod
    def deserialize(data: dict) -> "Player":
        obj = Player.from_parent(Entity.deserialize(data))
        obj.has_dash = data["has_dash"]
        obj.dash_speed = data["dash_speed"]
        obj.dash_cooldown = data["dash_cooldown"]
        return obj

class Spawn(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "🔅"):
        GameObject.__init__(self, pos, symbol)

    @staticmethod
    def from_parent(obj: GameObject) -> "Spawn":
        return Spawn(pos=obj.pos, symbol=obj.symbol)
    
    def serialize(self) -> dict:
        data = super().serialize()
        return data

    @staticmethod
    def deserialize(data: dict) -> "Spawn":
        obj = Spawn.from_parent(GameObject.deserialize(data))
        return obj

class Flag(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "🚩"):
        GameObject.__init__(self, pos, symbol)

    @staticmethod
    def from_parent(obj: GameObject) -> "Flag":
        return Flag(pos=obj.pos, symbol=obj.symbol)

    def serialize(self) -> dict:
        data = super().serialize()
        return data

    @staticmethod
    def deserialize(data: dict) -> "Flag":
        obj = Flag.from_parent(GameObject.deserialize(data))
        return obj

class Hazard(GameObject):
    def __init__(self, pos: Vector2, symbol: str = "❌", background: bool = False, breakable: bool = False):
        GameObject.__init__(self, pos, symbol)

    @staticmethod
    def from_parent(obj: GameObject) -> "Hazard":
        return Hazard(pos=obj.pos, symbol=obj.symbol)
    
    def serialize(self) -> dict:
        data = super().serialize()
        return data

    @staticmethod
    def deserialize(data: dict) -> "Hazard":
        obj = Hazard.from_parent(GameObject.deserialize(data))
        return obj

class Projectile(GameObject):
    def __init__(self, pos: Vector2, direction: Vector2, symbol: str = "+", speed: float = 5):
        GameObject.__init__(self, pos, symbol)
        self.subpos = Vector2F(0, 0)
        self.direction = direction.normalize()
        self.speed = speed
    
    @staticmethod
    def from_parent(obj: GameObject, direction: Vector2, symbol: str = "+", speed: float = 5) -> "Projectile":
        return Projectile(pos=obj.pos, symbol=obj.symbol, direction=direction, speed=speed)

    def serialize(self) -> dict:
        data = super().serialize()
        data["subpos"] = self.subpos.serialize()
        data["direction"] = self.direction.serialize()
        data["speed"] = self.speed
        return data

    @staticmethod
    def deserialize(data: dict) -> "Projectile":
        obj = Projectile.from_parent(GameObject.deserialize(data))
        obj.subpos = Vector2F.deserialize(data["subpos"])
        obj.direction = Vector2F.deserialize(data["direction"])
        obj.speed = data["speed"]
        return obj

class PlayerBullet(Projectile):
    def __init__(self, pos: Vector2, direction: Vector2, symbol: str = "+", speed: float = 5, pierce: int = 0):
        Projectile.__init__(self, pos, direction, symbol, speed)
        self.pierce = pierce

    @staticmethod
    def from_parent(obj: Projectile, direction: Vector2, symbol: str = "+", speed: float = 5, pierce: int = 0) -> "PlayerBullet":
        return PlayerBullet(pos=obj.pos, symbol=obj.symbol, direction=direction, speed=speed, pierce=pierce)

    def serialize(self) -> dict:
        data = super().serialize()
        data["pierce"] = self.pierce
        return data

    @staticmethod
    def deserialize(data: dict) -> "PlayerBullet":
        obj = PlayerBullet.from_parent(Projectile.deserialize(data))
        obj.pierce = data["pierce"]
        return obj

class Event:
    def __init__(self, name: str, delay_seconds: float = 0, params = None):
        self.name = name
        self.params = params
        # delay is in ticks
        self.delay = math.ceil(delay_seconds * config.TARGET_TICKRATE)
        self.initial_delay = self.delay

class GameLevel:
    def __init__(self, name: str = "Level", objects: list[GameObject] = []):
        self.name = name
        self.author = 'VadymDmytriiev'
        self.description = 'Built-in level'
        self.starting_weapon_name = "Pistol"
        self.starting_weapon_ammo = 4
        self.starting_weapon_ammo_reserve = 4
        self.starting_health = 4
        self.starting_armor = 0
        self.objects = objects[:]
        self.objects_to_load = None
        self.current_spawn_index = 0

    def copy(self):
        level = GameLevel()
        level.name = self.name
        level.author = self.author
        level.description = self.description
        level.starting_weapon_name = self.starting_weapon_name
        level.starting_weapon_ammo = self.starting_weapon_ammo
        level.starting_weapon_ammo_reserve = self.starting_weapon_ammo_reserve
        level.starting_health = self.starting_health
        level.starting_armor = self.starting_armor
        level.objects = []
        level.objects_to_load = self.objects_to_load
        level.current_spawn_index = self.current_spawn_index
        return level
    
    @property
    def spawns(self):
        return [obj for obj in self.objects if obj.type == "Spawn"]

    @property
    def flags(self):
        return [obj for obj in self.objects if obj.type == "Flag"]

    @property
    def spawn(self):
        return self.spawns[self.current_spawn_index]

    @property
    def flag(self):
        flags = self.flags
        return None if len(flags) == 0 else flags[0]
    
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
    
    def serialize(self) -> dict:
        data = {}
        data["name"] = self.name
        data["author"] = self.author
        data["description"] = self.description
        data["starting_weapon_name"] = self.starting_weapon_name
        data["starting_weapon_ammo"] = self.starting_weapon_ammo
        data["starting_weapon_ammo_reserve"] = self.starting_weapon_ammo_reserve
        data["starting_health"] = self.starting_health
        data["starting_armor"] = self.starting_armor
        data["objects"] = [obj.serialize() for obj in self.objects]
        return data

    @staticmethod
    def deserialize(data: dict) -> "Flag":
        obj = GameLevel()
        obj.name = data["name"]
        obj.author = data["author"]
        obj.description = data["description"]
        obj.starting_weapon_name = data["starting_weapon_name"]
        obj.starting_weapon_ammo = data["starting_weapon_ammo"]
        obj.starting_weapon_ammo_reserve = data["starting_weapon_ammo_reserve"]
        obj.starting_health = data["starting_health"]
        obj.starting_armor = data["starting_armor"]
        obj.objects_to_load = data["objects"]
        return obj
    
class Menu:
    def __init__(self, size: Vector2, caption: str, description: str, options: list[(str, str)]):
        self.size = size
        self.caption = caption
        self.description = description
        self.options_offset = Vector2(0, 0)
        self.options = options
        self.selected_option = 0
        self.frame_symbol = '#'
        self.frame_attr = 0
