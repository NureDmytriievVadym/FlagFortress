from models import *
from enemy import *

BUILTIN_LEVELS = [
    GameLevel(
        name = "Flag",
        objects = [
            Spawn(Vector2(5, 5)),
            Flag(Vector2(5, 14)),
            Label(Vector2(2, 2), text="Use the arrow keys to move around\nGet the flag and bring it back to spawn to win")
        ]
    ),
    GameLevel(
        name = "Walls",
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
        name = "Breakable walls",
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
    ),
    GameLevel(
        name = "A Ghost!",
        objects = [
            Spawn(Vector2(5, 5)),
            Flag(Vector2(5, 18)),
            Ghost(Vector2(5, 14)),
            Wall(Vector2(3, 12)),
            Wall(Vector2(3, 13)),
            Wall(Vector2(3, 14)),
            Wall(Vector2(3, 15)),
            Wall(Vector2(3, 16)),
            Wall(Vector2(3, 17)),
            Wall(Vector2(3, 18)),
            Wall(Vector2(3, 19)),
            Wall(Vector2(3, 20)),
            Wall(Vector2(7, 12)),
            Wall(Vector2(7, 13)),
            Wall(Vector2(7, 14)),
            Wall(Vector2(7, 15)),
            Wall(Vector2(7, 16)),
            Wall(Vector2(7, 17)),
            Wall(Vector2(7, 18)),
            Wall(Vector2(7, 19)),
            Wall(Vector2(7, 20)),
            Wall(Vector2(4, 20)),
            Wall(Vector2(5, 20)),
            Wall(Vector2(6, 20)),
            Wall(Vector2(4, 12), symbol = '◾', breakable = True),
            Wall(Vector2(5, 12), symbol = '◾', breakable = True),
            Wall(Vector2(6, 12), symbol = '◾', breakable = True),
            Wall(Vector2(4, 16), symbol = '◾', breakable = True),
            Wall(Vector2(5, 16), symbol = '◾', breakable = True),
            Wall(Vector2(6, 16), symbol = '◾', breakable = True),
        ]
    )
]
BUILTIN_LEVELS_COUNT = len(BUILTIN_LEVELS)