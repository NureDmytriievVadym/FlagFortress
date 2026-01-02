"""
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import time
import math
import queue
import config
from models import Vector2, GameObject, Event, GameLevel

_quit: bool = False
gamestate: int = 1 # 0 = main menu, 1 = ingame, 2 = paused, 3 = over
stdscr = None

ammo_left = 0
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
        fire_event("PlayerAttemptMove", params = Vector2(0, -1))
        last_move = Vector2(0, -1)
    if(c == "KEY_RIGHT"):
        fire_event("PlayerAttemptMove", params = Vector2(0, 1))
        last_move = Vector2(0, 1)
    if(c == "KEY_UP"):
        fire_event("PlayerAttemptMove", params = Vector2(-1, 0))
        last_move = Vector2(-1, 0)
    if(c == "KEY_DOWN"):
        fire_event("PlayerAttemptMove", params = Vector2(1, 0))
        last_move = Vector2(1, 0)
    if(c.lower() == "c"):
        fire_event("PlayerAttemptMove", params = last_move.mul(3))
    if(c.lower() == "f"):
        fire_event("Shoot")

LEVELS = [
    GameLevel(
        num = 1,
        name = "Flag",
        starting_ammo = 0,
        objects = [
            GameObject(Vector2(5, 5), "Spawn", '⭕'),
            GameObject(Vector2(5, 14), "Flag", '🚩'),
        ]
    ),
    GameLevel(
        num = 2,
        name = "Walls",
        starting_ammo = 0,
        objects = [
            GameObject(Vector2(5, 5), "Spawn", '⭕'),
            GameObject(Vector2(5, 14), "Flag", '🚩'),
            GameObject(Vector2(2, 10), "Wall", '⬛'),
            GameObject(Vector2(3, 10), "Wall", '⬛'),
            GameObject(Vector2(4, 10), "Wall", '⬛'),
            GameObject(Vector2(5, 10), "Wall", '⬛'),
            GameObject(Vector2(6, 10), "Wall", '⬛'),
            GameObject(Vector2(7, 10), "Wall", '⬛'),
            GameObject(Vector2(8, 10), "Wall", '⬛'),
        ]
    )
]

def load_level(i):
    global level
    global ammo_left
    global _quit
    if(len(LEVELS) == i):
        _quit = True
        return
    
    level = LEVELS[i]
    level.player = GameObject(level.spawn.pos.copy(), "Player", "🐛")
    level.objects.append(level.player)
    ammo_left = level.starting_ammo
    fire_event("InitializeLevel")

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

    stdscr.addstr(2, 3, "Arrow Keys - Move")
    stdscr.addstr(3, 3, "C - Dash")
    stdscr.addstr(4, 3, "F - Shoot")
    stdscr.addstr(5, 3, f"Ammo left: {ammo_left}")
    stdscr.addstr(7, 3, f"Level: {level.name} (#{level.num})")
    stdscr.addstr(8, 3, "Get the flag!")

    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y-1, config.LEVEL_SCREEN_OFFSET_X-1, '#' * (config.LEVEL_WIDTH * 2 + 4))
    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 1, config.LEVEL_SCREEN_OFFSET_X-1, '#' * (config.LEVEL_WIDTH * 2 + 4))
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X-1, '#')
    
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X + config.LEVEL_WIDTH * 2 + 2, '#')

def render():
    global stdscr
    for i in range(config.LEVEL_HEIGHT + 1):
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X, " " * (config.LEVEL_WIDTH * 2 + 1))
    
    for obj in level.objects:
        if(obj.hidden): continue
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + obj.pos.y, config.LEVEL_SCREEN_OFFSET_X + obj.pos.x * 2, obj.symbol)

def on_collide(a: GameObject, b: GameObject):
    if(a.type == "Player" and b.type == "Flag"):
        fire_event("ObtainedFlag")

    if(a.type == "Player" and b.type == "Spawn" and level.flag.hidden):
        fire_event("FlagCaptured")

    return a.type == "Player" and (b.type == "Wall" or b.type == "BreakableWall")

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
        
        if(e.name == "InitializeLevel"):
            stdscr.clear()
            initial_render()

        if(e.name == "Shoot"):
            if(ammo_left <= 0): continue

            ammo_left -= 1
            stdscr.addstr(5, 3, f"Ammo left: {ammo_left}")
        
        if(e.name == "ObtainedFlag"):
            level.flag.hidden = True
            stdscr.addstr(8, 3, "Bring the flag back to spawn!")
        
        if(e.name == "FlagCaptured"):
            ammo_left = 4
            load_level(level.num)

        if(e.name == "PlayerAttemptMove"):
            plr_move_x = 0
            plr_move_y = 0

            for i in range(round(math.copysign(1, e.params.x)), e.params.x + round(math.copysign(1, e.params.x)), round(math.copysign(1, e.params.x))):
                if(level.player.pos.x + i > config.LEVEL_WIDTH or level.player.pos.x + i < 0): break
                collided = False
                for obj in level.objects:
                    if(level.player.pos.add(0, i) == obj.pos):
                        if(on_collide(level.player, obj)):
                            collided = True
                            break
                if collided: break

                plr_move_x = i
            
            for i in range(round(math.copysign(1, e.params.y)), e.params.y + round(math.copysign(1, e.params.y)), round(math.copysign(1, e.params.y))):
                if(level.player.pos.y + i > config.LEVEL_HEIGHT or level.player.pos.y + i < 0): break
                collided = False
                for obj in level.objects:
                    if(level.player.pos.add(i, 0) == obj.pos):
                        if(on_collide(level.player, obj)):
                            collided = True
                            break
                if collided: break

                plr_move_y = i

            level.player.pos = level.player.pos.add(plr_move_y, plr_move_x)
    
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
        render()
        if _quit:
            break
    
    return 0

retcode = curses.wrapper(main)
if retcode == 0:
    print("You won!")
if retcode == 1:
    print("The console window isn't big enough for the game! Please run the game in a bigger terminal window.")