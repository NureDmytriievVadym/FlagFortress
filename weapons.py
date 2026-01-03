from models import *
import random

class BaseWeapon:
    name = "BaseWeapon"
    shorthand = "W"

    def __init__(self):
        self.name = "BaseWeapon"
        self.shorthand = "W"
        self.damage = 1
        self.ammo = 5
        self.mag_size = 5
        self.ammo_reserve = 5
        self.firerate = 1
        self.spread = 0 # degrees
        self.reload_time = 1
        self.sounds = {
            "shoot": ["shoot"],
            "reload": ["reload"]
        }
        # not configurable
        self.reloading = False
        self.reloading_time_left = 0
        self.shooting_time_left = 0
    
    def reload(self):
        if self.reloading: return
        self.reloading = True
        self.reloading_time_left = self.reload_time
    
    def finish_reload(self):
        ammo_to_load = self.mag_size - self.ammo
        if self.ammo_reserve != 1 and self.ammo_reserve < ammo_to_load: ammo_to_load = self.ammo_reserve
        self.ammo += ammo_to_load
        self.ammo_reserve -= ammo_to_load
        self.reloading = False

    def shoot(self, level: GameLevel, shooter: Entity) -> bool:
        if self.ammo != -1 and self.ammo <= 0: return False
        if self.ammo != -1: self.ammo -= 1
        self.shooting_time_left = 1.0 / self.firerate
        return True

    def serialize(self) -> dict:
        data = {}
        data["damage"] = self.damage
        data["name"] = self.name
        data["ammo"] = self.ammo
        data["mag_size"] = self.mag_size
        data["ammo_reserve"] = self.ammo_reserve
        data["firerate"] = self.firerate
        data["spread"] = self.spread
        data["reload_time"] = self.reload_time
        data["sounds"] = self.sounds.copy()
        return data

    @staticmethod
    def deserialize(data: dict) -> "BaseWeapon":
        obj = BaseWeapon()
        obj.damage = data["damage"]
        obj.ammo = data["ammo"]
        obj.mag_size = data["mag_size"]
        obj.ammo_reserve = data["ammo_reserve"]
        obj.firerate = data["firerate"]
        obj.spread = data["spread"]
        obj.reload_time = data["reload_time"] 
        obj.sounds = data["sounds"]
        return obj

class Pistol(BaseWeapon):
    name = "Pistol"
    shorthand = "P"

    def __init__(self):
        BaseWeapon.__init__(self)
        self.name = "Pistol"
        self.shorthand = "P"
        self.damage = 4
        self.ammo = 5
        self.mag_size = 5
        self.ammo_reserve = 5
        self.reload_time = 1
        self.spread = 0
        self.firerate = 2
        self.sounds = {
            "shoot": ["weapons/chaingun/f1b", "weapons/chaingun/f2b", "weapons/chaingun/f3b", "weapons/chaingun/f4b"],
            "reload": ["reload"]
        }
    
    def reload(self): super().reload()
    def finish_reload(self): super().finish_reload()

    def shoot(self, level: GameLevel, shooter: Entity) -> bool:
        if self.ammo != -1 and self.ammo <= 0: return False
        if self.ammo != -1: self.ammo -= 1
        spread = math.radians(random.random() * self.spread - self.spread/2)
        direction = Vector2F(math.sin(spread) * shooter.direction.x + math.cos(spread) * shooter.direction.y,
                            math.cos(spread) * shooter.direction.x - math.sin(spread) * shooter.direction.y)
        bullet = Bullet(shooter.pos.copy(), direction, shooter)
        bullet.damage = self.damage
        level.add_object(bullet)
        self.shooting_time_left = 1.0 / self.firerate
        return True
    
    def serialize(self) -> dict:
        return super().serialize()

    @staticmethod
    def deserialize(data: dict) -> "Pistol":
        return BaseWeapon.deserialize(data)

class Shotgun(BaseWeapon):
    name = "Shotgun"
    shorthand = "SH"

    def __init__(self):
        BaseWeapon.__init__(self)
        self.name = "Shotgun"
        self.shorthand = "SH"
        self.damage = 2
        self.ammo = 2
        self.mag_size = 2
        self.ammo_reserve = 4
        self.firerate = 1
        self.reload_time = 1
        self.spread = 90
        self.sounds = {
            "shoot": ["weapons/shotgun/sshotf1b"],
            "reload": ["reload"]
        }
    
    def reload(self): super().reload()
    def finish_reload(self): super().finish_reload()

    def shoot(self, level: GameLevel, shooter: Entity) -> bool:
        if self.ammo != -1 and self.ammo <= 0: return False
        if self.ammo != -1: self.ammo -= 1
        bullet_count = math.floor(random.random() * 2 + 5)
        spread = math.radians(self.spread)
        spread_per_bullet = spread / bullet_count
        for i in range(bullet_count):
            angle = (i + 0.5) * spread_per_bullet - spread / 2
            angle = angle + random.random() * spread_per_bullet - spread_per_bullet / 2
            bullet = Bullet(shooter.pos.copy(), shooter.direction.rotate(angle), shooter)
            bullet.speed = random.random() * 10 + 15
            bullet.damage = self.damage
            level.add_object(bullet)
        self.shooting_time_left = 1.0 / self.firerate
        return True
    
    def serialize(self) -> dict:
        return super().serialize()

    @staticmethod
    def deserialize(data: dict) -> "Shotgun":
        return BaseWeapon.deserialize(data)

