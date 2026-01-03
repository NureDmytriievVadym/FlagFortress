import json, base64
from models import *
from enemy import *
from weapons import *

_LEVEL_ENCODING = 'utf-16'

loaded_levels: list[GameLevel] = []

def get_type(type_name: str) -> type:
    return globals().get(type_name, type(None))

def load_level_objects(level: GameLevel) -> None:
    level.objects = []
    if level.objects_to_load == None: return
    for level_obj in level.objects_to_load:
        level_obj_type = get_type(level_obj["type"])
        level.objects.append(level_obj_type.deserialize(level_obj))

def load_entity_weapons(ent: Entity) -> None:
    ent.weapons = []
    if ent.weapons_to_load is None: return
    for wep in ent.weapons_to_load:
        wep_type = get_type(wep["name"])
        ent.set_weapon(wep_type.deserialize(wep))
        
def save_level_raw(level: GameLevel) -> str:
    return json.dumps(level.serialize())

def save_level(level: GameLevel) -> bytearray:
    b: bytearray = bytearray()
    b.extend('FF01'.encode('utf-8'))
    b.extend('LV'.encode('utf-8'))
    serial: bytes = base64.b64encode(json.dumps(level.serialize()).encode(_LEVEL_ENCODING))
    b.extend(len(serial).to_bytes(length=4))
    b.extend(serial)
    b.extend(int(0).to_bytes(length=1))
    return b

def save_levels(levels: list[GameLevel]) -> bytearray:
    b: bytearray = bytearray()
    b.extend('FF01'.encode('utf-8'))
    b.extend('LC'.encode('utf-8'))
    b.extend(len(levels).to_bytes(length=4))
    for level in levels:
        serial: bytes = base64.b64encode(json.dumps(level.serialize()).encode(_LEVEL_ENCODING))
        b.extend(len(serial).to_bytes(length=4))
        b.extend(serial)
        b.extend(int(0).to_bytes(length=1))
    return b

def save_level_to_file(path: str, level: GameLevel) -> bool:
    b = save_level(level=level)
    try:
        with open(path, "wb") as f: f.write(b)
    except: return False
    return True

def save_levels_to_file(path: str, levels: list[GameLevel]) -> bool:
    b = save_levels(levels=levels)
    try:
        with open(path, "wb") as f: f.write(b)
    except: return False
    return True

def load_level_raw(data: str) -> GameLevel:
    serial = json.loads(data)
    level = GameLevel.deserialize(serial)
    load_level_objects(level)
    for ent in [obj for obj in level.objects if issubclass(type(obj), Entity)]: load_entity_weapons(ent)
    loaded_levels.append(level)
    return level

def load_level(b: bytearray) -> GameLevel:
    if(b[0:6].decode('utf-8') != 'FF01LV'): raise Exception("Incorrect level format")
    serial_len = int.from_bytes(b[6:10])
    serial: str = json.loads(base64.b64decode(b[10:10+serial_len]).decode(_LEVEL_ENCODING))
    level = GameLevel.deserialize(serial)
    load_level_objects(level)
    for ent in [obj for obj in level.objects if issubclass(type(obj), Entity)]: load_entity_weapons(ent)
    loaded_levels.append(level)
    return level

def load_levels(b: bytearray) -> list[GameLevel]:
    levels = []
    if(b[0:6].decode('utf-8') != 'FF01LC'): raise Exception("Incorrect level collection format")
    level_count = int.from_bytes(b[6:10])
    cursor = 10
    for i in range(level_count):
        serial_len = int.from_bytes(b[cursor:cursor+4])
        serial: str = json.loads((base64.b64decode(b[cursor+4:cursor+4+serial_len])).decode(_LEVEL_ENCODING))
        cursor += 4 + serial_len + 1
        level = GameLevel.deserialize(serial)
        load_level_objects(level)
        for ent in [obj for obj in level.objects if issubclass(type(obj), Entity)]: load_entity_weapons(ent)
        loaded_levels.append(level)
        levels.append(level)
    return levels

def load_level_from_file(path: str, level: GameLevel) -> bool:
    b: bytearray = None
    try:
        with open(path, "rb") as f: b = f.read()
    except: return None
    if b is None: raise Exception("Couldn't load level serial from file")
    return load_level(b)

