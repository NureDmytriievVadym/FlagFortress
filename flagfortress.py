"""
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import time
import queue
from collections.abc import Callable

TICKRATE = 100
TIME_PER_TICK = 1 / TICKRATE

_quit = False
stdscr = None

event_queue = queue.SimpleQueue()

class GameObject:
    def __init__(self, x: int, y: int, type: str, symbol: str):
        self.x = x
        self.y = y
        self.type = type
        self.symbol = symbol

class Event:
    def __init__(self, name: str, callback: Callable[[list],None], delay_seconds: float):
        self.name = name
        self.callback = callback
        # delay is in ticks
        self.delay = (delay_seconds * TICKRATE).__ceil__()
        self.initial_delay = self.delay
    
class InputEvent(Event):
    def __init__(self, name: str, callback: Callable[[list],None], key: int):
        Event.__init__(self, name, callback, 0)
        self.key = key

def handle_input():
    global stdscr
    c = stdscr.getch()
    if(c == -1):
        return
    
    event_queue.put(InputEvent("KeyPressed", lambda a: print(a), c))

def tick():
    global event_queue

    repeat_events = []
    while(not event_queue.empty()):
        e: Event = event_queue.get()
        if(e.delay > 0):
            repeat_events.append(e)
            e.delay -= 1
            continue
        
        if(type(e) is InputEvent):
            e.callback([e.key])
        else:
            e.callback([None])
    
    for e in repeat_events:
        event_queue.put(e)

def render():
    pass

def main(stdscr_in):
    global stdscr
    global _quit
    stdscr = stdscr_in
    stdscr.clear()
    stdscr.nodelay(True)

    lasttime = time.time_ns() / (10 ** 9)
    accumulator = 0
    while True:
        newtime = time.time_ns() / (10 ** 9)
        deltatime = newtime - lasttime
        accumulator += deltatime
        lasttime = newtime
        handle_input()

        if(accumulator >= TIME_PER_TICK * 10):
            accumulator = TIME_PER_TICK
        while (accumulator >= TIME_PER_TICK):
            tick()
            accumulator -= TIME_PER_TICK
        
        render()

        if _quit:
            break

curses.wrapper(main)