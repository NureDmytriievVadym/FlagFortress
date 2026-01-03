"""
# pip install pygame
# pip install playsound==1.2.2
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import os
import time
import queue
import math
import config
import pygame
from enum import Enum
from models import *
from enemy import *
from weapons import *
import level_sideloading

_sound_cache = {}
_quit: bool = False
_frametime: float = 1
_frametimes: list[float] = []
_deltatime: float = 1
_deltatimes: list[float] = []
_timescale: float = 1
_lifetime: float = 0
_registered_events = []
_screensize: Vector2 = Vector2(10, 10)
class Gamestate(Enum):
    MAIN_MENU = 0
    INGAME = 1
    INGAME_CUSTOM = 2
    INGAME_PAUSED = 3
    OPTIONS = 4
    WINSCREEN = 5
    LOSESCREEN = 6
_gamestate: Gamestate = Gamestate.MAIN_MENU
_previous_gamestate: Gamestate = Gamestate.MAIN_MENU
_options_saved_volume = config.VOLUME
stdscr = None

HUD_SIZE = Vector2(5, _screensize.x-1)
_hud_frame_symbol: str = '#'
_hud_frame_attr: int = 0

BUILTIN_LEVELS_SERIAL = bytearray(b"FF01LC\x00\x00\x00\x04\x00\x00\x06\x88//57ACIAbgBhAG0AZQAiADoAIAAiAEYAbABhAGcAIgAsACAAIgBhAHUAdABoAG8AcgAiADoAIAAiAFYAYQBkAHkAbQBEAG0AeQB0AHIAaQBpAGUAdgAiACwAIAAiAGQAZQBzAGMAcgBpAHAAdABpAG8AbgAiADoAIAAiAEIAdQBpAGwAdAAtAGkAbgAgAGwAZQB2AGUAbAAiACwAIAAiAHMAdABhAHIAdABpAG4AZwBfAHcAZQBhAHAAbwBuAF8AbgBhAG0AZQAiADoAIAAiAFAAaQBzAHQAbwBsACIALAAgACIAcwB0AGEAcgB0AGkAbgBnAF8AdwBlAGEAcABvAG4AXwBhAG0AbQBvACIAOgAgADQALAAgACIAcwB0AGEAcgB0AGkAbgBnAF8AdwBlAGEAcABvAG4AXwBhAG0AbQBvAF8AcgBlAHMAZQByAHYAZQAiADoAIAA0ACwAIAAiAHMAdABhAHIAdABpAG4AZwBfAGgAZQBhAGwAdABoACIAOgAgADQALAAgACIAcwB0AGEAcgB0AGkAbgBnAF8AYQByAG0AbwByACIAOgAgADAALAAgACIAbwBiAGoAZQBjAHQAcwAiADoAIABbAHsAIgB0AHkAcABlACIAOgAgACIAUwBwAGEAdwBuACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANQAsACAAIgB4ACIAOgAgADUAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQBkADgAMwBkAFwAdQBkAGQAMAA1ACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIARgBsAGEAZwAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADUALAAgACIAeAAiADoAIAAxADQAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQBkADgAMwBkAFwAdQBkAGUAYQA5ACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIATABhAGIAZQBsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAMgAsACAAIgB4ACIAOgAgADIAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAEwAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgAC0AMQAsACAAIgB0AGUAeAB0ACIAOgAgACIAVQBzAGUAIAB0AGgAZQAgAGEAcgByAG8AdwAgAGsAZQB5AHMAIAB0AG8AIABtAG8AdgBlACAAYQByAG8AdQBuAGQAXABuAEcAZQB0ACAAdABoAGUAIABmAGwAYQBnACAAYQBuAGQAIABiAHIAaQBuAGcAIABpAHQAIABiAGEAYwBrACAAdABvACAAcwBwAGEAdwBuACAAdABvACAAdwBpAG4AIgAsACAAIgB0AGUAeAB0AF8AYQB0AHQAcgAiADoAIAAwAH0AXQB9AA==\x00\x00\x00\x0c\xb8//57ACIAbgBhAG0AZQAiADoAIAAiAFcAYQBsAGwAcwAiACwAIAAiAGEAdQB0AGgAbwByACIAOgAgACIAVgBhAGQAeQBtAEQAbQB5AHQAcgBpAGkAZQB2ACIALAAgACIAZABlAHMAYwByAGkAcAB0AGkAbwBuACIAOgAgACIAQgB1AGkAbAB0AC0AaQBuACAAbABlAHYAZQBsACIALAAgACIAcwB0AGEAcgB0AGkAbgBnAF8AdwBlAGEAcABvAG4AXwBuAGEAbQBlACIAOgAgACIAUABpAHMAdABvAGwAIgAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwB3AGUAYQBwAG8AbgBfAGEAbQBtAG8AIgA6ACAANAAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwB3AGUAYQBwAG8AbgBfAGEAbQBtAG8AXwByAGUAcwBlAHIAdgBlACIAOgAgADQALAAgACIAcwB0AGEAcgB0AGkAbgBnAF8AaABlAGEAbAB0AGgAIgA6ACAANAAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwBhAHIAbQBvAHIAIgA6ACAAMAAsACAAIgBvAGIAagBlAGMAdABzACIAOgAgAFsAewAiAHQAeQBwAGUAIgA6ACAAIgBTAHAAYQB3AG4AIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA1ACwAIAAiAHgAIgA6ACAANQB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1AGQAOAAzAGQAXAB1AGQAZAAwADUAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBGAGwAYQBnACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANQAsACAAIgB4ACIAOgAgADEANAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1AGQAOAAzAGQAXAB1AGQAZQBhADkAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAMgAsACAAIgB4ACIAOgAgADEAMAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADMALAAgACIAeAAiADoAIAAxADAAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA0ACwAIAAiAHgAIgA6ACAAMQAwAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANQAsACAAIgB4ACIAOgAgADEAMAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADYALAAgACIAeAAiADoAIAAxADAAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA3ACwAIAAiAHgAIgA6ACAAMQAwAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAOAAsACAAIgB4ACIAOgAgADEAMAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0AXQB9AA==\x00\x00\x00\x17`//57ACIAbgBhAG0AZQAiADoAIAAiAEIAcgBlAGEAawBhAGIAbABlACAAdwBhAGwAbABzACIALAAgACIAYQB1AHQAaABvAHIAIgA6ACAAIgBWAGEAZAB5AG0ARABtAHkAdAByAGkAaQBlAHYAIgAsACAAIgBkAGUAcwBjAHIAaQBwAHQAaQBvAG4AIgA6ACAAIgBCAHUAaQBsAHQALQBpAG4AIABsAGUAdgBlAGwAIgAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwB3AGUAYQBwAG8AbgBfAG4AYQBtAGUAIgA6ACAAIgBQAGkAcwB0AG8AbAAiACwAIAAiAHMAdABhAHIAdABpAG4AZwBfAHcAZQBhAHAAbwBuAF8AYQBtAG0AbwAiADoAIAA0ACwAIAAiAHMAdABhAHIAdABpAG4AZwBfAHcAZQBhAHAAbwBuAF8AYQBtAG0AbwBfAHIAZQBzAGUAcgB2AGUAIgA6ACAANAAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwBoAGUAYQBsAHQAaAAiADoAIAA0ACwAIAAiAHMAdABhAHIAdABpAG4AZwBfAGEAcgBtAG8AcgAiADoAIAAwACwAIAAiAG8AYgBqAGUAYwB0AHMAIgA6ACAAWwB7ACIAdAB5AHAAZQAiADoAIAAiAFMAcABhAHcAbgAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADUALAAgACIAeAAiADoAIAA1AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAZAA4ADMAZABcAHUAZABkADAANQAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAEYAbABhAGcAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA1ACwAIAAiAHgAIgA6ACAAMQA0AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAZAA4ADMAZABcAHUAZABlAGEAOQAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAAzACwAIAAiAHgAIgA6ACAAMQAyAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAMwAsACAAIgB4ACIAOgAgADEAMwB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADMALAAgACIAeAAiADoAIAAxADQAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAAzACwAIAAiAHgAIgA6ACAAMQA1AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAMwAsACAAIgB4ACIAOgAgADEANgB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADcALAAgACIAeAAiADoAIAAxADIAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA3ACwAIAAiAHgAIgA6ACAAMQAzAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANwAsACAAIgB4ACIAOgAgADEANAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADcALAAgACIAeAAiADoAIAAxADUAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA3ACwAIAAiAHgAIgA6ACAAMQA2AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANAAsACAAIgB4ACIAOgAgADEANgB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADUALAAgACIAeAAiADoAIAAxADYAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA2ACwAIAAiAHgAIgA6ACAAMQA2AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANAAsACAAIgB4ACIAOgAgADEAMgB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIANQBmAGUAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAdAByAHUAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA1ACwAIAAiAHgAIgA6ACAAMQAyAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgA1AGYAZQAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIAB0AHIAdQBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADYALAAgACIAeAAiADoAIAAxADIAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyADUAZgBlACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAHQAcgB1AGUAfQBdAH0A\x00\x00\x00\'\x98//57ACIAbgBhAG0AZQAiADoAIAAiAEEAIABHAGgAbwBzAHQAIQAiACwAIAAiAGEAdQB0AGgAbwByACIAOgAgACIAVgBhAGQAeQBtAEQAbQB5AHQAcgBpAGkAZQB2ACIALAAgACIAZABlAHMAYwByAGkAcAB0AGkAbwBuACIAOgAgACIAQgB1AGkAbAB0AC0AaQBuACAAbABlAHYAZQBsACIALAAgACIAcwB0AGEAcgB0AGkAbgBnAF8AdwBlAGEAcABvAG4AXwBuAGEAbQBlACIAOgAgACIAUABpAHMAdABvAGwAIgAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwB3AGUAYQBwAG8AbgBfAGEAbQBtAG8AIgA6ACAANAAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwB3AGUAYQBwAG8AbgBfAGEAbQBtAG8AXwByAGUAcwBlAHIAdgBlACIAOgAgADQALAAgACIAcwB0AGEAcgB0AGkAbgBnAF8AaABlAGEAbAB0AGgAIgA6ACAANAAsACAAIgBzAHQAYQByAHQAaQBuAGcAXwBhAHIAbQBvAHIAIgA6ACAAMAAsACAAIgBvAGIAagBlAGMAdABzACIAOgAgAFsAewAiAHQAeQBwAGUAIgA6ACAAIgBTAHAAYQB3AG4AIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA1ACwAIAAiAHgAIgA6ACAANQB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1AGQAOAAzAGQAXAB1AGQAZAAwADUAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBGAGwAYQBnACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANQAsACAAIgB4ACIAOgAgADEAOAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1AGQAOAAzAGQAXAB1AGQAZQBhADkAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBHAGgAbwBzAHQAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA1ACwAIAAiAHgAIgA6ACAAMQA0AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAZAA4ADMAZABcAHUAZABjADcAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBoAGUAYQBsAHQAaAAiADoAIAAzACwAIAAiAGEAcgBtAG8AcgAiADoAIAAwACwAIAAiAGQAaQByAGUAYwB0AGkAbwBuACIAOgAgAHsAIgB5ACIAOgAgADAALAAgACIAeAAiADoAIAAxAH0ALAAgACIAaQBuAHYAdQBsAG4AZQByAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlACwAIAAiAHMAZQBsAGUAYwB0AGUAZABfAHcAZQBhAHAAbwBuAF8AaQBuAGQAZQB4ACIAOgAgADAALAAgACIAdwBlAGEAcABvAG4AcwAiADoAIABbAF0ALAAgACIAcwBwAGUAZQBkACIAOgAgADEALAAgACIAcwBwAGUAZQBkAF8AcgBhAG4AZABvAG0AXwBkAGUAdgBpAGEAdABpAG8AbgAiADoAIAAwAC4AMgA1ACwAIAAiAGEAaQBfAGQAaQBzAGEAYgBsAGUAZAAiADoAIABmAGEAbABzAGUALAAgACIAdABoAGkAbgBrAF8AYwBvAG8AbABkAG8AdwBuACIAOgAgADAALAAgACIAcwB0AHIAZQBuAGcAdABoACIAOgAgADEAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAMwAsACAAIgB4ACIAOgAgADEAMgB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADMALAAgACIAeAAiADoAIAAxADMAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAAzACwAIAAiAHgAIgA6ACAAMQA0AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAMwAsACAAIgB4ACIAOgAgADEANQB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADMALAAgACIAeAAiADoAIAAxADYAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAAzACwAIAAiAHgAIgA6ACAAMQA3AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAAMwAsACAAIgB4ACIAOgAgADEAOAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADMALAAgACIAeAAiADoAIAAxADkAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAAzACwAIAAiAHgAIgA6ACAAMgAwAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANwAsACAAIgB4ACIAOgAgADEAMgB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADcALAAgACIAeAAiADoAIAAxADMAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA3ACwAIAAiAHgAIgA6ACAAMQA0AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANwAsACAAIgB4ACIAOgAgADEANQB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADcALAAgACIAeAAiADoAIAAxADYAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA3ACwAIAAiAHgAIgA6ACAAMQA3AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANwAsACAAIgB4ACIAOgAgADEAOAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADcALAAgACIAeAAiADoAIAAxADkAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA3ACwAIAAiAHgAIgA6ACAAMgAwAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANAAsACAAIgB4ACIAOgAgADIAMAB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIAYgAxAGIAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAZgBhAGwAcwBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADUALAAgACIAeAAiADoAIAAyADAAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyAGIAMQBiACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAGYAYQBsAHMAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA2ACwAIAAiAHgAIgA6ACAAMgAwAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgBiADEAYgAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIABmAGEAbABzAGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANAAsACAAIgB4ACIAOgAgADEAMgB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIANQBmAGUAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAdAByAHUAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA1ACwAIAAiAHgAIgA6ACAAMQAyAH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgA1AGYAZQAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIAB0AHIAdQBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADYALAAgACIAeAAiADoAIAAxADIAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyADUAZgBlACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAHQAcgB1AGUAfQAsACAAewAiAHQAeQBwAGUAIgA6ACAAIgBXAGEAbABsACIALAAgACIAcABvAHMAIgA6ACAAewAiAHkAIgA6ACAANAAsACAAIgB4ACIAOgAgADEANgB9ACwAIAAiAHMAeQBtAGIAbwBsACIAOgAgACIAXAB1ADIANQBmAGUAIgAsACAAIgBoAGkAZABkAGUAbgAiADoAIABmAGEAbABzAGUALAAgACIAbwByAGQAZQByACIAOgAgADAALAAgACIAYgByAGUAYQBrAGEAYgBsAGUAIgA6ACAAdAByAHUAZQB9ACwAIAB7ACIAdAB5AHAAZQAiADoAIAAiAFcAYQBsAGwAIgAsACAAIgBwAG8AcwAiADoAIAB7ACIAeQAiADoAIAA1ACwAIAAiAHgAIgA6ACAAMQA2AH0ALAAgACIAcwB5AG0AYgBvAGwAIgA6ACAAIgBcAHUAMgA1AGYAZQAiACwAIAAiAGgAaQBkAGQAZQBuACIAOgAgAGYAYQBsAHMAZQAsACAAIgBvAHIAZABlAHIAIgA6ACAAMAAsACAAIgBiAHIAZQBhAGsAYQBiAGwAZQAiADoAIAB0AHIAdQBlAH0ALAAgAHsAIgB0AHkAcABlACIAOgAgACIAVwBhAGwAbAAiACwAIAAiAHAAbwBzACIAOgAgAHsAIgB5ACIAOgAgADYALAAgACIAeAAiADoAIAAxADYAfQAsACAAIgBzAHkAbQBiAG8AbAAiADoAIAAiAFwAdQAyADUAZgBlACIALAAgACIAaABpAGQAZABlAG4AIgA6ACAAZgBhAGwAcwBlACwAIAAiAG8AcgBkAGUAcgAiADoAIAAwACwAIAAiAGIAcgBlAGEAawBhAGIAbABlACIAOgAgAHQAcgB1AGUAfQBdAH0A\x00")
BUILTIN_LEVELS: list[GameLevel] = []

BIG_TEXT = {
    "YOU WIN": """
