"""
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import time
import queue
from collections.abc import Callable
import config
from models import Vector2, GameObject, Event

_quit: bool = False
gamestate: int = 1 # 0 = main menu, 1 = ingame, 2 = paused, 3 = over
stdscr = None

ammo_left = config.AMMO_PER_LEVEL
level = {}
last_move = Vector2(0, 0)
event_queue = queue.SimpleQueue()

def fire_event(e: Event):
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
        fire_event(Event("PlayerAttemptMove", 0, Vector2(0, -1)))
        last_move = Vector2(0, -1)
    if(c == "KEY_RIGHT"):
        fire_event(Event("PlayerAttemptMove", 0, Vector2(0, 1)))
        last_move = Vector2(0, 1)
    if(c == "KEY_UP"):
        fire_event(Event("PlayerAttemptMove", 0, Vector2(-1, 0)))
        last_move = Vector2(-1, 0)
    if(c == "KEY_DOWN"):
        fire_event(Event("PlayerAttemptMove", 0, Vector2(1, 0)))
        last_move = Vector2(1, 0)
    if(c.lower() == "c"):
        fire_event(Event("PlayerAttemptMove", 0, last_move.mul(3)))
    if(c.lower() == "f"):
        fire_event(Event("Shoot"))

LEVELS = [
    {
        "Level": 1,
        "Ammo": 0,
        "Spawn": GameObject(Vector2(3, 3), "Spawn", '⭕'),
        "Flag": GameObject(Vector2(3, 10), "Flag", '🚩'),
        "Objects": []
    },
    {
        "Level": 2,
        "Ammo": config.AMMO_PER_LEVEL,
        "Spawn": GameObject(Vector2(3, 3), "Spawn", '⭕'),
        "Flag": GameObject(Vector2(3, 10), "Flag", '🚩'),
        "Objects": []
    }
]

def load_level(i):
    global level
    global ammo_left
    global _quit
    if(len(LEVELS) == i):
        _quit = True
        return
    
    level = LEVELS[i]
    level["Player"] = GameObject(level["Spawn"].pos.copy(), "Player", "🐛")
    level["Objects"].append(level["Spawn"])
    level["Objects"].append(level["Flag"])
    level["Objects"].append(level["Player"])
    ammo_left = LEVELS[i]["Ammo"]
    fire_event(Event("InitializeLevel"))

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
    stdscr.addstr(7, 3, "Level: 1")
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
    
    for obj in level["Objects"]:
        if(obj.hidden): continue
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + obj.pos.y, config.LEVEL_SCREEN_OFFSET_X + obj.pos.x * 2, obj.symbol)

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
            level["Flag"].hidden = True
            stdscr.addstr(8, 3, "Bring the flag back to spawn!")
        
        if(e.name == "FlagCaptured"):
            ammo_left = 4
            load_level(level["Level"])

        if(e.name == "PlayerAttemptMove"):
            if(level["Player"].pos.x + e.params.x > config.LEVEL_WIDTH or level["Player"].pos.x + e.params.x < 0): e.params.x = 0
            if(level["Player"].pos.y + e.params.y > config.LEVEL_HEIGHT or level["Player"].pos.y + e.params.y < 0): e.params.y = 0

            level["Player"].pos = level["Player"].pos.add(e.params.y, e.params.x)

            for obj in level["Objects"]:
                if(obj.pos.x == level["Player"].pos.x and obj.pos.y == level["Player"].pos.y and obj != level["Player"]):
                    if(obj.type == "Spawn" and level["Flag"].hidden):
                        fire_event(Event("FlagCaptured"))

                    if(obj.type == "Flag"):
                        fire_event(Event("ObtainedFlag"))
    
    for e in repeat_events: fire_event(e)

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