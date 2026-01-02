"""
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import time
import queue
from collections.abc import Callable
import config

_quit: bool = False
gamestate: int = 0 # 0 = main menu, 1 = ingame, 2 = paused, 3 = over
stdscr = None

ammo_left = 4
level = {}
last_move = (1, 0)
event_queue = queue.SimpleQueue()

class GameObject:
    def __init__(self, x: int, y: int, type: str, symbol: str, hidden: bool = False):
        self.x = x
        self.y = y
        self.type = type
        self.symbol = symbol
        self.hidden = hidden

class Event:
    def __init__(self, name: str, delay_seconds: float = 0, params = None):
        self.name = name
        self.params = params
        # delay is in ticks
        self.delay = (delay_seconds * config.TICKRATE).__ceil__()
        self.initial_delay = self.delay

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
        event_queue.put(Event("PlayerAttemptMove", 0, (-1, 0)))
        last_move = (-1, 0)
    if(c == "KEY_RIGHT"):
        event_queue.put(Event("PlayerAttemptMove", 0, (1, 0)))
        last_move = (1, 0)
    if(c == "KEY_UP"):
        event_queue.put(Event("PlayerAttemptMove", 0, (0, -1)))
        last_move = (0, -1)
    if(c == "KEY_DOWN"):
        event_queue.put(Event("PlayerAttemptMove", 0, (0, 1)))
        last_move = (0, 1)
    if(c.lower() == "c"):
        move = list(last_move)
        move[0] *= 3
        move[1] *= 3
        event_queue.put(Event("PlayerAttemptMove", 0, move))
    if(c.lower() == "f"):
        event_queue.put(Event("Shoot", 0))

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

    for i in range(config.LEVEL_WIDTH*2+2):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y-1, config.LEVEL_SCREEN_OFFSET_X-1+i, '#')
    
    for i in range(config.LEVEL_WIDTH*2+2):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 1, config.LEVEL_SCREEN_OFFSET_X-1+i, '#')
    
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X-1, '#')
    
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X + config.LEVEL_WIDTH * 2 + 1, '#')

LEVELS = [
    {
        "Level": 1,
        "Spawn": GameObject(3, 3, "Spawn", '⭕'),
        "Flag": GameObject(3, 10, "Flag", '🚩'),
        "Objects": []
    }
]

def load_level(i):
    global level
    global _quit
    if(len(LEVELS) == i):
        _quit = True
        return
    
    level = LEVELS[i]
    level["Player"] = GameObject(level["Spawn"].x, level["Spawn"].y, "Player", "🐛")
    level["Objects"].append(level["Spawn"])
    level["Objects"].append(level["Flag"])
    level["Objects"].append(level["Player"])
    event_queue.put(Event("InitializeLevel"))

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
            for i in range(config.LEVEL_HEIGHT):
                stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X, " " * config.LEVEL_WIDTH * 2)

            stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + level["Player"].y, config.LEVEL_SCREEN_OFFSET_X + level["Player"].x * 2, level["Player"].symbol)
            stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + level["Flag"].y, config.LEVEL_SCREEN_OFFSET_X + level["Flag"].x * 2, level["Flag"].symbol)
        
        if(e.name == "Shoot"):
            ammo_left -= 1
            stdscr.addstr(5, 3, f"Ammo left: {ammo_left}")
        
        if(e.name == "ObtainedFlag"):
            level["Flag"].hidden = True
            stdscr.addstr(8, 3, "Bring the flag back to spawn!")
        
        if(e.name == "FlagCaptured"):
            ammo_left = 4
            load_level(level["Level"])

        if(e.name == "PlayerAttemptMove"):
            stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + level["Player"].y, config.LEVEL_SCREEN_OFFSET_X + level["Player"].x * 2, " ")
            for obj in level["Objects"]:
                if(obj.x == level["Player"].x and obj.y == level["Player"].y and obj != level["Player"] and not obj.hidden):
                    stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + level["Player"].y, config.LEVEL_SCREEN_OFFSET_X + level["Player"].x * 2, obj.symbol)

            level["Player"].x += e.params[0]
            level["Player"].y += e.params[1]
            stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + level["Player"].y, config.LEVEL_SCREEN_OFFSET_X + level["Player"].x * 2, level["Player"].symbol)

            for obj in level["Objects"]:
                if(obj.x == level["Player"].x and obj.y == level["Player"].y and obj != level["Player"]):
                    if(obj.type == "Spawn" and level["Flag"].hidden):
                        event_queue.put(Event("FlagCaptured"))

                    if(obj.type == "Flag"):
                        event_queue.put(Event("ObtainedFlag"))
    
    for e in repeat_events:
        event_queue.put(e)

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

        if _quit:
            break
    
    return 0

retcode = curses.wrapper(main)
if retcode == 0:
    print("You won!")
if retcode == 1:
    print("The console window isn't big enough for the game! Please run the game in a bigger terminal window.")