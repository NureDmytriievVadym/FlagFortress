"""
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import time
import queue
import config
from models import sign, Vector2, GameObject, Player, Wall, Spawn, Flag, PlayerBullet, Event, GameLevel

_quit: bool = False
gamestate: int = 1 # 0 = main menu, 1 = ingame, 2 = paused, 3 = over
stdscr = None

level = {}
last_move = Vector2(0, 0)
event_queue = queue.SimpleQueue()

def fire_event(name: str, delay: float = 0, params: any = []):
    event_queue.put(Event(name, delay, params))

def refire_event(e: Event):
    event_queue.put(e)

def handle_input():
    global stdscr
    global last_move
    c = ""
    try:
        c = stdscr.getkey()
    except:
        time.sleep(0.01)
        pass
        
    if(c == -1 or c == ""):
        return
    
    if(c == "KEY_LEFT"):
        fire_event("PlayerMove", params = Vector2(0, -1))
        last_move = Vector2(0, -1)
    if(c == "KEY_RIGHT"):
        fire_event("PlayerMove", params = Vector2(0, 1))
        last_move = Vector2(0, 1)
    if(c == "KEY_UP"):
        fire_event("PlayerMove", params = Vector2(-1, 0))
        last_move = Vector2(-1, 0)
    if(c == "KEY_DOWN"):
        fire_event("PlayerMove", params = Vector2(1, 0))
        last_move = Vector2(1, 0)
    if(c.lower() == "c"):
        fire_event("PlayerDash", params = last_move.mul(3))
    if(c.lower() == "f"):
        fire_event("Shoot")

LEVELS = [
    GameLevel(
        num = 1,
        name = "Flag",
        starting_ammo = 3,
        objects = [
            Spawn(Vector2(5, 5)),
            Flag(Vector2(5, 14)),
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

def load_level(i):
    global level
    global _quit
    if(len(LEVELS) == i):
        _quit = True
        return
    
    level = LEVELS[i]
    level.player = Player(level.spawn.pos.copy())
    level.add_object(level.player)
    level.player.ammo_left = level.starting_ammo
    fire_event("InitializeLevel")

def render_hud():
    stdscr.addstr(2, 3, "Q - Quit")
    stdscr.addstr(3, 3, "Arrow Keys - Move")
    stdscr.addstr(4, 3, "C - Dash")
    stdscr.addstr(5, 3, "F - Shoot")
    stdscr.addstr(6, 3, f"Ammo left: {0 if level.player is None else level.player.ammo_left}")
    stdscr.addstr(8, 3, f"Level: {level.name} (#{level.num})")
    stdscr.addstr(9, 3, "Get the flag and bring it back to spawn")

def render_debug():
    for i in range(stdscr.getmaxyx()[0] - (config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3)):
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 3, " " * 30)

    for i in range(len(level.objects)):
        obj = level.objects[i]
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 3, obj.type + str(obj.pos))

def initial_render():
    global stdscr
    screen_height, screen_width = stdscr.getmaxyx()
    for i in range(0, screen_width-1):
        stdscr.addch(0, i, '.')
    
    for i in range(0, screen_height-1):
        stdscr.addch(i, 0, '.')

    for i in range(0, screen_width-1):
        stdscr.addch(screen_height-1, i, '.')
    
    for i in range(0, screen_height-1):
        stdscr.addch(i, screen_width-1, '.')

    render_hud()

    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y-1, config.LEVEL_SCREEN_OFFSET_X-1, '#' * (config.LEVEL_WIDTH * 2 + 4))
    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 1, config.LEVEL_SCREEN_OFFSET_X-1, '#' * (config.LEVEL_WIDTH * 2 + 4))
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X-1, '#')
    
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X + config.LEVEL_WIDTH * 2 + 2, '#')

def render_seperate():
    global stdscr

    for i in range(config.LEVEL_HEIGHT + 1):
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X, "!" * (config.LEVEL_WIDTH * 2 + 2))
    
    for obj in level.objects:
        if(obj.hidden): continue
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + obj.pos.y, config.LEVEL_SCREEN_OFFSET_X + obj.pos.x * 2, obj.symbol)
    
    if(not level.player is None):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + level.player.pos.y, config.LEVEL_SCREEN_OFFSET_X + level.player.pos.x * 2, level.player.symbol)

def render_matrix():
    global stdscr

    render_matrix = []
    for i in range(config.LEVEL_HEIGHT+1):
        row = []
        for i in range(config.LEVEL_WIDTH*2+2): row.append(' ')
        render_matrix.append(row)
    
    for obj in level.objects:
        if(obj.hidden): continue
        if((not 0 <= obj.pos.y <= config.LEVEL_HEIGHT) or (not 0 <= obj.pos.x <= config.LEVEL_WIDTH)): continue
        render_matrix[obj.pos.y][obj.pos.x*2] = obj.symbol
        if(ord(obj.symbol) > 255): render_matrix[obj.pos.y][obj.pos.x*2+1] = ''
    
    for i in range(len(render_matrix)):
        row = render_matrix[i]
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X, ''.join(row))

def on_collide(a: GameObject, b: GameObject):
    if(a.type == "Player" and b.type == "Flag"):
        fire_event("ObtainedFlag")

    elif(a.type == "Player" and b.type == "Spawn" and level.flag.hidden):
        fire_event("FlagCaptured")

    elif(a.type == "Player" and b.type == "Hazard" and not a.invulnerable):
        fire_event("PlayerHurt", 0, 1)
    
    elif(a.type == "PlayerBullet" and b.type == "Wall"):
        if(a.pierce != -1):
            a.pierce -= 1
            if(a.pierce < 0):
                level.delete_object(a)
        
        if(b.breakable): level.delete_object(b)

    if(a == None or b == None): return False
    return a.type == "Player" and b.type == "Wall"

def move_object(a: GameObject, move: Vector2):
    move_x = 0
    move_y = 0

    if move.x != 0:
        for i in range(sign(move.x), move.x + sign(move.x), sign(move.x)):
            if(a.pos.x + i > config.LEVEL_WIDTH or a.pos.x + i < 0):
                if(a.type == "Player"): break
                else:
                    level.delete_object(a)
                    return
            collided = False
            for b in level.objects:
                if(a.pos.add(0, i) == b.pos and a != b):
                    if(on_collide(a, b)):
                        collided = True
                        break
            
            if collided: break
            move_x = i           
    
    if move.y != 0:
        for i in range(sign(move.y), move.y + sign(move.y), sign(move.y)):
            if(a.pos.y + i > config.LEVEL_HEIGHT or a.pos.y + i < 0):
                if(a.type == "Player"): break
                else:
                    level.delete_object(a)
                    return
            collided = False
            for b in level.objects:
                if(a.pos.add(i, 0) == b.pos and a != b):
                    if(on_collide(a, b)):
                        collided = True
                        break
            if collided: break
            move_y = i

    a.pos = a.pos.add(move_y, move_x)

def tick():
    global stdscr
    global event_queue
    global ammo_left

    repeat_events = []
    while(not event_queue.empty()):
        e: Event = event_queue.get()
        if(e.delay > 0):
            repeat_events.append(e)
            e.delay -= 1
            continue
        
        elif(e.name == "InitializeLevel"):
            stdscr.clear()
            initial_render()

        elif(e.name == "Shoot"):
            if(level.player.ammo_left <= 0): continue

            level.player.ammo_left -= 1
            render_hud()

            bullet = PlayerBullet(level.player.pos.copy(), last_move.normal())
            level.add_object(bullet)
            fire_event("BulletMove", 0, bullet)
        
        elif(e.name == "BulletMove"):
            bullet = e.params
            if(bullet == None): continue
            move_object(bullet, bullet.direction)
            fire_event("BulletMove", 1 / bullet.speed, bullet)
        
        elif(e.name == "ObtainedFlag"):
            level.flag.hidden = True
        
        elif(e.name == "FlagCaptured"):
            ammo_left = 4
            load_level(level.num)

        elif(e.name == "PlayerDash"):
            if (not level.player.has_dash) or level.player.dash_speed == 0: return
            level.player.invulnerable = True
            fire_event("PlayerMove", params = last_move.mul(level.player.dash_speed))
            level.player.invulnerable = False

        elif(e.name == "PlayerMove"):
            move_object(level.player, e.params)
        
        elif(e.name == "PlayerHurt"):
            if(level.player.invulnerable): return
            level.player.health -= e.params
            # todo
    
    for e in repeat_events: refire_event(e)

def main(stdscr_in):
    global stdscr
    global _quit
    stdscr = stdscr_in
    stdscr.clear()
    stdscr.nodelay(True)
    screen_height, screen_width = stdscr.getmaxyx()

    if(screen_height < 30 or screen_width < 60):
        return 1

    lasttime = time.time_ns() / (10 ** 9)
    accumulator = 0

    load_level(0)
    initial_render()
    while True:
        newtime = time.time_ns() / (10 ** 9)
        deltatime = newtime - lasttime
        accumulator += deltatime
        lasttime = newtime
        handle_input()

        if(accumulator >= config.TIME_PER_TICK * 10):
            accumulator = config.TIME_PER_TICK
        while (accumulator >= config.TIME_PER_TICK):
            tick()
            accumulator -= config.TIME_PER_TICK
        render_matrix()
        if(config.DEBUG): render_debug()
        if _quit:
            break
    
    return 0

retcode = curses.wrapper(main)
if retcode == 0:
    print("You won!")
if retcode == 1:
    print("The console window isn't big enough for the game! Please run the game in a bigger terminal window.")