def load_levels_from_file(path: str, level: GameLevel) -> bool:
    b: bytearray = None
    try:
        with open(path, "rb") as f: b = f.read()
    except: return None
    if b is None: raise Exception("Couldn't load level collection serial from file")
    return load_levels(b)

BUILTIN_LEVEL_ZOO = GameLevel("Zoo", [])
BUILTIN_LEVEL_ZOO.description = "Built-in level that has a bit of everything"
BUILTIN_LEVEL_ZOO.size = Vector2(10, 18)
BUILTIN_LEVEL_ZOO.objects.append(Label(Vector2(1, 1), "Below is every object in the game"))
BUILTIN_LEVEL_ZOO.objects.append(GameObject(Vector2(3, 1), ' '))
BUILTIN_LEVEL_ZOO.objects.append(Solid(Vector2(3, 3)))
BUILTIN_LEVEL_ZOO.objects.append(Wall(Vector2(3, 5)))
BUILTIN_LEVEL_ZOO.objects.append(Spawn(Vector2(3, 7)))
BUILTIN_LEVEL_ZOO.objects.append(Flag(Vector2(3, 9)))
BUILTIN_LEVEL_ZOO.objects.append(Hazard(Vector2(3, 11)))
BUILTIN_LEVEL_ZOO.objects.append(ItemPickup(Vector2(5, 1)))
BUILTIN_LEVEL_ZOO.objects.append(HealthPickup(Vector2(5, 3)))
BUILTIN_LEVEL_ZOO.objects.append(ArmorPickup(Vector2(5, 5)))
BUILTIN_LEVEL_ZOO.objects.append(AmmoPickup(Vector2(5, 7)))

BUILTIN_LEVEL_ZOO_weapon_pickup_pistol = WeaponPickup(Vector2(5, 9))
BUILTIN_LEVEL_ZOO.objects.append(BUILTIN_LEVEL_ZOO_weapon_pickup_pistol)

BUILTIN_LEVEL_ZOO_weapon_pickup_shotgun = WeaponPickup(Vector2(5, 11))
BUILTIN_LEVEL_ZOO_weapon_pickup_shotgun.weapon_name = "Shotgun"
BUILTIN_LEVEL_ZOO.objects.append(BUILTIN_LEVEL_ZOO_weapon_pickup_shotgun)

BUILTIN_LEVEL_ZOO_weapon_pickup_railgun = WeaponPickup(Vector2(7, 1))
BUILTIN_LEVEL_ZOO_weapon_pickup_railgun.weapon_name = "Railgun"
BUILTIN_LEVEL_ZOO.objects.append(BUILTIN_LEVEL_ZOO_weapon_pickup_railgun)

BUILTIN_LEVEL_ZOO.objects.append(Entity(Vector2(7, 3)))

BUILTIN_LEVEL_ZOO_enemy = Enemy(Vector2(7, 5))
BUILTIN_LEVEL_ZOO_enemy.ai_disabled = True
BUILTIN_LEVEL_ZOO.objects.append(BUILTIN_LEVEL_ZOO_enemy)

BUILTIN_LEVEL_ZOO_ghost = Ghost(Vector2(7, 7))
BUILTIN_LEVEL_ZOO_ghost.ai_disabled = True
BUILTIN_LEVEL_ZOO.objects.append(BUILTIN_LEVEL_ZOO_ghost)

BUILTIN_LEVEL_ZOO_sentry = Sentry(Vector2(7, 9))
BUILTIN_LEVEL_ZOO_sentry.ai_disabled = True
BUILTIN_LEVEL_ZOO_sentry.set_weapon(WeaponManager.CreateWeapon(name="SentryGun"))
BUILTIN_LEVEL_ZOO.objects.append(BUILTIN_LEVEL_ZOO_sentry)

BUILTIN_LEVEL_ZOO_mercenary = Mercenary(Vector2(7, 11))
BUILTIN_LEVEL_ZOO_mercenary.ai_disabled = False
BUILTIN_LEVEL_ZOO_mercenary.set_weapon(WeaponManager.CreateWeapon(name="EnemyShotgun"))
BUILTIN_LEVEL_ZOO.objects.append(BUILTIN_LEVEL_ZOO_mercenary)