class EnemyShotgun(Shotgun):
    name = "EnemyShotgun"
    shorthand = "Sh"

    def __init__(self):
        Shotgun.__init__(self)
        self.name = 'EnemyShotgun'
        self.shorthand = 'Sh'
        self.damage = 2
        self.sounds["shoot"] = ["cg1"]
    
    def shoot(self, level: GameLevel, shooter: Entity) -> bool:
        if self.ammo != -1 and self.ammo <= 0: return False
        if self.ammo != -1: self.ammo -= 1
        bullet_count = math.floor(random.random() * 2 + 3)
        spread = math.radians(self.spread)
        spread_per_bullet = spread / bullet_count
        for i in range(bullet_count):
            angle = (i + 0.5) * spread_per_bullet - spread / 2
            angle = angle + random.random() * spread_per_bullet - spread_per_bullet / 2
            bullet = Bullet(shooter.pos.copy(), shooter.direction.rotate(angle), shooter)
            bullet.speed = random.random() * 8 + 10
            bullet.damage = self.damage
            level.add_object(bullet)
        self.shooting_time_left = 1.0 / self.firerate
        return True
    
    def serialize(self) -> dict:
        return super().serialize()

    @staticmethod
    def deserialize(data: dict) -> "EnemyShotgun":
        return Shotgun.deserialize(data)

class Railgun(BaseWeapon):
    name = "Railgun"
    shorthand = "RG"

    def __init__(self):
        BaseWeapon.__init__(self)
        self.name = "Railgun"
        self.shorthand = "RG"
        self.damage = 5
        self.ammo = 1
        self.mag_size = 1
        self.ammo_reserve = 4
        self.firerate = 0.5
        self.reload_time = 2
        self.spread = 0
        self.sounds = {
            "shoot": ["weapons/railgun/railgf1a"],
            "reload": []
        }
    
    def reload(self): super().reload()
    def finish_reload(self): super().finish_reload()

    def shoot(self, level: GameLevel, shooter: Entity) -> bool:
        if self.ammo != -1 and self.ammo <= 0: return False
        if self.ammo != -1: self.ammo -= 1
        bullet_count = 30
        for i in range(bullet_count):
            bullet = Bullet(shooter.pos.copy(), shooter.direction, shooter)
            bullet.speed = 20 + i * 20
            bullet.lifetime = 0.1
            bullet.pierce = -1
            bullet.damage = self.damage if i == bullet_count-1 else 0 # only one bullet is real
            level.add_object(bullet)
        self.shooting_time_left = 1.0 / self.firerate
        self.reload()
        return True
    
    def serialize(self) -> dict:
        return super().serialize()

    @staticmethod
    def deserialize(data: dict) -> "Railgun":
        return BaseWeapon.deserialize(data)

class SentryGun(BaseWeapon):
    name = "SentryGun"
    shorthand = "Se"

    def __init__(self):
        BaseWeapon.__init__(self)
        self.name = "SentryGun"
        self.shorthand = "Se"
        self.ammo = -1
        self.mag_size = 1
        self.ammo_reserve = -1
        self.reload_time = 0
        self.spread = 20
        self.firerate = 1
        self.sounds = {
            "shoot": ["shoot"],
            "reload": []
        }
    
    def reload(self): super().reload()
    def finish_reload(self): super().finish_reload()

    def shoot(self, level: GameLevel, shooter: Entity) -> bool:
        if self.ammo != -1 and self.ammo <= 0: return False
        if self.ammo != -1: self.ammo -= 1
        spread = math.radians(random.random() * self.spread - self.spread/2)
        direction = Vector2F(math.sin(spread) * shooter.direction.x + math.cos(spread) * shooter.direction.y,
                            math.cos(spread) * shooter.direction.x - math.sin(spread) * shooter.direction.y)
        bullet = Bullet(shooter.pos.copy(), direction, shooter)
        bullet.speed = 10
        level.add_object(bullet)
        self.shooting_time_left = 1.0 / self.firerate
        return True
    
    def serialize(self) -> dict:
        return super().serialize()

    @staticmethod
    def deserialize(data: dict) -> "SentryGun":
        return BaseWeapon.deserialize(data)

class WeaponManager:
    WEAPONS = [
        BaseWeapon,
        Pistol,
        Shotgun,
        EnemyShotgun,
        Railgun,
        SentryGun
    ]

    @staticmethod
    def CreateWeapon(**kwargs) -> BaseWeapon:
        if not kwargs.get("id") is None: return WeaponManager.WEAPONS[kwargs.get("id")]()
        elif not kwargs.get("name") is None: 
            for wep_type in WeaponManager.WEAPONS:
                if(wep_type.name == kwargs.get("name")): return wep_type()
        else: return BaseWeapon()