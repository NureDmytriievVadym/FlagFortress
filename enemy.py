import heapq, itertools, random
from models import *

class EnemyAction:
    def __init__(self, action: str, **kwargs):
        self.action: str = action
        self.move: Vector2 = None
        self.target: Entity = None
        if kwargs.get("move"): self.move = kwargs.get("move")
        if kwargs.get("target"): self.target = kwargs.get("target")

class Enemy(Entity):
    def __init__(self, pos: Vector2, symbol: str = "🤖"):
        Entity.__init__(self, pos, symbol)
        self.speed = 1
        self.speed_random_deviation = 0.25
        self.ai_disabled = False
        self.think_cooldown = 0

    @staticmethod
    def from_parent(obj: Entity) -> "Enemy":
        return Enemy(pos=obj.pos, symbol=obj.symbol)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data["speed"] = self.speed
        data["speed_random_deviation"] = self.speed_random_deviation
        data["ai_disabled"] = self.ai_disabled
        data["think_cooldown"] = self.think_cooldown
        return data

    @staticmethod
    def deserialize(data: dict) -> "Enemy":
        obj = Enemy.from_parent(Entity.deserialize(data))
        obj.speed = data["speed"]
        obj.speed_random_deviation = data["speed_random_deviation"]
        obj.ai_disabled = data["ai_disabled"]
        obj.think_cooldown = data["think_cooldown"]
        return obj

    def think(self, level: GameLevel, deltatime: float) -> EnemyAction:
        self.think_cooldown -= deltatime
        if(self.think_cooldown <= 0):
            self.think_cooldown = 1.0 / self.speed + (random.random() - 0.5) * 2 * self.speed_random_deviation
        return None

# Vibe coded. Don't have enough time to implement and debug an A* algorithm, unfortunately
_counter = itertools.count()

def is_walkable(pos: Vector2, objects: list[GameObject]) -> bool:
    for o in objects:
        if o.deleted:
            continue
        if o.pos == pos and (issubclass(type(o), Wall) or
                             issubclass(type(o), Hazard) or
                             issubclass(type(o), Enemy)):
            return False
    return True

def astar_next_move(start: Vector2, goal: Vector2, level: GameLevel):
    open_set = []
    heapq.heappush(open_set, (0, next(_counter), start))

    came_from = {}
    g_score = { (start.y, start.x): 0 }

    directions = [
        Vector2(-1, 0),
        Vector2(1, 0),
        Vector2(0, -1),
        Vector2(0, 1),
    ]

    while open_set:
        _, _, current = heapq.heappop(open_set)

        if current == goal:
            key = (current.y, current.x)
            prev = came_from.get(key)
            if prev is None:
                return None
            while prev != start:
                current = prev
                prev = came_from.get((current.y, current.x))
                if prev is None:
                    return None
            return current

        for d in directions:
            neighbor = current.add(d.y, d.x)

            if not is_walkable(neighbor, level.objects):
                continue

            key = (neighbor.y, neighbor.x)
            tentative_g = g_score[(current.y, current.x)] + 1

            if key not in g_score or tentative_g < g_score[key]:
                came_from[key] = current
                g_score[key] = tentative_g
                f = tentative_g + neighbor.manhattan_distance_to(goal)
                heapq.heappush(open_set, (f, next(_counter), neighbor))

    return None  # no path

def raytrace(start: Vector2, end: Vector2, objects: list[GameObject]) -> bool:
    x0, y0 = start.x, start.y
    x1, y1 = end.x, end.y

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx - dy

    x, y = x0, y0

    while True:
        pos = Vector2(y, x)

        for o in objects:
            if o.deleted: continue
            if o.pos == pos and issubclass(type(o), Solid): return False

        if x == x1 and y == y1:
            return True

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


class Ghost(Enemy):
    def __init__(self, pos: Vector2, symbol: str = "👻"):
        Enemy.__init__(self, pos, symbol)
        self.health = 3
        self.strength = 1

    @staticmethod
    def from_parent(obj: Enemy) -> "Ghost":
        return Ghost(pos=obj.pos, symbol=obj.symbol)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data["strength"] = self.strength
        return data

    @staticmethod
    def deserialize(data: dict) -> "Ghost":
        obj = Ghost.from_parent(Enemy.deserialize(data))
        obj.strength = data["strength"]
        return obj

    def think(self, level: GameLevel, deltatime: float) -> EnemyAction:
        self.think_cooldown -= deltatime

        if(self.think_cooldown > 0): return None
        
        self.think_cooldown = 1.0 / self.speed + (random.random() - 0.5) * 2 * self.speed_random_deviation

        if(self.pos.manhattan_distance_to(level.player.pos) <= 1):
            self.think_cooldown = 2
            return EnemyAction("TackleEntity", target=level.player)

        self.look_at(level.player.pos)
        move = astar_next_move(self.pos, level.player.pos, level)
        if not move is None: return EnemyAction("Move", move=Vector2(move.y - self.pos.y, move.x - self.pos.x))
        
        return None

class Sentry(Enemy):
    def __init__(self, pos: Vector2, symbol: str = "🔭"):
        Enemy.__init__(self, pos, symbol)
        self.health = 10

    @staticmethod
    def from_parent(obj: Enemy) -> "Ghost":
        return Ghost(pos=obj.pos, symbol=obj.symbol)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data["strength"] = self.strength
        return data

    @staticmethod
    def deserialize(data: dict) -> "Ghost":
        obj = Ghost.from_parent(Enemy.deserialize(data))
        obj.strength = data["strength"]
        return obj

    def think(self, level: GameLevel, deltatime: float) -> EnemyAction:
        self.think_cooldown -= deltatime
        if(self.think_cooldown > 0): return None
        self.think_cooldown = 1.0 / self.speed + (random.random() - 0.5) * 2 * self.speed_random_deviation

        if(self.get_selected_weapon() == None): return None
        if(raytrace(self.pos, level.player.pos, level.objects)):
            self.look_at(level.player.pos)
            return EnemyAction("Shoot")

        return None

class Mercenary(Enemy):
    def __init__(self, pos: Vector2, symbol: str = "🥷"):
        Enemy.__init__(self, pos, symbol)
        self.health = 6
        self.armor = 4
        self.speed = 2
        self.strength = 1

    @staticmethod
    def from_parent(obj: Enemy) -> "Mercenary":
        return Mercenary(pos=obj.pos, symbol=obj.symbol)
    
    def serialize(self) -> dict:
        data = super().serialize()
        data["strength"] = self.strength
        return data

    @staticmethod
    def deserialize(data: dict) -> "Ghost":
        obj = Ghost.from_parent(Enemy.deserialize(data))
        obj.strength = data["strength"]
        return obj

    def think(self, level: GameLevel, deltatime: float) -> EnemyAction:
        self.think_cooldown -= deltatime

        if(self.think_cooldown > 0): return None
        
        self.think_cooldown = 1.0 / self.speed + (random.random() - 0.5) * 2 * self.speed_random_deviation

        if(self.pos.manhattan_distance_to(level.player.pos) <= 1):
            self.think_cooldown /= 2
            return EnemyAction("TackleEntity", target=level.player)
        
        self.look_at(level.player.pos)
        if random.random() < 0.5 or not raytrace(self.pos, level.player.pos, level.objects):
            move = astar_next_move(self.pos, level.player.pos, level)
            if not move is None: return EnemyAction("Move", move=Vector2(move.y - self.pos.y, move.x - self.pos.x))
        else:
            if(self.get_selected_weapon().ammo == 0):
                self.think_cooldown += 1
                return EnemyAction("Reload")
            else: return EnemyAction("Shoot")
        
        return None