██╗   ██╗ ██████╗ ██╗   ██╗    ██╗    ██╗██╗███╗   ██╗
╚██╗ ██╔╝██╔═══██╗██║   ██║    ██║    ██║██║████╗  ██║
 ╚████╔╝ ██║   ██║██║   ██║    ██║ █╗ ██║██║██╔██╗ ██║
  ╚██╔╝  ██║   ██║██║   ██║    ██║███╗██║██║██║╚██╗██║
   ██║   ╚██████╔╝╚██████╔╝    ╚███╔███╔╝██║██║ ╚████║
   ╚═╝    ╚═════╝  ╚═════╝      ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝""",
   "YOU LOSE": """
██╗   ██╗ ██████╗ ██╗   ██╗    ██╗      ██████╗ ███████╗███████╗
╚██╗ ██╔╝██╔═══██╗██║   ██║    ██║     ██╔═══██╗██╔════╝██╔════╝
 ╚████╔╝ ██║   ██║██║   ██║    ██║     ██║   ██║███████╗█████╗  
  ╚██╔╝  ██║   ██║██║   ██║    ██║     ██║   ██║╚════██║██╔══╝  
   ██║   ╚██████╔╝╚██████╔╝    ███████╗╚██████╔╝███████║███████╗
   ╚═╝    ╚═════╝  ╚═════╝     ╚══════╝ ╚═════╝ ╚══════╝╚══════╝""",
   "FF": """
   ▄████████    ▄████████ 
  ███    ███   ███    ███ 
  ███    █▀    ███    █▀  
 ▄███▄▄▄      ▄███▄▄▄     
