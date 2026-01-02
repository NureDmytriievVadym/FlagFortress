"""
# pip install pygame
# pip install playsound==1.2.2
# pip install curses (linux)
# pip install windows-curses (windows)
"""

import curses
import time
import queue
import config
import pygame
from models import sign, Vector2, GameObject, Player, Wall, Spawn, Flag, PlayerBullet, Event, GameLevel

_sound_cache = {}
_quit: bool = False
_frametime: float = 1
_lifetime: float = 0
_registered_events = []
gamestate: int = 1 # 0 = main menu, 1 = ingame, 2 = paused, 3 = over
stdscr = None

level = {}
last_move = Vector2(0, 0)
event_queue = queue.SimpleQueue()

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

def play_sound(snd: str):
    _sound_cache[snd].play()

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

def get_fps():
    return round(1.0 / _frametime)

def render_fps():
    maxy, maxx = stdscr.getmaxyx()
    stdscr.addstr(2, maxx - 16, f"FPS: {get_fps()}     ")

def render_hud():
    stdscr.addstr(2, 3, "Arrow Keys - Move | C - Dash | F - Shoot | M - Main Menu")
    stdscr.addstr(4, 3, f"HP: {0 if level.player is None else level.player.health}")
    stdscr.addstr(5, 3, f"Ammo left: {0 if level.player is None else level.player.ammo_left}")
    stdscr.addstr(7, 3, f"Level: {level.name} (#{level.num})")
    stdscr.addstr(8, 3, "Get the flag and bring it back to spawn")
    render_fps()

def render_debug():
    global _registered_events

    for i in range(stdscr.getmaxyx()[0] - (config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 4)):
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 3, " " * 60)

    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 2, 3, "GameObjects")
    for i in range(len(level.objects)):
        obj = level.objects[i]
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 3, obj.type + str(obj.pos))
    
    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 2, 40, "Events")
    for i in range(len(_registered_events)):
        e = _registered_events[i]
        stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 3 + i, 40, f"{'%.1f' % e[1]}: {e[0].name}")

def render_window_frame(symbol: str = '.'):
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

def render_level_frame(symbol: str = '#'):
    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y-1, config.LEVEL_SCREEN_OFFSET_X-1, symbol * (config.LEVEL_WIDTH * 2 + 4))
    stdscr.addstr(config.LEVEL_SCREEN_OFFSET_Y + config.LEVEL_HEIGHT + 1, config.LEVEL_SCREEN_OFFSET_X-1, symbol * (config.LEVEL_WIDTH * 2 + 4))
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X-1, symbol)
    
    for i in range(config.LEVEL_HEIGHT+1):
        stdscr.addch(config.LEVEL_SCREEN_OFFSET_Y + i, config.LEVEL_SCREEN_OFFSET_X + config.LEVEL_WIDTH * 2 + 2, symbol)

def initial_render():
    render_window_frame()
    render_hud()
    render_level_frame()

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
        
        elif(e.name == "FlagCaptured"):
            play_sound('level_complete')
            load_level(level.num)

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
            render_level_frame('!')
            fire_event("PlayerHurtFlashOver", delay = 0.5)
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
    screen_height, screen_width = stdscr.getmaxyx()

    if(screen_height < 30 or screen_width < 60):
        return 1
    
    pygame.mixer.init()
    load_sounds()

    lasttime = time.time_ns() / (10 ** 9)
    accumulator = 0

    load_level(0)
    initial_render()
    while True:
        newtime = time.time_ns() / (10 ** 9)
        deltatime = newtime - lasttime
        _frametime = deltatime
        _lifetime += deltatime
        accumulator += deltatime
        lasttime = newtime
        handle_input()

        if(accumulator >= config.TARGET_TIME_PER_TICK * 10):
            accumulator = config.TARGET_TIME_PER_TICK
        while (accumulator >= config.TARGET_TIME_PER_TICK):
            tick()
            accumulator -= config.TARGET_TIME_PER_TICK
        render_matrix()
        render_fps()
        if(config.DEBUG): render_debug()
        if _quit:
            break

        if(_frametime < config.TARGET_FRAMETIME): time.sleep(config.TARGET_FRAMETIME)
    
    return 0

retcode = curses.wrapper(main)
if retcode == 0:
    print("You won!")
if retcode == 1:
    print("The console window isn't big enough for the game! Please run the game in a bigger terminal window.")