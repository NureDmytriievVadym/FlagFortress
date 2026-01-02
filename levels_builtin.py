from models import *

BUILTIN_LEVELS = [
    GameLevel(
        num = 1,
        name = "Flag",
        starting_ammo = 3,
        objects = [
            Spawn(Vector2(5, 5)),
            Flag(Vector2(5, 14)),
            Label(Vector2(2, 2), "Use the arrow keys to move around\nGet the flag and bring it back to spawn to win")
        ]
    ),
    GameLevel(
        num = 2,
        name = "Walls",
        starting_ammo = 2,
        objects = [
            Spawn(Vector2(5, 5)),
            Flag(Vector2(5, 14)),
            Wall(Vector2(2, 10)),
            Wall(Vector2(3, 10)),
            Wall(Vector2(4, 10)),
            Wall(Vector2(5, 10)),
            Wall(Vector2(6, 10)),
            Wall(Vector2(7, 10)),
            Wall(Vector2(8, 10)),
        ]
    ),
    GameLevel(
        num = 3,
        name = "Breakable walls",
        starting_ammo = 3,
        objects = [
            Spawn(Vector2(5, 5)),
            Flag(Vector2(5, 14)),
            Wall(Vector2(3, 12)),
            Wall(Vector2(3, 13)),
            Wall(Vector2(3, 14)),
            Wall(Vector2(3, 15)),
            Wall(Vector2(3, 16)),
            Wall(Vector2(7, 12)),
            Wall(Vector2(7, 13)),
            Wall(Vector2(7, 14)),
            Wall(Vector2(7, 15)),
            Wall(Vector2(7, 16)),
            Wall(Vector2(4, 16)),
            Wall(Vector2(5, 16)),
            Wall(Vector2(6, 16)),
            Wall(Vector2(4, 12), symbol = '◾', breakable = True),
            Wall(Vector2(5, 12), symbol = '◾', breakable = True),
            Wall(Vector2(6, 12), symbol = '◾', breakable = True),
        ]
    )
]
BUILTIN_LEVELS_COUNT = len(BUILTIN_LEVELS)