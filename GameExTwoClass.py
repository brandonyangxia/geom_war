import math, uuid, json, random


def gfroml(level):
    grades = ["F-","F","F+","E-","E","E+","D-","D","D+","C-","C","C+","B-","B","B+","A-","A","A+","S-","S","S+","SS-","SS","SS+","SSS-","SSS","SSS+","U-","U","U+"]
    if level < len(grades):
        base = grades[level]
    else:
        # Extend infinitely: after U, use L-prefixed sequence
        n = level - len(grades)
        base = "L"*(n//30 + 1) + grades[n % len(grades)]
    return base

class UnitData:
    def __init__(self, hp=100, level=0, letterrank = 'F-'):
        self.hp = hp
        self.level = level
        self.letterrank = letterrank

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "level": self.level,
            "letterrank": self.letterrank,
            "lvlVec": self.lvlVec,
            "hp": self.hp
        }
    
    @classmethod
    def from_dict(cls, data):
        unit_type = data["type"]
    
        if unit_type == "Triangle":
            unit = Triangle(level=data["level"], letterrank=data["letterrank"], lvlVec=data["lvlVec"])
        elif unit_type == "Square":
            unit = Square(level=data["level"], letterrank=data["letterrank"], lvlVec=data["lvlVec"])
        elif unit_type == "Pentagon":
            unit = Pentagon(level=data["level"], letterrank=data["letterrank"], lvlVec=data["lvlVec"])
        else:
            raise ValueError(f"Unknown unit type {unit_type}")
        if "hp" in data:
            unit.hp = data["hp"]
    
        return unit


class Triangle(UnitData):
    def __init__(self, damage=5, speed=100, acceleration=100, rate=3.0, lvlVec=None, level=0, letterrank = 'F-'):
        super().__init__(level=level, letterrank=letterrank)
        if lvlVec is None: lvlVec = [0,0,0,0,0]
        self.level = level
        self.lvlVec = lvlVec
        self.damage = damage + lvlVec[1]
        self.speed = speed + 5*lvlVec[2]
        self.acceleration = acceleration + 10*lvlVec[3]
        self.rate = rate * (0.9**lvlVec[4])
        self.hp += 10*lvlVec[0]
    
    def upgrade(self):
        choice = random.choice(['dmg', 'spd', 'acc', 'rate', 'hp'])
        if choice == 'dmg':
            self.damage += 1
            self.lvlVec[1] += 1
        elif choice == 'spd':
            self.speed += 5
            self.lvlVec[2] += 1
        elif choice == 'acc':
            self.acceleration += 10
            self.lvlVec[3] += 1
        elif choice == 'rate':
            self.rate *= 0.9
            self.lvlVec[4] += 1
        else:
            self.hp += 10
        self.level += 1
        self.letterrank = gfroml(self.level)

    def info(self):
        profile = f"Rank:{self.letterrank} {self.__class__.__name__} \nHP:{self.hp}  ATK:{self.damage}\nSPD:{self.speed}  ACC:{self.acceleration}  RLD:{(self.rate):.2f}"
        return profile
    
    def stats(self):
        return {
            "HP": self.hp,
            "ATK": self.damage,
            "SPD": self.speed,
            "ACC": self.acceleration,
            "RLD": self.rate
        }

class Square(UnitData):
    def __init__(self, speed=160, acceleration=200, rate=5.0, lifetime=5.0, lvlVec=None, level=0, letterrank = 'F-'):
        super().__init__(level=level, letterrank=letterrank)
        if lvlVec is None: lvlVec = [0,0,0,0,0]
        self.level = level
        self.lvlVec = lvlVec
        self.damage = 0
        self.speed = speed + 5*lvlVec[1]
        self.acceleration = acceleration + 50*lvlVec[2]
        self.rate = rate * (0.9**lvlVec[3])
        self.lifetime = lifetime + 0.5*lvlVec[4]
        self.hp += 10*lvlVec[0]
    
    def upgrade(self):
        choice = random.choice(['life', 'spd', 'acc', 'rate', 'hp'])
        if choice == 'life':
            self.lifetime += 0.5
            self.lvlVec[4] += 1
        elif choice == 'spd':
            self.speed += 5
            self.lvlVec[1] += 1
        elif choice == 'acc':
            self.acceleration += 50
            self.lvlVec[2] += 1
        elif choice == 'rate':
            self.rate *= 0.9
            self.lvlVec[4] += 1
        else:
            self.hp += 10
        self.level += 1
        self.letterrank = gfroml(self.level)

    def info(self):
        profile = f"{self.letterrank} {self.__class__.__name__} \nHP:{self.hp}  DUR:{self.lifetime}\nSPD:{self.speed}  ACC:{self.acceleration}  RLD:{(self.rate):.2f}"
        return profile
    
    def stats(self):
        return {
            "HP": self.hp,
            "DUR": self.lifetime,
            "SPD": self.speed,
            "ACC": self.acceleration,
            "RLD": self.rate
        }