▀▀███▀▀▀     ▀▀███▀▀▀     
  ███          ███        
  ███          ███        
  ███          ███        """
}

MENUS = {
    "MainMenu": Menu(Vector2(20, 48), "FlagFortress", BIG_TEXT["FF"] + "\n\nCapture the Flag in your terminal!", [
        ["play_builtin", "Start Game"],
        ["play_custom", "Play Custom Levels"],
        ["open_options", "Options"],
        ["quit", "Quit"]
    ]),
    "Options": Menu(Vector2(16, 42), "Options", "Customize the game to your liking", [
        ["options_set_target_tickrate", f"Target Tickrate ({config.TARGET_TICKRATE})"],
        ["options_set_max_fps", f"Target FPS ({config.TARGET_FPS})"],
        ["options_set_volume", f"Volume ({config.VOLUME})"],
        ["options_set_show_fps", f"Display FPS ({config.DISPLAY_FPS})"],
        ["options_set_show_tps", f"Display TPS ({config.DISPLAY_TPS})"],
        ["options_set_debug", f"Debug Mode ({config.DEBUG})"],
        ["back", "Back"]
    ]),
    "Options_Target_Tickrate": Menu(Vector2(10, 36), "Target Tickrate", "Current value: ", [
        ["options_set_target_tickrate_500", "500"],
        ["options_set_target_tickrate_100", "100"],
        ["options_set_target_tickrate_30", "30"],
        ["options_set_target_tickrate_10", "10"],
        ["back", "Back"]
    ]),
    "Options_Max_FPS": Menu(Vector2(14, 36), "Max FPS", "Current value: ", [
        ["options_set_max_fps_1000", "1000"],
        ["options_set_max_fps_250", "250"],
        ["options_set_max_fps_144", "144"],
        ["options_set_max_fps_100", "100"],
        ["options_set_max_fps_60", "60"],
        ["options_set_max_fps_30", "30"],
        ["options_set_max_fps_10", "10"],
        ["back", "Back"]
    ]),
    "Options_Volume": Menu(Vector2(16, 36), "Volume", "Current value: ", [
        ["options_set_volume_100", "100"],
        ["options_set_volume_90", "90"],
        ["options_set_volume_80", "80"],
        ["options_set_volume_70", "70"],
        ["options_set_volume_60", "60"],
        ["options_set_volume_50", "50"],
        ["options_set_volume_40", "40"],
        ["options_set_volume_30", "30"],
        ["options_set_volume_20", "20"],
        ["options_set_volume_10", "10"],
        ["options_set_volume_0", "0"],
        ["back", "Back"]
    ]),
    "Paused": Menu(Vector2(8, 32), "Paused", "", [
        ["back", "Back"],
        ["to_mainmenu", "To Main Menu"]
    ]),
    "Winscreen": Menu(Vector2(20, 64), "", BIG_TEXT["YOU WIN"], [
       ["next_level", "Next level"],
       ["to_mainmenu", "To Main Menu"]
    ]),
    "Winscreen_Custom": Menu(Vector2(20, 64), "", BIG_TEXT["YOU WIN"], [
        ["to_mainmenu", "To Main Menu"]
    ]),
    "Losescreen": Menu(Vector2(16, 70), "", BIG_TEXT["YOU LOSE"], [
        ["try_again", "Try again"],
        ["to_mainmenu", "To Main Menu"]
    ]),
    "LevelSelection": Menu(Vector2(32, 64), "Level selection", "", [])
}

MENUS["MainMenu"].options_offset = Vector2(6, 0)
MENUS["Winscreen"].options_offset = Vector2(4, 0)
MENUS["Winscreen_Custom"].options_offset = Vector2(6, 0)
MENUS["Options_Max_FPS"].options_offset = Vector2(1, 0)
MENUS["Options_Volume"].options_offset = Vector2(1, 0)
MENUS["Losescreen"].options_offset = Vector2(3, 0)

menu: Menu = None
campaign_level: int = 0
level: GameLevel = None
level_time: float = 0
level_score_additive: int = 0
camera_pos: Vector2 = Vector2(0, 0)
event_queue = queue.SimpleQueue()
saved_events = []

def load_colors():
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

def get_screensize():
    return stdscr.getmaxyx()

def load_sound(snd: str):
    global _sound_cache
    _sound_cache[snd] = pygame.mixer.Sound(f"snd/{snd}.wav")

def load_sounds(root: str = "snd"):
    global _sound_cache
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith(".wav"):
                continue

            full_path = os.path.join(dirpath, name)
            key = os.path.relpath(full_path, root)[:-4] # remove ".wav"

            _sound_cache[key] = pygame.mixer.Sound(full_path)

def play_sound(snd: str):
    _sound_cache[snd].set_volume(math.sqrt(config.VOLUME / 100.0))
    _sound_cache[snd].play()

def play_random_sound(snds: list[str]):
    if len(snds) == 0: return
    selected_sound = snds[math.floor(random.random() * len(snds))]
    _sound_cache[selected_sound].set_volume(math.sqrt(config.VOLUME / 100.0))
    _sound_cache[selected_sound].play()

def save_settings():
    with open("config.py", "w") as f:
        for key, val in config.__dict__.items():
            if key.isupper(): f.write(f"{key}={val}\n")

def fire_event(name: str, delay: float = 0, params: any = []):
    global _lifetime
    e: Event = Event(name, delay, params)
    if(len(_registered_events) > 15): _registered_events.clear()
    _registered_events.append((e, _lifetime))
    event_queue.put(e)

def refire_event(e: Event):
    event_queue.put(e)

def handle_input():
    global stdscr
    c = ""
    try:
        c = stdscr.getkey()
    except:
        pass
        
    if(c == -1 or c == ""):
        return
    
    if _gamestate in (Gamestate.INGAME, Gamestate.INGAME_CUSTOM):
        if(c == "KEY_LEFT"): fire_event("PlayerMove", params = Vector2(0, -1))
        elif(c == "KEY_RIGHT"): fire_event("PlayerMove", params = Vector2(0, 1))
        elif(c == "KEY_UP"): fire_event("PlayerMove", params = Vector2(-1, 0))
        elif(c == "KEY_DOWN"): fire_event("PlayerMove", params = Vector2(1, 0))
        elif(c.lower() == "c"): fire_event("PlayerDash")
        elif(c.lower() == "r"): fire_event("PlayerReload")
        elif(c.lower() == "f"): fire_event("PlayerShoot")
        elif(c.lower() == "k" and config.DEBUG): fire_event("TestEventA")
        elif(c.lower() == "l" and config.DEBUG): fire_event("TestEventB")
        elif(c.lower() == "p"): fire_event("Pause")
    else:
        if(c == "KEY_UP"): fire_event("MoveMenuOption", params = -1)
        elif(c == "KEY_DOWN"): fire_event("MoveMenuOption", params = 1)
        elif(c == "KEY_LEFT"): fire_event("BackOption", params = -1)
        elif(c == "KEY_RIGHT"): fire_event("SelectMenuOption")

def get_score():
    global _gamestate
    global level
    global level_time
    global level_score_additive

    if not _gamestate in (Gamestate.INGAME, Gamestate.INGAME_CUSTOM, Gamestate.INGAME_PAUSED): return 0
    return min(level.starting_score + level_score_additive - math.floor(level_time), level.max_score)

def play_level(lvl: GameLevel):
    global level
    global level_time
    global level_score_additive
    if lvl.failed_to_load: return False
    level = lvl.copy()
    level_score_additive = 0
    level_time = 0
    level_sideloading.load_level_objects(level)
    for ent in [obj for obj in level.objects if issubclass(type(obj), Entity)]: level_sideloading.load_entity_weapons(ent)
    level.player = Player(level.spawn.pos.copy())
    level.add_object(level.player)
    if not level.starting_weapon_name == "":
        wep: BaseWeapon = WeaponManager.CreateWeapon(name=level.starting_weapon_name)
        wep.ammo = level.starting_weapon_ammo
        wep.ammo_reserve = level.starting_weapon_ammo_reserve
        level.player.weapons.append(wep)
        level.player.selected_weapon_index = 0

    fire_event("InitializeLevel")
    return True

def get_fps():
    global _frametimes
    avg_frametime = sum(_frametimes) / (float(len(_frametimes) if len(_frametimes) > 0 else 1))
    if(avg_frametime == 0): avg_frametime = 1
    return round(1.0 / avg_frametime)

def get_tps():
    global _deltatimes
    avg_deltatime = sum(_deltatimes) / (float(len(_deltatimes) if len(_deltatimes) > 0 else 1))
    if(avg_deltatime == 0): avg_deltatime = 1
    return round(1.0 / avg_deltatime)

def render_fps():
    global _screensize
    stdscr.addstr(_screensize.y - 2, _screensize.x - 13, f"FPS: {get_fps()}  ")

def render_tps():
    global _screensize
    stdscr.addstr(_screensize.y - 3, _screensize.x - 13, f"TPS: {get_tps()}  ")

def render_hud():
    global HUD_SIZE
    global _screensize
    global _hud_frame_symbol, _hud_frame_attr
    if(level is None or level.player is None): return
    HUD_SIZE = Vector2(HUD_SIZE.y, _screensize.x-1)
    ITEMS_PANEL_POS = Vector2(1, 10)
    ITEMS_PANEL_SIZE = Vector2(HUD_SIZE.y-2, 8)
    render_frame(Vector2(0, 0), HUD_SIZE, _hud_frame_symbol, _hud_frame_attr)
    stdscr.addstr(2, 3, "❤️        ")
    stdscr.addstr(3, 3, "🛡️        ")
    stdscr.addstr(2, 6, f"{level.player.health}")
    stdscr.addstr(3, 6, f"{level.player.armor}")
    render_frame(ITEMS_PANEL_POS, ITEMS_PANEL_SIZE, '*')
    stdscr.addstr(ITEMS_PANEL_POS.y, ITEMS_PANEL_POS.x + round(ITEMS_PANEL_SIZE.x/2 - len("ITEMS") / 2), "ITEMS")
    if level.player.has_dash: stdscr.addstr(ITEMS_PANEL_POS.y + 1, ITEMS_PANEL_POS.x + 2, "💨")
    if level.player.has_flag: stdscr.addstr(ITEMS_PANEL_POS.y + 1, ITEMS_PANEL_POS.x + 4, "🚩")

    stdscr.addstr(7, 3, f"Level: {level.name}")
    stdscr.addstr(8, 3, "Get the flag and bring it back to spawn")

def render_frame(pos: Vector2, size: Vector2, symbol: str = '#', symbol_attr: int = 0):
    try: stdscr.addstr(pos.y, pos.x, symbol * size.x, symbol_attr)
    except: pass
    try: stdscr.addstr(pos.y + size.y, pos.x, symbol * size.x, symbol_attr)
    except: pass
    for i in range(size.y+1):
        try: stdscr.addch(pos.y + i, pos.x, symbol, symbol_attr)
        except: pass
        try: stdscr.addch(pos.y + i, pos.x + size.x, symbol, symbol_attr)
        except: pass

def render_window_frame(symbol: str = '.'):
    global _screensize

    try:
        render_frame(Vector2(0, 0), Vector2(_screensize.y-1, _screensize.x-1), '.')
    except:
        pass

def render_level_frame(symbol: str = '#', symbol_attr: int = 0):
    global HUD_SIZE
    global _screensize

    viewport_pos = Vector2(HUD_SIZE.y+1, 1)
    viewport_size = _screensize.add(-HUD_SIZE.y-3, -2)

    render_frame(Vector2(viewport_pos.y-1, viewport_pos.x-1), Vector2(viewport_size.y+2, viewport_size.x+1), symbol, symbol_attr)

def render_menu(menu: Menu, pos: Vector2):
    global _screensize
    render_frame(Vector2(pos.y-math.floor(menu.size.y/2)-1, pos.x-math.floor(menu.size.x/2)-1), menu.size.add(2, 2), ' ', curses.COLOR_BLACK)
    render_frame(Vector2(pos.y-math.floor(menu.size.y/2), pos.x-math.floor(menu.size.x/2)), menu.size, menu.frame_symbol, menu.frame_attr)

    stdscr.addstr(pos.y-math.floor(menu.size.y/2), pos.x-math.floor(len(menu.caption)/2), menu.caption)

    for i in range(1, menu.size.y):
        stdscr.addstr(math.floor(pos.y - menu.size.y/2) + i, math.floor(pos.x - menu.size.x/2)+1, ' ' * ((menu.size.x - 2) + 1))

    description_lines = menu.description.split('\n')
    for i in range(len(description_lines)):
        stdscr.addstr(pos.y-math.floor(menu.size.y/2) + 2 + i, pos.x-math.floor(len(description_lines[i])/2), description_lines[i])
    
    max_option_len = len(menu.options[0][1]) if len(menu.options[0]) > 0 else 0
    option_count = len(menu.options)
    for i in range(len(menu.options)-1):
        option = menu.options[i]
        stdscr.addstr(menu.options_offset.y + math.floor(pos.y - math.floor(option_count/2)) + i, menu.options_offset.x + math.floor(pos.x - len(option[1])/2), f" {option[1]} ")
        max_option_len = max(max_option_len, len(option[1]))
    
    last_option = menu.options[-1]
    stdscr.addstr(menu.options_offset.y + math.floor(pos.y - math.floor(option_count/2)) + len(menu.options), menu.options_offset.x + math.floor(pos.x - len(last_option[1])/2), f" {last_option[1]} ")
    max_option_len = max(max_option_len, len(last_option[1]))
    
    if len(menu.options) > 0:
        stdscr.addch(menu.options_offset.y + math.floor(pos.y - math.floor(option_count/2)) + menu.selected_option + (1 if menu.selected_option == len(menu.options)-1 else 0), menu.options_offset.x + math.floor(pos.x - max_option_len/2)-2, '>')

def render_current_menu():
    global menu
    render_menu(menu, Vector2(_screensize.y / 2, _screensize.x / 2))

def level_coords_to_matrix(pos_in: Vector2):
    global camera_pos
    global _screensize
    viewport_size = _screensize.add(-HUD_SIZE.y-2, -2)
    viewport_size_half = viewport_size.mul(0.5)
    
    pos = pos_in.copy()
    pos.y = pos.y - camera_pos.y + viewport_size_half.y
    pos.x = pos.x*2 - camera_pos.x * 2 + viewport_size_half.x
    return pos

def matrix_coords_to_level(pos_in: Vector2):
    global camera_pos
    global _screensize
    viewport_size = _screensize.add(-HUD_SIZE.y-2, -2)
    viewport_size_half = viewport_size.mul(0.5)

    pos = pos_in.copy()
    pos.y = pos.y + camera_pos.y - viewport_size_half.y
    pos.x = math.floor((pos.x - viewport_size_half.x + camera_pos.x * 2)/2)
    return pos

def render_ingame_matrix():
    global stdscr
    global HUD_SIZE
    global camera_pos
    global _screensize

    viewport_pos = Vector2(HUD_SIZE.y+1, 1)
    viewport_size = _screensize.add(-HUD_SIZE.y-2, -2)
    viewport_size_half = viewport_size.mul(0.5)

    OUT_OF_BOUNDS = '·'
    AIR = ' '

    render_matrix = []
    for i in range(viewport_size.y):
        row = []
        for j in range(viewport_size.x):
            global_pos = matrix_coords_to_level(Vector2(i, j))
            if 0 <= global_pos.y < level.size.y and 0 <= global_pos.x < level.size.x:
                row.append(AIR)
            else:
                row.append(OUT_OF_BOUNDS if -1 <= global_pos.y <= level.size.y and (-1 <= global_pos.x <= level.size.x and j % 2 == 0) else AIR)
        render_matrix.append(row)
    
    for obj in level.objects:
        if(obj.hidden): continue
        matrix_pos = level_coords_to_matrix(obj.pos)
        oy = matrix_pos.y
        ox = matrix_pos.x

        if(obj.type == "Label"):
            lines = obj.text.split('\n')
            for i in range(len(lines)):
                line = lines[i]
                char_y = oy+i 
                for j in range(len(line)):
                    char_x = ox+j
                    if not(0 < char_y < len(render_matrix) and
                           0 < char_x < len(render_matrix[char_y])): continue
                    render_matrix[char_y][char_x] = line[j]
            continue

        # frustum culling
        if not((0 < oy < viewport_size.y) and
               (0 < ox < viewport_size.x)): continue

        # projectiles have subpos rendering on the X axis
        if(issubclass(type(obj), Projectile)):
            sp = round(obj.subpos.x)
            if 0 <= ox + sp < viewport_size.x:
                if render_matrix[oy][ox + sp] == '' or ord(render_matrix[oy][ox]) > 255:
                    sp = 0
                render_matrix[oy][ox + sp] = obj.symbol
                if ox + sp + 1 < viewport_size.x and render_matrix[oy][ox + sp + 1] == '': render_matrix[oy][ox + sp + 1] = AIR
        else:
            if(ord(obj.symbol) < 255 or ox <= viewport_size.x-2):
                render_matrix[oy][ox] = obj.symbol

        # edge case for emoji symbol on the right edge of the viewport
        if ox < viewport_size.x-1:
            if ord(obj.symbol) > 255:
                render_matrix[oy][ox+1] = ''
            else:
                if(render_matrix[oy][ox] == ''): render_matrix[oy][ox+1] = AIR
    
    for i in range(len(render_matrix)):
        row = render_matrix[i]
        stdscr.addstr(viewport_pos.y + i, viewport_pos.x, ''.join(row))

def render_clear():
    global stdscr
    stdscr.clear()

def render():
    global _gamestate
    global _screensize

    new_screensize = Vector2(get_screensize()[0], get_screensize()[1])

    if(new_screensize != _screensize): stdscr.clear()

    _screensize = new_screensize

    if(_gamestate in (Gamestate.INGAME, Gamestate.INGAME_CUSTOM)):
        render_level_frame()
        render_hud()
        render_ingame_matrix()
    else:
        render_current_menu()
    
    if(config.DISPLAY_FPS): render_fps()
    if(config.DISPLAY_TPS): render_tps()

def on_collide(a: GameObject, b: GameObject):
    if(_gamestate == Gamestate.INGAME_PAUSED): return False
    if issubclass(type(a), Wall): a, b = b, a
    elif issubclass(type(b), Entity) and not issubclass(type(a), Entity): a, b = b, a
    
    if issubclass(type(a), Entity) and issubclass(type(b), Solid):
        return True

    if issubclass(type(a), Player) and issubclass(type(b), Flag):
        fire_event("PlayerObtainedFlag")
        return False

    elif issubclass(type(a), Player) and issubclass(type(b), Spawn) and a.has_flag:
        fire_event("FlagCaptured")
        return False

    elif issubclass(type(a), Entity) and issubclass(type(b), Hazard) and not a.invulnerable:
        fire_event("EntityHurt", 0, (a, b.damage))
        return True
    
    elif issubclass(type(a), Entity) and issubclass(type(b), Bullet) and not a.invulnerable and not b.owner == a:
        fire_event("EntityHurt", 0, (a, b.damage))
        if b.pierce != -1:
            b.pierce -= 1
            if b.pierce < 0: level.delete_object(b)
        return False

    elif issubclass(type(a), Bullet) and issubclass(type(b), Wall):
        if(a.wallbang != -1):
            a.wallbang -= 1
            if(a.wallbang < 0):
                level.delete_object(a)
        
        if(b.breakable): level.delete_object(b)
        return False
    
    elif issubclass(type(a), Bullet) and issubclass(type(b), Solid):
        if not b.background: level.delete_object(a)
        return True

    else: return False

def move_object(a: GameObject, move: Vector2):
    if(_gamestate == Gamestate.INGAME_PAUSED): return

    move_x = 0
    move_y = 0

    if move.x != 0:
        for i in range(sign(move.x), move.x + sign(move.x), sign(move.x)):
            if 0 > a.pos.x + i >= level.size.x:
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
            if 0 > a.pos.y + i >= level.size.y:
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

    if a == None or a.deleted: return
    a.pos = a.pos.add(move_y, move_x)

def change_gamestate(gamestate: Gamestate):
    global _gamestate
    global menu
    global _previous_gamestate
    global _hud_frame_symbol, _hud_frame_symbol

    _hud_frame_symbol = '#'
    _hud_frame_attr = 0

    if(gamestate == Gamestate.MAIN_MENU):
        render_clear()
        render_window_frame()
        level = None
        menu = MENUS["MainMenu"]
    elif(gamestate == Gamestate.OPTIONS):
        menu = MENUS["Options"]
    elif(gamestate == Gamestate.INGAME_PAUSED):
        menu = MENUS["Paused"]
    elif(gamestate == Gamestate.INGAME):
        menu = None
        render_clear()
        render_level_frame()
        render_hud()
    elif(gamestate == Gamestate.INGAME_CUSTOM):
        menu = None
        render_clear()
        render_hud()
    elif(gamestate == Gamestate.WINSCREEN):
        menu = MENUS["Winscreen"] if _gamestate == Gamestate.INGAME and campaign_level < len(BUILTIN_LEVELS) - 1 else MENUS["Winscreen_Custom"]
    elif(gamestate == Gamestate.LOSESCREEN):
        menu = MENUS["Losescreen"]
    
    _previous_gamestate = _gamestate
    _gamestate = gamestate

def process_menu_action(action: str):
    global _quit
    global _options_saved_volume
    global menu
    global campaign_level
    global _previous_gamestate
    if(action == "play_builtin"):
        campaign_level = 0
        if play_level(BUILTIN_LEVELS[campaign_level]): change_gamestate(Gamestate.INGAME)
    elif(action == "play_custom"):
        menu = MENUS["LevelSelection"]
        menu.options.clear()
        for i in range(len(level_sideloading.loaded_levels)):
            lv = level_sideloading.loaded_levels[i]
            menu.options.append([f"select_level_{i}", f"{lv.name}"])
        menu.options.append(["back", "Back"])
    elif(action == "try_again"):
        change_gamestate(_previous_gamestate)
        play_level(level.original)
    elif(action.startswith("select_level_")):
        lv_num = int(action.split('_')[-1])
        if play_level(level_sideloading.loaded_levels[lv_num]): change_gamestate(Gamestate.INGAME_CUSTOM)
    elif(action == "open_options"):
        change_gamestate(Gamestate.OPTIONS)
        _options_saved_volume = config.VOLUME
        menu = MENUS["Options"]
    elif(action == "back"):
        if(_gamestate == Gamestate.INGAME_PAUSED): fire_event("Unpause")
        elif(_gamestate == Gamestate.MAIN_MENU and menu == MENUS["LevelSelection"]):
            render_clear()
            render_window_frame()
            menu = MENUS["MainMenu"]
        elif(_gamestate == Gamestate.OPTIONS):
            config.VOLUME = _options_saved_volume
            if(menu == MENUS["Options"]):
                change_gamestate(Gamestate.MAIN_MENU)
                save_settings()
            else: menu = MENUS["Options"]
        else: _options_saved_volume = config.VOLUME
    elif(action == "to_mainmenu"):
        change_gamestate(Gamestate.MAIN_MENU)
    elif(action == "next_level"):
        campaign_level += 1
        if play_level(BUILTIN_LEVELS[campaign_level]): change_gamestate(Gamestate.INGAME)
        else: change_gamestate(Gamestate.MAIN_MENU)
    elif(action == "options_set_target_tickrate"):
        menu = MENUS["Options_Target_Tickrate"]
        menu.description = f"Current Value: {config.TARGET_TICKRATE}"
        selected_option = [option for option in menu.options if option[1] != "Back" and int(option[0].split('_')[-1]) <= config.TARGET_TICKRATE][0]
        menu.selected_option = menu.options.index(selected_option)
    elif(action == "options_set_max_fps"):
        menu = MENUS["Options_Max_FPS"]
        menu.description = f"Current Value: {config.TARGET_FPS}"
        selected_option = [option for option in menu.options if option[1] != "Back" and int(option[0].split('_')[-1]) <= config.TARGET_FPS][0]
        menu.selected_option = menu.options.index(selected_option)
    elif(action == "options_set_volume"):
        _options_saved_volume = config.VOLUME
        menu = MENUS["Options_Volume"]
        menu.description = f"Current Value: {config.VOLUME}"
        selected_option = [option for option in menu.options if option[1] != "Back" and int(option[0].split('_')[-1]) <= config.VOLUME][0]
        menu.selected_option = menu.options.index(selected_option)
    elif(action.startswith("options_set_target_tickrate_")):
        config.TARGET_TICKRATE = int(action.split('_')[-1])
        config.TARGET_TIME_PER_TICK = 1.0 / config.TARGET_TICKRATE
        [option for option in MENUS["Options"].options if option[0] == "options_set_target_tickrate"][0][1] = f"Target Tickrate ({config.TARGET_TICKRATE})"
        menu = MENUS["Options"]
    elif(action.startswith("options_set_max_fps_")):
        config.TARGET_FPS = int(action.split('_')[-1])
        config.TARGET_FRAMETIME = 1.0 / config.TARGET_FPS
        [option for option in MENUS["Options"].options if option[0] == "options_set_max_fps"][0][1] = f"Max FPS ({config.TARGET_FPS})"
        menu = MENUS["Options"]
    elif(action.startswith("options_set_volume_")):
        config.VOLUME = int(action.split('_')[-1])
        [option for option in MENUS["Options"].options if option[0] == "options_set_volume"][0][1] = f"Volume ({config.VOLUME})"
        menu = MENUS["Options"]
    elif(action == "options_set_debug"):
        config.DEBUG = not config.DEBUG
        [option for option in MENUS["Options"].options if option[0] == "options_set_debug"][0][1] = f"Debug Mode ({config.DEBUG})"
    elif(action == "options_set_show_fps"):
        config.DISPLAY_FPS = not config.DISPLAY_FPS
        if not config.DISPLAY_FPS: stdscr.addstr(_screensize.y - 2, _screensize.x - 13, "         ")
        [option for option in MENUS["Options"].options if option[0] == "options_set_show_fps"][0][1] = f"Display FPS ({config.DISPLAY_FPS})"
    elif(action == "options_set_show_tps"):
        config.DISPLAY_TPS = not config.DISPLAY_TPS
        if not config.DISPLAY_TPS: stdscr.addstr(_screensize.y - 3, _screensize.x - 13, "         ")
        [option for option in MENUS["Options"].options if option[0] == "options_set_show_tps"][0][1] = f"Display TPS ({config.DISPLAY_TPS})"
    elif(action == "quit"): _quit = True

def tick():
    global stdscr
    global event_queue
    global menu
    global _previous_gamestate
    global saved_events
    global campaign_level
    global _deltatime, _timescale
    global level_time, level_score_additive
    global camera_pos
    global _hud_frame_symbol, _hud_frame_attr

    dt = _deltatime * _timescale

    if(_gamestate in (Gamestate.INGAME, Gamestate.INGAME_CUSTOM)):
        level_time += dt

        if(level.player.dash_cooldown > 0):
            level.player.dash_cooldown = max(0, level.player.dash_cooldown - dt)

        for projectile in [projectile for projectile in level.objects if issubclass(type(projectile), Projectile)]:
            if projectile.deleted: continue
            projectile.lifetime -= dt
            if(projectile.lifetime <= 0): 
                level.delete_object(projectile)
                continue
            projectile.subpos = projectile.subpos.add(projectile.direction.y * projectile.speed * dt, projectile.direction.x * projectile.speed * dt)
            move = Vector2(math.floor(projectile.subpos.y) if sign(projectile.subpos.y) == 1 else math.ceil(projectile.subpos.y),
                           math.floor(projectile.subpos.x) if sign(projectile.subpos.x) == 1 else math.ceil(projectile.subpos.x))

            if(move.y != 0 or move.x != 0):
                projectile.subpos = projectile.subpos.add(-move.y, -move.x)
                move_object(projectile, move)

        for entity in [entity for entity in level.objects if issubclass(type(entity), Entity)]:
            if entity.deleted: continue

            selected_weapon: BaseWeapon = entity.get_selected_weapon()

            if not selected_weapon is None:
                selected_weapon.shooting_time_left = max(0, selected_weapon.shooting_time_left - dt)
                if selected_weapon.reloading_time_left > 0 and selected_weapon.reloading_time_left - dt <= 0:
                    selected_weapon.reloading_time_left = 0
                    selected_weapon.reloading = False
                    selected_weapon.finish_reload()
                elif selected_weapon.reloading_time_left > 0:
                    selected_weapon.reloading_time_left -= dt

            if issubclass(type(entity), Enemy):
                decision: EnemyAction = entity.think(level, dt)
                if decision is None: continue
                if(decision.action == "Move"):
                    fire_event("EntityMove", params=(entity, decision.move))
                elif(decision.action == "TackleEntity"):
                    fire_event("EntityTackleEntity", params=(entity, decision.target)) 
                elif(decision.action == "Shoot"):
                    fire_event("EntityShoot", params=entity) 

    repeat_events = []
    while(not event_queue.empty()):
        e: Event = event_queue.get()
        if(e.delay > 0):
            repeat_events.append(e)
            e.delay -= 1
            continue
        
        elif(e.name == "MoveMenuOption"):
            menu.selected_option = min(len(menu.options)-1, max(menu.selected_option + e.params, 0))
            if(menu == MENUS["Options_Volume"]): config.VOLUME = max(0, min(10, 10 - menu.selected_option)) * 10
            play_sound("select")
        
        elif(e.name == "SelectMenuOption"):
            process_menu_action(menu.options[menu.selected_option][0])
            play_sound("select")
        
        elif(e.name == "BackOption"):
            process_menu_action("back")
            play_sound("select")

        elif(e.name == "InitializeLevel"):
            stdscr.clear()
            _hud_frame_symbol = '#'
            _hud_frame_attr = 0
            camera_pos = level.player.pos.copy()

        elif(e.name == "TestEventA"):
            for entity in [entity for entity in level.objects if issubclass(type(entity), Entity)]:
                entity.health = 10
                entity.armor = 0

            level.player.health = 100
            level.player.armor = 100
            level.player.weapons.append(WeaponManager.CreateWeapon(name="Shotgun"))
            level.player.weapons.append(WeaponManager.CreateWeapon(name="Railgun"))
            level.player.selected_weapon_index = 2
        
        elif(e.name == "TestEventB"):
            sentry = Mercenary(level.player.pos.add(0, 7))
            sentry.weapons.append(WeaponManager.CreateWeapon(name="EnemyShotgun"))
            sentry.selected_weapon_index = 0
            level.objects.append(sentry)

        elif(e.name == "PlayerShoot"):
            fire_event("EntityShoot", params=level.player)
        
        elif(e.name == "PlayerObtainedFlag"):
            play_sound('pickup')
            level.delete_object(level.flag)
            level.player.has_flag = True
        
        elif(e.name == "Pause"):
            saved_events.clear()
            while not event_queue.empty():
                saved_events.append(event_queue.get())
            
            change_gamestate(Gamestate.INGAME_PAUSED)
        
        elif(e.name == "Unpause"):
            while len(saved_events) > 0:
                event_queue.put(saved_events[-1])
                saved_events.remove(saved_events[-1])

            change_gamestate(_previous_gamestate)

        elif(e.name == "ToMainMenu"):
            change_gamestate(Gamestate.MAIN_MENU)

        elif(e.name == "Victory"):
            play_sound('victory')
            while not event_queue.empty():
                event_queue.get()

            change_gamestate(Gamestate.WINSCREEN)
        
        elif(e.name == "FlagCaptured"):
            fire_event("Victory")

        elif(e.name == "EntityHurt"):
            entity, dmg = e.params
            if(dmg <= 0): continue
            play_sound('hurt')
            armor_absorbed_dmg = min(entity.armor, math.ceil(dmg * 0.66))
            entity.health -= max(0, dmg - armor_absorbed_dmg)
            entity.armor -= max(0, armor_absorbed_dmg)

            if(entity.health <= 0):
                fire_event("EntityDying", params=entity)

            if(entity == level.player):
                _hud_frame_symbol = '@'
                _hud_frame_attr = curses.color_pair(1)
                fire_event("PlayerHurtFlashOver", delay = 0.2)

        elif(e.name == "EntityDying"):
            entity = e.params
            level.delete_object(entity)
            if(entity == level.player):
                while not event_queue.empty():
                    event_queue.get()

                fire_event("Defeat", delay=0.01)
            else:
                play_sound('kill')
        
        elif(e.name == "PlayerReload"):
            fire_event("EntityReload", params=level.player)

        elif(e.name == "EntityReload"):
            entity: Entity = e.params
            selected_weapon: BaseWeapon = entity.get_selected_weapon()

            if selected_weapon is None: continue
            if selected_weapon.reloading > 0 or selected_weapon.reloading_time_left > 0: continue

            play_random_sound(selected_weapon.sounds["reload"])
            selected_weapon.reload()

        elif(e.name == "Defeat"):
            play_sound('death')
            change_gamestate(Gamestate.LOSESCREEN)

        elif(e.name == "PlayerDash"):
            if (not level.player.has_dash) or level.player.dash_speed == 0 or level.player.dash_cooldown > 0: return
            play_sound('dash')
            level.player.dash_cooldown = 1
            level.player.invulnerable = True
            fire_event("PlayerMove", params = Vector2.from_Vector2F(level.player.direction.mul(level.player.dash_speed)))
            level.player.invulnerable = False

        elif(e.name == "PlayerMove"):
            level.player.direction = Vector2F.from_Vector2(e.params.normalize())
            move_object(level.player, e.params)
            camera_pos = level.player.pos.copy()
        
        elif(e.name == "PlayerHurtFlashOver"):
            _hud_frame_symbol = '#'
            _hud_frame_attr = 0
        
        elif(e.name == "EntityMove"):
            entity, move = e.params
            move_object(entity, move)
        
        elif(e.name == "EntityTackleEntity"):
            e1, e2 = e.params
            if(e2.invulnerable): return
            fire_event("EntityHurt", params=(e2, max(0, e1.strength)))
        
        elif(e.name == "EntityShoot"):
            entity: Entity = e.params
            selected_weapon: BaseWeapon = entity.get_selected_weapon()

            if selected_weapon is None: continue
            if selected_weapon.shooting_time_left > 0: continue
            if selected_weapon.reloading: continue

            if selected_weapon.shoot(level, entity):
                play_random_sound(selected_weapon.sounds["shoot"])
            else:
                play_sound("weapons/noammo")
    
    for e in repeat_events: refire_event(e)

def main(stdscr_in):
    global stdscr
    global _quit
    global _lifetime
    global _frametime
    global _screensize
    global _deltatime
    global BUILTIN_LEVELS
    stdscr = stdscr_in
    stdscr.clear()
    stdscr.nodelay(True)
    _screensize.y, _screensize.x = get_screensize()

    if(_screensize.y < 36 or _screensize.x < 76):
        return 1
    
    pygame.mixer.init()
    load_colors()
    load_sounds()
    BUILTIN_LEVELS = level_sideloading.load_levels(BUILTIN_LEVELS_SERIAL)

    last_time = time.perf_counter()
    last_tick_time = time.perf_counter()
    accumulator = 0

    change_gamestate(Gamestate.MAIN_MENU)
    while True:
        frame_start = time.perf_counter()
        _lifetime += _frametime
        last_time = frame_start
        handle_input()
        while (accumulator >= config.TARGET_TIME_PER_TICK):
            _deltatime = time.perf_counter() - last_tick_time
            if(len(_deltatimes) > 1000): _deltatimes.clear()
            _deltatimes.append(_deltatime)
            tick()
            last_tick_time = time.perf_counter()
            accumulator -= config.TARGET_TIME_PER_TICK
        render()

        if(_screensize.y < 20 or _screensize.x < 76): return 1
        if _quit: break

        _frametime = time.perf_counter() - frame_start
        if(len(_frametimes) > 1000): _frametimes.clear()
        if(config.TARGET_FRAMETIME > _frametime):
            _frametimes.append(config.TARGET_FRAMETIME)
            time.sleep(config.TARGET_FRAMETIME - _frametime)
            accumulator += config.TARGET_FRAMETIME
        else:
            _frametimes.append(_frametime)
            accumulator += _frametime

    return 0

retcode = curses.wrapper(main)
if retcode == 1:
    print("The console window isn't big enough for the game! Please run the game in a bigger terminal window.")