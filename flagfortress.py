"""
# pip install pygame
# pip install playsound==1.2.2
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import time
import queue
import math
import config
import pygame
from enum import Enum
from levels_builtin import BUILTIN_LEVELS, BUILTIN_LEVELS_COUNT
from models import sign, Vector2, GameObject, Player, Wall, Spawn, Flag, PlayerBullet, Event, GameLevel, Menu

_sound_cache = {}
_quit: bool = False
_frametime: float = 1
_lifetime: float = 0
_registered_events = []
_screensize: Vector2 = Vector2(10, 10)
class Gamestate(Enum):
    MAIN_MENU = 0
    INGAME_BUILTIN = 1
    INGAME_CUSTOM = 2
    INGAME_PAUSED = 3
    OPTIONS = 4
    WINSCREEN = 5
_gamestate: Gamestate = Gamestate.MAIN_MENU
stdscr = None

MENUS = {
    "MainMenu": Menu(Vector2(16, 48), "FlagFortress", "", [
        ("play_builtin", "Start Game"),
        ("play_custom", "Play Custom Levels"),
        ("open_options", "Options"),
        ("quit", "Quit")
    ])
}

menu: Menu = None
level: GameLevel = None
last_move = Vector2(0, 0)
event_queue = queue.SimpleQueue()

def load_colors():
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

def update_screen_size():
    global _screensize
    global stdscr
    _screensize.y, _screensize.x = stdscr.getmaxyx()

def load_sound(snd: str):
    global _sound_cache
    _sound_cache[snd] = pygame.mixer.Sound(f"snd/{snd}.wav")

def load_sounds():
    load_sound("dash")
    load_sound("death")
    load_sound("explosion")
    load_sound("hurt")
    load_sound("level_complete")
    load_sound("pickup")
    load_sound("rg_reloaded")
    load_sound("rg_shoot_a")
    load_sound("rg_shoot_b")
    load_sound("rl_shoot")
    load_sound("select")
    load_sound("shoot")
    load_sound("victory")

def play_sound(snd: str):
    _sound_cache[snd].play()

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
    global last_move
    c = ""
    try:
        c = stdscr.getkey()
    except:
        pass
        
    if(c == -1 or c == ""):
        return
    
    if(_gamestate == Gamestate.INGAME_BUILTIN or _gamestate == Gamestate.INGAME_CUSTOM):
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
        if(c.lower() == "m"):
            fire_event("ToMainMenu")
        if(c.lower() == "c"):
            fire_event("PlayerDash", params = last_move.mul(3))
        if(c.lower() == "f"):
            fire_event("Shoot")
        if(c.lower() == "k"):
            fire_event("PlayerHurt", params = 1)

def load_level_builtin(num: int):
    load_level(BUILTIN_LEVELS[num])

def load_level(lvl: GameLevel, custom: bool = False):
    global level

    change_gamestate(Gamestate.INGAME_BUILTIN if not custom else Gamestate.INGAME_CUSTOM)

    level = lvl
    level.player = Player(level.spawn.pos.copy())
    level.add_object(level.player)
    level.player.ammo_left = level.starting_ammo
    fire_event("InitializeLevel")

def get_fps():
    return round(1.0 / _frametime)

def render_fps():
    global _screensize
    stdscr.addstr(2, _screensize.x - 16, f"FPS: {get_fps()}     ")

def render_hud():
    stdscr.addstr(2, 3, "Arrow Keys - Move | C - Dash | F - Shoot | M - Main Menu | CTRL+C - Quit")
    stdscr.addstr(4, 3, f"HP: {0 if level.player is None else level.player.health}")
    stdscr.addstr(5, 3, f"Ammo left: {0 if level.player is None else level.player.ammo_left}")
    stdscr.addstr(7, 3, f"Level: {level.name} (#{level.num})")
    stdscr.addstr(8, 3, "Get the flag and bring it back to spawn")
    render_fps()

def render_debug():
    global _registered_events
    global _screensize

    for i in range(_screensize.y - (config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 4)):
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 3, " " * 60)

    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 2, 3, "GameObjects")
    for i in range(len(level.objects)):
        obj = level.objects[i]
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 3, obj.type + str(obj.pos))
    
    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 2, 40, "Events")
    for i in range(len(_registered_events)):
        e = _registered_events[i]
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 40, f"{'%.1f' % e[1]}: {e[0].name}")

def render_frame(pos: Vector2, size: Vector2, symbol: str = '#', symbol_attr: int = 0):
    stdscr.addstr(pos.y, pos.x, symbol * size.x, symbol_attr)
    stdscr.addstr(pos.y + size.y, pos.x, symbol * size.x, symbol_attr)
    for i in range(size.y+1):
        stdscr.addch(pos.y + i, pos.x, symbol, symbol_attr)
        stdscr.addch(pos.y + i, pos.x + size.x, symbol, symbol_attr)

def render_window_frame(symbol: str = '.'):
    global _screensize

    try:
        render_frame(Vector2(0, 0), Vector2(_screensize.y-1, _screensize.x-1), '.')
    except:
        pass

def render_level_frame(symbol: str = '#', symbol_attr: int = 0):
    render_frame(Vector2(config.LEVEL_SCREEN_OFFSET_Y-1, config.LEVEL_SCREEN_OFFSET_X-1), Vector2(config.LEVEL_HEIGHT+2, config.LEVEL_WIDTH*2+3), symbol, symbol_attr)

def initial_ingame_render():
    render_window_frame()
    render_hud()
    render_level_frame()

def render_current_menu():
    global menu
    global _screensize
    render_frame(Vector2(math.floor(_screensize.y/2 - menu.size.y/2)-1, math.floor(_screensize.x/2 - menu.size.x/2)-1), menu.size.add(2, 2), ' ', curses.COLOR_BLACK)
    render_frame(Vector2(math.floor(_screensize.y/2 - menu.size.y/2), math.floor(_screensize.x/2 - menu.size.x/2)), menu.size, menu.frame_symbol, menu.frame_attr)

    stdscr.addstr(math.floor(_screensize.y/2 - menu.size.y/2), math.floor(_screensize.x/2 - len(menu.caption)/2), menu.caption)

    for i in range(1, menu.size.y):
        stdscr.addstr(math.floor(_screensize.y/2 - menu.size.y/2) + i, math.floor(_screensize.x/2 - menu.size.x/2)+1, ' ' * (menu.size.x - 2))
    
    max_option_len = len(menu.options[0][1]) if len(menu.options[0]) > 0 else 0
    option_count = len(menu.options)
    for i in range(len(menu.options)):
        option = menu.options[i]
        stdscr.addstr(math.floor(_screensize.y/2 - math.floor(option_count/2)) + i, math.floor(_screensize.x/2 - len(option[1])/2)+1, option[1])
        max_option_len = max(max_option_len, len(option[1]))
    
    stdscr.addch(math.floor(_screensize.y/2 - math.floor(option_count/2)) + menu.selected_option, math.floor(_screensize.x/2 - max_option_len/2)-2, '>')

def render_ingame_seperate():
    global stdscr

    for i in range(config.LEVEL_HEIGHT + 1):
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X, "!" * (config.LEVEL_WIDTH * 2 + 2))
    
    for obj in level.objects:
        if(obj.hidden): continue
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + obj.pos.y, config.LEVEL_SCREEN_OFFSET_X + obj.pos.x * 2, obj.symbol)
    
    if(not level.player is None):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + level.player.pos.y, config.LEVEL_SCREEN_OFFSET_X + level.player.pos.x * 2, level.player.symbol)

def render_ingame_matrix():
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

def render():
    global _gamestate
    if(_gamestate == Gamestate.INGAME_BUILTIN or
       _gamestate == Gamestate.INGAME_CUSTOM):
        render_ingame_matrix()
        if(config.DEBUG): render_debug()

    elif(_gamestate == Gamestate.MAIN_MENU or
         _gamestate == Gamestate.OPTIONS or
         _gamestate == Gamestate.INGAME_PAUSED):
        render_current_menu()

def on_collide(a: GameObject, b: GameObject):
    if(a.type == "Player" and b.type == "Flag" and not b.hidden):
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

def change_gamestate(gamestate: Gamestate):
    global _gamestate
    global menu
    if(gamestate == Gamestate.MAIN_MENU): menu = MENUS["MainMenu"]
    elif(gamestate == Gamestate.OPTIONS): menu = MENUS["Options"]
    elif(gamestate == Gamestate.INGAME_PAUSED): menu = MENUS["Paused"]
    else: menu = None
        
    _gamestate = gamestate

def tick():
    global stdscr
    global event_queue

    repeat_events = []
    while(not event_queue.empty()):
        e: Event = event_queue.get()
        if(e.delay > 0):
            repeat_events.append(e)
            e.delay -= 1
            continue
        
        elif(e.name == "InitializeLevel"):
            stdscr.clear()
            initial_ingame_render()

        elif(e.name == "Shoot"):
            if(level.player.ammo_left <= 0): continue

            level.player.ammo_left -= 1
            render_hud()

            play_sound('shoot')

            bullet = PlayerBullet(level.player.pos.copy(), last_move.normal())
            level.add_object(bullet)
            fire_event("BulletMove", 0, bullet)
        
        elif(e.name == "BulletMove"):
            bullet = e.params
            if(bullet == None or bullet.deleted): continue
            move_object(bullet, bullet.direction)
            fire_event("BulletMove", 1 / bullet.speed, bullet)
        
        elif(e.name == "ObtainedFlag"):
            play_sound('pickup')
            level.flag.hidden = True
        
        elif(e.name == "ToMainMenu"):
            change_gamestate(Gamestate.MAIN_MENU)

        elif(e.name == "Victory"):
            play_sound('victory')
            change_gamestate(Gamestate.WINSCREEN)
        
        elif(e.name == "FlagCaptured"):
            play_sound('level_complete')
            fire_event("LevelComplete")
            if(_gamestate == Gamestate.INGAME_BUILTIN and level.num == BUILTIN_LEVELS_COUNT):
                while not event_queue.empty():
                    event_queue.get()

                fire_event("Victory")
                continue

            load_level_builtin(level.num)

        elif(e.name == "PlayerDash"):
            if (not level.player.has_dash) or level.player.dash_speed == 0: return
            play_sound('dash')
            level.player.invulnerable = True
            fire_event("PlayerMove", params = last_move.mul(level.player.dash_speed))
            level.player.invulnerable = False

        elif(e.name == "PlayerMove"):
            move_object(level.player, e.params)
        
        elif(e.name == "PlayerHurt"):
            if(level.player.invulnerable): return
            play_sound('hurt')
            level.player.health -= e.params
            render_level_frame('@', curses.color_pair(1))
            fire_event("PlayerHurtFlashOver", delay = 0.2)
            # todo
        
        elif(e.name == "PlayerHurtFlashOver"):
            render_level_frame('#')
    
    for e in repeat_events: refire_event(e)

def main(stdscr_in):
    global stdscr
    global _quit
    global _lifetime
    global _frametime
    stdscr = stdscr_in
    stdscr.clear()
    stdscr.nodelay(True)
    update_screen_size()

    if(_screensize.y < 30 or _screensize.x < 60):
        return 1
    
    load_colors()
    pygame.mixer.init()
    load_sounds()

    lasttime = time.time_ns() / (10 ** 9)
    accumulator = 0

    _gamestate = Gamestate.INGAME_BUILTIN
    load_level_builtin(0)
    while True:
        newtime = time.time_ns() / (10 ** 9)
        deltatime = newtime - lasttime
        _frametime = deltatime
        _lifetime += deltatime
        accumulator += deltatime
        lasttime = newtime
        handle_input()

        update_screen_size()

        if(accumulator >= config.TARGET_TIME_PER_TICK * 10):
            accumulator = config.TARGET_TIME_PER_TICK
        while (accumulator >= config.TARGET_TIME_PER_TICK):
            tick()
            accumulator -= config.TARGET_TIME_PER_TICK
        render()
        render_fps()

        if _quit:
            break

        if(_frametime < config.TARGET_FRAMETIME): time.sleep(config.TARGET_FRAMETIME)
    
    return 0

retcode = curses.wrapper(main)
if retcode == 0:
    print("You won!")
if retcode == 1:
    print("The console window isn't big enough for the game! Please run the game in a bigger terminal window.")