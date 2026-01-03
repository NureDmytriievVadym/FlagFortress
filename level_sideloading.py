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
    for level_obj in level.objects_to_load:
        level_obj_type = get_type(level_obj["type"])
        level.objects.append(level_obj_type.deserialize(level_obj))

def load_entity_weapons(ent: Entity) -> None:
    ent.weapons = []
    if ent.weapons_to_load is None: return
    for wep in ent.weapons_to_load:
        wep_type = get_type(wep["name"])
        ent.weapons.append().append(wep_type.deserialize(wep))
        

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