class Pentagon(UnitData):
    def __init__(self, heal=20, speed=100, acceleration=300, rate=7.5, lvlVec=None, level=0, letterrank = 'F-'):
        super().__init__(level=level, letterrank=letterrank)
        if lvlVec is None: lvlVec = [0,0,0,0]
        self.level = level
        self.lvlVec = lvlVec
        self.heal = heal + 2*lvlVec[1]
        self.speed = speed + 10*lvlVec[2]
        self.acceleration = acceleration
        self.rate = rate * (0.9**lvlVec[3])
        self.hp += 10*lvlVec[0]

    def upgrade(self):
        choice = random.choice(['heal', 'spd', 'rate', 'hp'])
        if choice == 'heal':
            self.heal += 2
            self.lvlVec[1] += 1
        elif choice == 'spd':
            self.speed += 10
            self.lvlVec[2] += 1
        elif choice == 'rate':
            self.rate *= 0.9
            self.lvlVec[3] += 1
        else:
            self.hp += 10
        self.level += 1
        self.letterrank = gfroml(self.level)

    def info(self):
        profile = f"Rank:{self.letterrank} {self.__class__.__name__} \nHP:{self.hp}  HL:{self.heal}\nSPD:{self.speed}  ACC:{self.acceleration}  RLD:{(self.rate):.2f}"
        return profile
    
    def stats(self):
        return {
            "HP": self.hp,
            "HL": self.heal,
            "SPD": self.speed,
            "ACC": self.acceleration,
            "RLD": self.rate
        }


class Inventory:
    def __init__(self, capacity = 200):
        self.units = {}  # {unit_id: unit instance}
        self.capacity = capacity
        self.cap = 600
    
    def isfull(self):
        return len(self.units) >= self.capacity
    
    def has_space_for(self, pulls):
        return len(self.units) + pulls <= self.capacity

    def add_unit(self, unit):
        if self.isfull():
            return
        unit_id = str(uuid.uuid4())
        self.units[unit_id] = unit
        return unit_id

    def upgrade(self, uid):
        self.units[uid].upgrade()
    
    def expandcapacity(self, amount = 5, gold = 10, economy = None):
        if economy is None:
            return False
        if not economy.spend(gold):
            return False
        if self.capacity >= self.cap:
            return False
        self.capacity = min(self.capacity + amount, self.cap)
        return True

    def to_dict(self):
        return {uid: unit.to_dict() for uid, unit in self.units.items()}

    @classmethod
    def from_dict(cls, data, capacity):
        inv = cls(capacity=capacity)
        for uid, unit_data in data.items():
            inv.units[uid] = UnitData.from_dict(unit_data)
        return inv

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
    def remove_unit(self, unit_id):
        if unit_id in self.units:
            return self.units.pop(unit_id)
        return None

    def list_units(self):
        return {uid: unit.__dict__ for uid, unit in self.units.items()}


import pygame, json

class Formation:
    def __init__(self, name='Team'):
        self.name = name
        self.slots = {}  # {uid: Vector2}

    def place_unit(self, unit_id, pos):
        self.slots[unit_id] = pos

    def slots_to_dict(self):
        slotcopy = {}
        for uid, pos in self.slots.items():
            slotcopy[uid] = (pos.x, pos.y) if isinstance(pos, pygame.Vector2) else tuple(pos)
        return slotcopy

    def to_dict(self):
        return {"name": self.name, "slots": self.slots_to_dict()}

    @classmethod
    def from_dict(cls, data):
        f = cls(data["name"])
        f.slots = {uid: pygame.Vector2(*pos) for uid, pos in data["slots"].items()}
        return f

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def remove_unit(self, unit_id):
        if unit_id in self.slots:
            self.slots.pop(unit_id)

    def validate(self, inventory):
        """Remove slots pointing to units no longer in the inventory."""
        self.slots = {uid: pos for uid, pos in self.slots.items() if uid in inventory.units}

    def list_slots(self):
        return self.slots


    

