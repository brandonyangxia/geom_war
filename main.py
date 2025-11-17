import pygame, math, time, random, json, os
from pygame import gfxdraw
from gamble import GachaBanner
from GameExTwoClass import Inventory, Formation, Triangle, Pentagon, Square
from game3 import instantiate, instantiatedummy, World, ShooterBehavior, HealerBehavior, Unit, random_position
SAVE_DIR = "saves"
os.makedirs(SAVE_DIR, exist_ok=True)

SAVE_SLOTS = [os.path.join(SAVE_DIR, f"save{i}.json") for i in range(1, 4)]

def render_multiline(text, x, y, font, color, surface, line_height=4):
    """Render text that may contain '\\n' by splitting lines and blitting them stacked."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y + i * (surf.get_height() + line_height)))


def regular_polygon_points(cx, cy, radius, sides, rotation_deg=0):
    """Return list of points for a regular polygon centered at (cx,cy)."""
    pts = []
    rot = math.radians(rotation_deg)
    for i in range(sides):
        a = 2 * math.pi * i / sides + rot
        px = cx + math.cos(a) * radius
        py = cy + math.sin(a) * radius
        pts.append((px, py))
    return pts


def draw_unit_icon(surface, rect, unit, font):
    """
    Draw small polygon icon and letter rank inside it.
      - rect: pygame.Rect area to draw in
      - unit: UnitData instance (Triangle/Square/Pentagon)
    """
    cx = rect.x + rect.w // 2 - 4 
    cy = rect.y + rect.h // 2 + 2
    radius = min(rect.w, rect.h) * 0.45
    # determine sides
    cls_name = unit.__class__.__name__.lower()
    if "triangle" in cls_name:
        sides = 3
    elif "square" in cls_name:
        sides = 4
    elif "pentagon" in cls_name:
        sides = 5
    else:
        sides = 3
    pts = regular_polygon_points(cx, cy, radius, sides, rotation_deg=-90)
    color = (220, 220, 220)
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, (0,0,0), pts, 2)

    # draw letter rank inside shape
    rank_text = getattr(unit, "letterrank", None) or getattr(unit, "rank", None) or getattr(unit, "grade", None) or ""
    if rank_text is not None:
        # draw small text centered on polygon
        txt = font.render(str(rank_text), True, (0,0,0))
        r = txt.get_rect(center=(cx, cy))
        surface.blit(txt, r)

class RespawnBattleSim:
    def __init__(self, left_bounds, right_bounds, world):
        self.world = world
        self.left_bounds = left_bounds
        self.right_bounds = right_bounds
        self.team0 = []
        self.team1 = []
        # spawn 4 units per side
        for shape in [3,3,4,5]:
            if shape == 3:
                behavior = ShooterBehavior(rate=5)
            elif shape == 4:
                behavior = ShooterBehavior(defensive=True,lifetime=5,proj_speed=150,acceleration=350)
            else:
                behavior = HealerBehavior(rate=7,acceleration=100)
            u = Unit(0, random_position(0,self.team0),shape,behavior=behavior, rotation_speed=30)
            self.team0.append(u)
            self.world.units.append(u)

        for shape in [3,3,4,5]:
            if shape == 3:
                behavior = ShooterBehavior(rate=3)
            elif shape == 4:
                behavior = ShooterBehavior(defensive=True,lifetime=5,proj_speed=150,acceleration=350)
            else:
                behavior = HealerBehavior(rate=7,acceleration=100)
            u = Unit(1, random_position(1,self.team1),shape,behavior=behavior,rotation_speed=30)
            self.team1.append(u)
            self.world.units.append(u)

    def update(self, dt):
        self.world.update(dt)

        # respawn instead of removing
        for u in self.world.units:
            if not u.alive:
                if u.team == 0:
                    r = u.respawn(self.team0)
                    self.team0.remove(u)
                    self.team0.append(r)
                    self.world.units.remove(u)
                    self.world.units.append(r)
                else:
                    r = u.respawn(self.team1)
                    self.team1.remove(u)
                    self.team1.append(r)
                    self.world.units.remove(u)
                    self.world.units.append(r)

    def draw(self, screen):
        self.world.draw(screen)



class CampaignState:
    def __init__(self):
        self.level = 1
        self.enemyuid = []
        self.enemypos = []
        self.enemy_inventory = Inventory()
        self.enemy_formation = Formation('Enemy Team')
        pos = self._random_enemy_position()
        self.enemypos.append(pos)
        self.enemyuid.append(self.enemy_inventory.add_unit(Triangle()))
        self.enemy_formation.place_unit(self.enemyuid[0], pos)

    def advance_level(self):
        self.level += 1
        # Choose: add new enemy OR upgrade one
        if len(self.enemyuid) < 8 and random.random() < 0.2:
            # Add another base unit
            unit_type = random.choice(["triangle", "square", "pentagon"])
            pos = self._random_enemy_position(existing=self.enemypos)
            unit = self._make_enemy(unit_type, 0)
            self.enemy_formation.place_unit(unit, pos)
            self.enemypos.append(pos)
            self.enemyuid.append(unit)
        else:
            # Upgrade random enemy’s stat
            choice = random.choice(self.enemyuid)
            self.enemy_inventory.upgrade(choice)
        
    def _random_enemy_position(self, existing=None):
        """Pick a random valid spot in enemy territory, avoiding overlaps."""
        if existing is None: existing = []
        while True:
            pos = pygame.Vector2(random.randint(500, 750), random.randint(100, 500))
            if all(pos.distance_to(e) > 40 for e in existing):  # No overlapping
                return pos

    def _make_enemy(self, unit_type, level):
        # Creates enemy units at a given base level
        if unit_type == "triangle":
            u = self.enemy_inventory.add_unit(Triangle())
            return u
        elif unit_type == "square":
            u = self.enemy_inventory.add_unit(Square())
            return u
        else:
            u = self.enemy_inventory.add_unit(Pentagon())
            return u

    def reward(self):
        # Level clear reward
        return 50 + (self.level // 10) * 10
    
    def pos_to_tuple(self):
        copypos = list(self.enemypos)
        for index, val in enumerate(copypos):
            copypos[index] = (copypos[index].x, copypos[index].y)
        return copypos
    
    def to_dict(self):
        return {
            "level": self.level,
            "enemy_inventory": self.enemy_inventory.to_dict(),
            "enemy_formation": self.enemy_formation.to_dict(),
            "enemyuid": self.enemyuid,
            "enemypos": self.pos_to_tuple(),
        }
    

    @classmethod
    def from_dict(cls, data):
        obj = cls.__new__(cls)
        obj.level = data.get("level", 1)
        obj.enemy_inventory = Inventory.from_dict(data["enemy_inventory"], 200)
        obj.enemy_formation = Formation.from_dict(data["enemy_formation"])
        obj.enemypos = [pygame.Vector2(*pos) for pos in data["enemypos"]]
        obj.enemyuid = []
        for uid in data["enemyuid"]:
            if uid in obj.enemy_inventory.units:
                obj.enemyuid.append(uid)
    
        return obj
    
# Button helper function
class Button:
    def __init__(self, rect, text, callback, transparent = False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.active = True
        self.transparent = transparent

    def draw(self, surf, font):
        base_color = (200, 200, 200) if self.active else (110, 110, 110)
    
        if self.transparent:
            temp = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            temp.fill((*base_color, 150)) 
            surf.blit(temp, self.rect.topleft)
        else:
            pygame.draw.rect(surf, base_color, self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
    
        # text
        txt = font.render(self.text, True, (0, 0, 0))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if not self.active: return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if callable(self.callback):
                    self.callback()

class SaveMenu:
    def __init__(self, manager):
        self.manager = manager
        self.font = pygame.font.SysFont(None, 30)
        self.slot_buttons = []
        self.delete_buttons = []

        for i, path in enumerate(SAVE_SLOTS):
            y = 100 + i * 80
            slot_rect = (200, y, 300, 60)
            delete_rect = (520, y, 100, 60)

            slot_btn = Button(slot_rect, f"Save Slot {i+1}", lambda p=path: self.choose_slot(p))
            delete_btn = Button(delete_rect, "Delete", lambda p=path: self.delete_save(p))

            self.slot_buttons.append(slot_btn)
            self.delete_buttons.append(delete_btn)

        exit_rect = (200, 400, 420, 60)
        self.exit_btn = Button(exit_rect, "Exit Game", self.exit_game)

    def choose_slot(self, path):
        self.manager.save_path = path
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                self.manager.load_state(data)
            except (json.JSONDecodeError, FileNotFoundError):
                self.start_fresh()
        else:
            self.start_fresh()

        self.manager.switch(MainMenu(self.manager, self.manager.gacha, self.manager.inventory))

    def delete_save(self, path):
        if os.path.exists(path):
            os.remove(path)

        if self.manager.save_path == path:
        # Reset in-memory state to defaults
            self.manager.inventory = Inventory()
            self.manager.formation = Formation()
            self.manager.economy = Economy(300)
            self.manager.campaign = CampaignState()
            self.manager.save_path = None
    
    def start_fresh(self):
        inv = Inventory()
        form = Formation()
        econ = Economy(300)
        self.manager.inventory = inv
        self.manager.formation = form
        self.manager.economy = econ
        self.manager.campaign = CampaignState()
        self.manager.save()

    def exit_game(self):
        pygame.quit()
        raise SystemExit

    def handle_event(self, event):
        for b in self.slot_buttons + self.delete_buttons + [self.exit_btn]:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((30, 30, 30))
        for i, (path, slot_btn, delete_btn) in enumerate(zip(SAVE_SLOTS, self.slot_buttons, self.delete_buttons)):
            if os.path.exists(path):
                # load summary info
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                    gold = data.get("economy", {}).get("gold", 0)
                    inv_count = len(data.get("inventory", []))
                    inv_max = data.get("capacity", 200)
                    lvl = data.get("campaign", {}).get("level", 1)
                    progress = data.get("campaign", {}).get("progress", 0)
                    slot_btn.text = f"Gold: {gold}, Inv: {inv_count}/{inv_max}, Lvl: {lvl}"
                except Exception:
                    slot_btn.text = f"Slot {i+1} (Corrupt)"
                delete_btn.enabled = True
            else:
                slot_btn.text = f"Slot {i+1} (New)"
                delete_btn.enabled = False

            slot_btn.draw(screen, self.font)
            delete_btn.draw(screen, self.font)

        self.exit_btn.draw(screen, self.font)


class Scene:
    def handle_event(self, event): pass
    def update(self, dt): pass
    def draw(self, screen): pass

class SceneManager:
    def __init__(self, start_scene, gacha, inventory, formation, economy):
        self.current = start_scene
        self.gacha=gacha
        self.inventory=inventory
        self.formation=formation
        self.campaign = CampaignState()
        self.economy = economy
        self.save_path = None

    def save_state(self):
        return {
            "campaign": self.campaign.to_dict(),
            "formation": self.formation.to_dict(),
            "inventory": self.inventory.to_dict(),
            "capacity": self.inventory.capacity,
            "economy": self.economy.to_dict()
        }
    
    def save(self):
        if not self.save_path:
            return
        with open(self.save_path, "w") as f:
            json.dump(self.save_state(), f, indent=2)

    def load_state(self, data):
        self.economy = Economy.from_dict(data["economy"])
        self.inventory = Inventory.from_dict(data["inventory"], data["capacity"])
        self.formation = Formation.from_dict(data["formation"])
        self.campaign = CampaignState.from_dict(data["campaign"])

    def switch(self, new_scene):
        self.current = new_scene


class MainMenu(Scene):
    def __init__(self, manager, gacha_system, inventory):
        self.manager = manager
        self.gacha = gacha_system
        self.inventory = inventory
        self.formation = self.manager.formation
        self.campaign = self.manager.campaign
        self.font = pygame.font.SysFont(None, 36)
        self.world = World()

        # buttons
        self.buttons = [
            Button((250, 200, 300, 50), "Draw Banner",
                   lambda: self.manager.switch(BannerScene(self.manager, self.gacha, self.inventory)), transparent=True),
            Button((250, 270, 300, 50), "View Inventory",
                   lambda: self.manager.switch(InventoryScene(self.manager, self.inventory)), transparent=True),
            Button((250, 340, 300, 50), "Edit Formation",
                   lambda: self.manager.switch(FormationScene(self.manager, self.inventory, self.formation)), transparent=True),
            Button((250, 410, 300, 50), "Campaign",
                   lambda: self.manager.switch(CampaignPreviewScene(self.manager, self.formation, self.campaign)), transparent=True),
            Button((250, 480, 300, 50), "Exit to Save Menu",
                   lambda: self.manager.switch(SaveMenu(self.manager)), transparent=True),
        ]

        # background battle
        self.battle = RespawnBattleSim(
            pygame.Rect(50, 100, 400, 500),   # left territory
            pygame.Rect(550, 100, 400, 500),   # right territory
            self.world
        )

    def handle_event(self, event):
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            for b in self.buttons:
                b.handle_event(event)

    def update(self, dt):
        self.battle.update(dt)

    def draw(self, screen):
        screen.fill((0,0,0))
        self.battle.draw(screen)
        for b in self.buttons:
            b.draw(screen, self.font)

        # gold display
        gold_txt = self.font.render(f"Gold: {self.manager.economy.gold}", True, (255,215,0))
        screen.blit(gold_txt, (645, 26))

class BannerScene(Scene):
    def __init__(self, manager, gacha_systems, inventory):
        self.manager = manager
        self.gacha_systems = gacha_systems
        self.inventory = inventory
        self.font = pygame.font.SysFont(None, 50)
        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        y = 150
        for banner_name in self.gacha_systems:
            self.buttons.append(Button(
                rect=(100, y, 300, 60),
                text=f"{banner_name.capitalize()} Banner",
                callback=lambda b=banner_name: self.open_banner_detail(b)
            ))
            y += 90
        self.back_btn = Button((100, 500, 200, 50), "Back", self.go_back)

    def open_banner_detail(self, name):
        self.manager.switch(BannerDetailScene(self.manager, name, self.gacha_systems[name], self.inventory))

    def go_back(self):
        self.manager.switch(MainMenu(self.manager, self.gacha_systems, self.inventory))

    def draw(self, screen):
        screen.fill((30,30,50))
        screen.blit(self.font.render("Select a Banner", True, (255,255,255)), (100, 80))
        for b in self.buttons + [self.back_btn]:
            b.draw(screen, self.font)

    def handle_event(self, event):
        for b in self.buttons + [self.back_btn]:
            b.handle_event(event)

class BannerDetailScene(Scene):
    def __init__(self, manager, name, banner, inventory):
        self.manager = manager
        self.banner_name = name
        self.banner = banner
        self.inventory = inventory
        self.font = pygame.font.SysFont(None, 36)
        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        x, y = 10, 400
        self.buttons = [
            Button((x, y, 180, 50), "Summon", lambda: self.summon("x1")),
            Button((x+200, y, 180, 50), "Summon x10", lambda: self.summon("x10")),
            Button((x+400, y, 180, 50), "Summon x100", lambda: self.summon("x100")),
            Button((x+600, y, 180, 50), "Max Summon", lambda: self.summon(-1)),
        ]
        if not self.can_afford("x100"):
            self.buttons[2].active = False
            self.buttons[2].transparent = True
            if not self.can_afford("x10"):
                self.buttons[1].active = False
                self.buttons[1].transparent = True
                if not self.can_afford("x1"):
                    self.buttons[0].active = False
                    self.buttons[0].transparent = True
                    self.buttons[3].active = False
                    self.buttons[3].transparent = True
                
        self.back_btn = Button((300, 500, 200, 50), "Back", self.go_back)

    def summon(self, n):
        if n == -1:
            if not self.has_space("x1"):
                self.manager.switch(InventoryFullScene(self.manager, self.inventory, self.banner_name, self.banner))
            else:
                self.manager.switch(SummonResultScene(self.manager, self.banner_name, self.banner, self.inventory, mode="max"))
        else:
            if not self.has_space(n):
                self.manager.switch(InventoryFullScene(self.manager, self.inventory, self.banner_name, self.banner))
            else:
                self.manager.switch(SummonResultScene(self.manager, self.banner_name, self.banner, self.inventory, mode=n))

    def can_afford(self, mode):
        cost_map = {"x1": 15, "x10": 150, "x100": 1500}
        cost = cost_map.get(mode, 0)
        return self.manager.economy.gold >= cost
    
    def has_space(self, mode):
        pulls = int(mode[1:])
        return self.inventory.has_space_for(pulls)
    
    def go_back(self):
        self.manager.switch(BannerScene(self.manager, self.manager.gacha, self.inventory))

    def draw(self, screen):
        screen.fill((10,10,30))
        base_unit = self.banner.base_unit()
        stats_text = f"Base Stats for the {self.banner_name.capitalize()}"
        screen.blit(self.font.render(stats_text, True, (255,255,255)), (100, 100))
        y = 160
        for stat_name, stat_value in base_unit.stats().items():
            txt = self.font.render(f"{stat_name}: {stat_value}", True, (255,255,100))
            screen.blit(txt, (100, y))
            y += 40

        for b in self.buttons + [self.back_btn]:
            b.draw(screen, self.font)

    def handle_event(self, event):
        for b in self.buttons + [self.back_btn]:
            b.handle_event(event)

import pygame, random, math

class SummonResultScene(Scene):
    def __init__(self, manager, name, banner, inventory, mode="single"):
        self.manager = manager
        self.name = name
        self.banner = banner
        self.inventory = inventory
        self.mode = mode
        self.phase = "summon"
        self.font = pygame.font.SysFont(None, 40)
        self.result_units = []
        self.result_uids = []
        self.buttons = []
        self.timer = 0
        self.animation_time = 0
        self.unit_pos = pygame.Vector2(400, 300)
        self.blobs = []
        self.absorbed = 0
        self.unit = None
        self.unit_image = None
        self.spawn_timer = 0
        self.stars = []
        self.repel_blobs = False
        self.finished = False
        self.shape_angle = 0
        self.shape_scale = 1.0
        self.shape_rot_speed = 0.0
        self.shape_growth_speed = 0.0
        self.expanding = False
        self.accelfactor = 1
        self.bg_glow = False

        self._do_summon()
        if self.result_units:
            self.unit = max(self.result_units, key=lambda u: u.level)
            self.unit.level_value = self._rank_to_level(self.unit.letterrank)
            self.total_blobs = self.unit.level_value
            self._init_params_for_rank()
            self._init_special_effects()

    def _rank_to_level(self, rank: str):
        """Converts rank string to numeric level value."""
        base_table = {
            "F-": 0, "F": 1, "F+": 2, "E-": 3, "E": 4, "E+": 5,
            "D-": 6, "D": 7, "D+": 8, "C-": 9, "C": 10, "C+": 11,
            "B-": 12, "B": 13, "B+": 14, "A-": 15, "A": 16, "A+": 17,
            "S-": 18, "S": 19, "S+": 20, "SS-": 21, "SS": 22, "SS+": 23,
            "SSS-": 24, "SSS": 25, "SSS+": 26, "U-": 27, "U": 28, "U+": 29,
        }
        base = base_table.get(rank[-2:], 0)
        return base + 30 * rank.count("L")
 
    def _do_summon(self):
        pulls = []
        n = {"single": 1, "x10": 10, "x100": 100, "max": 999999}.get(self.mode, 1)
        for _ in range(n):
            if self.manager.economy.spend(15) and not self.inventory.isfull():
                pulls.append(self.banner.draw_unit())
            else:
                break
        for u in pulls:
            self.result_uids.append(self.inventory.add_unit(u))
        self.result_units = pulls
 
    def _init_params_for_rank(self):
        rank = self.unit.letterrank.upper()
        self.tier = rank.count("L")
        self.spawn_interval = 0.06
        self.pull_strength = 250
        self.burst_force = 500
        self.color_palette = [
            (255, 255, 200),
            (120, 200, 255),
            (255, 160, 240),
            (255, 255, 255)
        ]

    def _init_special_effects(self):
        if self.tier >= 4:
            for _ in range(60):
                x = 400 
                y = 300
                speed = random.uniform(5, 120)
                direction = random.uniform(0,360)
                self.stars.append({"pos": pygame.Vector2(x, y), "speed": speed, "direction": direction})

    def update(self, dt):
        if self.phase == "summon":
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                self._spawn_blob()
            self._update_blobs(dt)
            if self.absorbed >= 120:
                self._update_stars(dt)

            # End condition: animation complete
            if self.repel_blobs and len(self.blobs) == 0:
                if all(b["pos"].x < -5 or b["pos"].x > 805 or b["pos"].y < -5 or b["pos"].y > 605 for b in self.blobs):
                    self.phase = "expand"
                    self.expanding = True
                    self.shape_rot_speed = 0
                    self.shape_growth_speed = 0

        elif self.phase == "expand":
            self._update_expand_phase(dt)

        elif self.phase == "reveal" and self.tier >= 4:
            self._update_stars(dt)

    # Spawn inward moving blobs
    def _spawn_blob(self):
        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            pos = pygame.Vector2(random.randint(0, 800), -20)
        elif side == "bottom":
            pos = pygame.Vector2(random.randint(0, 800), 620)
        elif side == "left":
            pos = pygame.Vector2(-20, random.randint(0, 600))
        else:
            pos = pygame.Vector2(820, random.randint(0, 600))
        color = random.choice(self.color_palette)
        self.blobs.append({
            "pos": pos,
            "vel": pygame.Vector2(0, 0),
            "color": color,
            "absorbed": False,
            "burst": False
        })

    # Blob motion
    def _update_blobs(self, dt):
        for b in list(self.blobs):
            direction = self.unit_pos - b["pos"]
            dist = direction.length()

            # Repel once enough absorbed
            if self.absorbed >= self.total_blobs:
                self.repel_blobs = True

            if not self.repel_blobs:
                # Attract blobs to center
                if not b["absorbed"]:
                    if dist != 0:
                        direction = direction.normalize()
                    b["vel"] += direction * self.pull_strength * dt
                    b["pos"] += b["vel"] * dt
                    if dist < 40:
                        b["absorbed"] = True
                        self.absorbed += 1
            else:
                # Repel blobs away
                if not b["burst"]:
                    b["vel"] = (b["pos"] - self.unit_pos).normalize() * self.burst_force
                    b["burst"] = True
                b["pos"] += b["vel"] * dt
                if (b["pos"].x < -5 or b["pos"].x > 805 or
                    b["pos"].y < -5 or b["pos"].y > 605):
                    self.blobs.remove(b)

    # Background stars 
    def _update_stars(self, dt):
        for s in self.stars:
            radians = math.radians(s["direction"])
            x = math.cos(radians)
            y = math.sin(radians)
            s["pos"].y += s["speed"] * dt * y
            s["pos"].x += s["speed"] * dt * x
            if s["pos"].y > 620 or s["pos"].y < -20 or s["pos"].x > 820 or s["pos"].x < -20:
                s["pos"].y = 300
                s["pos"].x = 400
                s["direction"] = random.uniform(0,360)
                s["speed"] = random.uniform(5,120)

    def _update_expand_phase(self, dt):
        if self.tier >= 4:
            self._update_stars(dt)
        self.accelfactor += 1
        self.shape_rot_speed += 0.2 * dt * self.accelfactor  # acceleration of spin
        self.shape_growth_speed += 3 * dt * self.accelfactor # acceleration of size
        self.shape_angle += self.shape_rot_speed * dt * 120
        self.shape_scale += self.shape_growth_speed * dt * 0.5

        # Reveal
        if self.shape_scale > 22.0:
            self.phase = "reveal"
            self.expanding = False
            self._build_buttons()

    def draw(self, screen):
        # Determine effects from absorbed count
        absorbed = self.absorbed
        blob_glow = absorbed >= 60
        border_glow = absorbed >= 90
        show_stars = absorbed >= 120
        if self.phase == "summon":
            self.bg_glow = absorbed >= 150

        # Background
        if not self.bg_glow:
            self.r = 0
            self.g = 0
            self.b = 0

        if self.bg_glow:
            # Fade background color
            r = max(0, min(255, 200 - self.r))
            g = max(0, min(255, 170 - self.g))
            b = max(0, min(255, self.b))
            screen.fill((r, g, b))

            if self.phase == "reveal":
                self.r += 3.9
                self.g += 3.3
                self.b += 0.3
                if self.r >= 190:
                    self.r = 190 
                    self.bg_glow = False
        else:
            screen.fill((5, 5, 15))

        # Stars
        if show_stars:
            for s in self.stars:
                self.draw_tetragonal_star(screen, s["pos"], 6, (255, 220, 100))

        # Border
        if border_glow:
            pygame.draw.rect(screen, (255, 220, 50), (0, 0, 800, 600), 10)

        # Blobs
        for b in self.blobs:
            if not b["absorbed"]:
                color = (255, 220, 100) if blob_glow else b["color"]
                pygame.draw.circle(screen, color, b["pos"], 5)

        # Center shape
        if self.phase in ("summon", "expand"):
            for b in self.blobs:
                if not b["absorbed"]:
                    color = b["color"]
                    if self.absorbed >= 60:
                        color = (255, 220, 100)
                    pygame.draw.circle(screen, color, b["pos"], 5)
            self._draw_center_shape(screen)
        else:
            self._draw_result(screen)

    def _draw_center_shape(self, screen):
        pos = self.unit_pos
        base_size = 60
        size = base_size * self.shape_scale
        angle_offset = self.shape_angle
        glow_color = (255, 215, 0) if self.absorbed >= 30 else (200, 200, 255)
    
        if self.name == "triangle":
            pts = []
            for i in range(3):
                angle = math.radians(30 + i * 120 + angle_offset)
                pts.append((pos.x + size * math.cos(angle), pos.y + size * math.sin(angle)))
            pygame.draw.polygon(screen, glow_color, pts, width=3)
    
        elif self.name == "square":
            pts = []
            for i in range(4):
                angle = math.radians(45 + i * 90 + angle_offset)
                pts.append((pos.x + size * math.cos(angle), pos.y + size * math.sin(angle)))
            pygame.draw.polygon(screen, glow_color, pts, width=3)
    
        elif self.name == "pentagon":
            pts = []
            for i in range(5):
                angle = math.radians(270 + i * 72 + angle_offset)
                pts.append((pos.x + size * math.cos(angle), pos.y + size * math.sin(angle)))
            pygame.draw.polygon(screen, glow_color, pts, width=3)
    
        else:
            pygame.draw.circle(screen, glow_color, pos, size, width=3)

    def draw_tetragonal_star(self, screen, pos, size, color):
        cx, cy = pos
        points = []
        for i in range(8):
            angle = math.pi / 4 * i
            r = size if i % 2 == 0 else size / 2.5
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        gfxdraw.aapolygon(screen, points, color)
        gfxdraw.filled_polygon(screen, points, color)

    def _draw_result(self, screen):
        u = self.unit
        try:
            self.uid = list(self.manager.inventory.units.keys())[list(self.manager.inventory.units.values()).index(u)]
        except:
            self.uid = self.result_uids[0]
        rank_text = f"{type(u).__name__}  ({u.letterrank})"
        txt = self.font.render(rank_text, True, (255, 255, 100))
        screen.blit(txt, (280, 140))
        y = 200
        for k, v in u.stats().items():
            val = f"{v:.2f}" if isinstance(v, float) else str(v)
            screen.blit(self.font.render(f"{k}: {val}", True, (200, 200, 255)), (280, y))
            y += 30
        for b in self.buttons:
            b.draw(screen, self.font)

    def _build_buttons(self):
        self.buttons = [
            Button((190, 520, 200, 50), "Inspect Unit", self.inspect_unit),
            Button((410, 520, 200, 50), "Done", self.done)
        ]

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def inspect_unit(self):
        self.manager.switch(UnitDetailScene(self.manager, self.inventory, self.uid, self.manager.economy))

    def done(self):
        self.manager.switch(BannerScene(self.manager, self.manager.gacha, self.inventory))


class InventoryFullScene(Scene):
    def __init__(self, manager, inventory, banner_name, banner):
        self.manager = manager
        self.inventory = inventory
        self.name = banner_name
        self.banner = banner
        self.font = pygame.font.SysFont(None, 28)

        self.ok_btn = Button((200, 300, 120, 40), "OK", self.back)
        self.expand_btn = Button((340, 300, 200, 40), "Expand +5 (10g)", self.expand)

    def back(self):
        # return to gacha menu
        self.manager.switch(BannerDetailScene(self.manager, self.name, self.banner, self.inventory))

    def expand(self):
        if self.inventory.capacity >= self.inventory.cap:
            # Already maxed, disable expansion
            self.expand_btn.text = "Max Capacity Reached"
            self.expand_btn.active = False
            return
        if self.inventory.expandcapacity(5, 10, self.manager.economy):
            # successful expansion >> back to gacha
            self.manager.switch(BannerDetailScene(self.manager, self.name, self.banner, self.inventory))
        else:
            # insufficient gold
            self.expand_btn.text = "Not enough gold!"

    def handle_event(self, event):
        self.ok_btn.handle_event(event)
        self.expand_btn.handle_event(event)

    def update(self, dt): pass

    def draw(self, screen):
        screen.fill((40, 40, 60))
        txt = self.font.render("Purchase Failed: Inventory Full", True, (255, 100, 100))
        screen.blit(txt, (150, 200))
        self.ok_btn.draw(screen, self.font)
        self.expand_btn.draw(screen, self.font)

class InventoryScene(Scene):
    BOX_W = 220
    BOX_H = 90
    PADDING = 12
    COLUMNS = 3
    LEFT = 40
    TOP = 80

    SORT_OPTIONS = [None, "level", "hp", "speed", "damage", "rate"]
    FILTER_OPTIONS = [None, "triangle", "square", "pentagon"]

    def __init__(self, manager, inventory):
        self.manager = manager
        self.inventory = inventory
        self.font = pygame.font.SysFont(None, 20)
        self.bigfont = pygame.font.SysFont(None, 26)
        self.goldfont = pygame.font.SysFont(None, 36)
        self.scroll = 0      # number of rows skipped
        self.sort_idx = 0
        self.sort_asc = False
        self.filter_idx = 0
        self.box_map = []    # list of tuples (uid, pygame.Rect)
        self.instructions = "Left-click: inspect. Right-click: mark/unmark for recycle. Wheel/Up/Down to scroll. S/O/F to sort/order/filter. ESC back."

        # recycling state
        self.selected_uids = set()        # right-click toggles membership
        self.recycle_btn = Button((236, 20, 130, 36), "Sell Selected", self.recycle_selected)
        self.auto_btn = Button((380, 20, 260, 36), "Auto Sell", self.start_auto_recycle)

        # auto recycle flow
        self.show_auto_prompt = False
        self.auto_preview_uids = []  # uids that would be removed
        self.auto_preview_gold = 0
        self.auto_cutoff_level = None  # set when selecting a unit as cutoff

    def update(self, dt):
        pass

    def recycle_value(self, unit):
        level = getattr(unit, "level", 0)
        rank_count = level // 30   # each 30 levels = one rank
        return max(1, (level + 1) * (2 ** rank_count))

    def recycle_unit(self, uid):
        # remove single unit and add gold
        if uid not in self.inventory.units: return
        unit = self.inventory.units[uid]
        value = self.recycle_value(unit)
        # give gold
        if hasattr(self.manager, "economy"):
            self.manager.economy.add(value)
        else:
            print("Economy not found on manager; recycle would add", value, "gold")
        # remove
        self.inventory.remove_unit(uid)
        # ensure selection cleaned up
        self.selected_uids.discard(uid)

    def recycle_selected(self):
        if not self.selected_uids:
            return
        total = 0
        for uid in list(self.selected_uids):
            if uid in self.inventory.units:
                total += self.recycle_value(self.inventory.units[uid])
                self.inventory.remove_unit(uid)
        if hasattr(self.manager, "economy"):
            self.manager.economy.add(total)
        self.selected_uids.clear()
        # clear any auto preview state
        self.show_auto_prompt = False
        self.auto_preview_uids = []
        self.auto_preview_gold = 0

    def start_auto_recycle(self):
        # enter prompt mode: user now clicks a unit box to pick cutoff
        self.show_auto_prompt = True
        self.auto_preview_uids = []
        self.auto_preview_gold = 0
        self.auto_cutoff_level = None

    def compute_auto_preview(self, cutoff_level):
        uids = []
        gold = 0
        for uid, unit in self.inventory.units.items():
            if getattr(unit, "level", 0) <= cutoff_level:
                uids.append(uid)
                gold += self.recycle_value(unit)
        self.auto_preview_uids = uids
        self.auto_preview_gold = gold
        self.auto_cutoff_level = cutoff_level

    def confirm_auto_recycle(self):
        if not self.auto_preview_uids:
            self.show_auto_prompt = False
            return
        total = 0
        for uid in list(self.auto_preview_uids):
            if uid in self.inventory.units:
                total += self.recycle_value(self.inventory.units[uid])
                self.inventory.remove_unit(uid)
        if hasattr(self.manager, "economy"):
            self.manager.economy.add(total)
        # clear preview
        self.show_auto_prompt = False
        self.auto_preview_uids = []
        self.auto_preview_gold = 0
        self.auto_cutoff_level = None

    def get_sorted_filtered_items(self):
        items = list(self.inventory.units.items())  # (uid, unit) pairs

        # filter
        fil = InventoryScene.FILTER_OPTIONS[self.filter_idx]
        if fil:
            lower = fil.lower()
            items = [(uid, u) for uid, u in items if lower in u.__class__.__name__.lower()]

        # sort
        key = InventoryScene.SORT_OPTIONS[self.sort_idx]
        if key:
            def keyfn(kv):
                uid, u = kv
                return getattr(u, key, 0)
            items.sort(key=keyfn, reverse=not self.sort_asc)

        return items

    def handle_event(self, event):
        # return to main
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # cancel auto prompt if open
                if self.show_auto_prompt:
                    self.show_auto_prompt = False
                    self.auto_preview_uids = []
                    self.auto_preview_gold = 0
                    self.auto_cutoff_level = None
                    return
                # otherwise go back
                self.manager.switch(MainMenu(self.manager, self.manager.gacha, self.inventory))
                return
            if event.key == pygame.K_DOWN:
                self.scroll += 1
            elif event.key == pygame.K_UP:
                self.scroll = max(0, self.scroll - 1)
            elif event.key == pygame.K_s:
                # cycle sort options
                self.sort_idx = (self.sort_idx + 1) % len(InventoryScene.SORT_OPTIONS)
            elif event.key == pygame.K_o:
                self.sort_asc = not self.sort_asc
            elif event.key == pygame.K_f:
                self.filter_idx = (self.filter_idx + 1) % len(InventoryScene.FILTER_OPTIONS)

        # mouse wheel + clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # left click -> inspect / in auto prompt choose cutoff or confirm
            if event.button == 1:
                # if auto prompt showing: choose unit to set threshold (preview)
                if self.show_auto_prompt:
                    for uid, rect in self.box_map:
                        if rect.collidepoint(mx, my):
                            # compute preview using chosen unit's level
                            unit = self.inventory.units.get(uid)
                            if not unit: continue
                            cutoff = getattr(unit, "level", 0)
                            # if same cutoff clicked twice, confirm
                            if self.auto_cutoff_level is None or cutoff != self.auto_cutoff_level:
                                self.compute_auto_preview(cutoff)
                            else:
                                # confirm recycle
                                self.confirm_auto_recycle()
                            return

                # normal left-click -> open detail view
                for uid, rect in self.box_map:
                    if rect.collidepoint(mx, my):
                        # open detail view
                        self.manager.switch(UnitDetailScene(self.manager, self.inventory, uid, self.manager.economy))
                        return

            # right-click -> toggle selection for recycle
            elif event.button == 3:
                for uid, rect in self.box_map:
                    if rect.collidepoint(mx, my):
                        if uid in self.selected_uids:
                            self.selected_uids.remove(uid)
                        else:
                            self.selected_uids.add(uid)
                        # when selecting at least one, the recycle button becomes active
                        return

            elif event.button == 4:  # wheel up
                self.scroll = max(0, self.scroll - 1)
            elif event.button == 5:  # wheel down
                self.scroll += 1

        # let buttons handle events too
        self.recycle_btn.handle_event(event)
        self.auto_btn.handle_event(event)

    def draw(self, screen):
        screen.fill((40, 40, 60))
        title = self.bigfont.render(f"Inventory ({len(self.inventory.units)}/{self.inventory.capacity})", True, (255,255,255))
        screen.blit(title, (20, 16))

        # show current sort/filter info
        sort_label = InventoryScene.SORT_OPTIONS[self.sort_idx] or "none"
        filt_label = InventoryScene.FILTER_OPTIONS[self.filter_idx] or "all"
        info_txt = f"Sort: {sort_label} ({'asc' if self.sort_asc else 'desc'})  |  Filter: {filt_label}"
        screen.blit(self.font.render(info_txt, True, (200,200,200)), (20, 46))
        screen.blit(self.goldfont.render(f"Gold: {self.manager.economy.gold}", True, (255,215,0)), (645,26))

        # top buttons
        # update recycle button text and enabled state
        if self.selected_uids:
            total = sum(self.recycle_value(self.inventory.units[uid]) for uid in self.selected_uids if uid in self.inventory.units)
            self.recycle_btn.text = f"Sell Selected (+{total}g)"
            self.recycle_btn.active = True
        else:
            self.recycle_btn.text = "Sell Selected"
            self.recycle_btn.active = False

        # auto button text
        if self.auto_preview_gold > 0 and self.auto_cutoff_level is not None:
            rankcutoff = GachaBanner._grade_from_level(self,self.auto_cutoff_level)
            self.auto_btn.text = f"Auto Sell {rankcutoff} Rank and Lower: (+{self.auto_preview_gold}g)"
        else:
            self.auto_btn.text = "Auto Sell"

        # draw buttons
        self.recycle_btn.draw(screen, self.font)
        self.auto_btn.draw(screen, self.font)

        items = self.get_sorted_filtered_items()

        # compute grid layout and which to render
        cols = InventoryScene.COLUMNS
        box_w, box_h, pad = self.BOX_W, self.BOX_H, self.PADDING
        left, top = self.LEFT, self.TOP

        # how many rows fit on screen
        rows_visible = max(1, (screen.get_height() - top) // (box_h + pad))
        max_rows = max(0, math.ceil(len(items) / cols) - rows_visible)
        self.scroll = min(self.scroll, max_rows)

        self.box_map = []
        # draw boxes
        for idx, (uid, unit) in enumerate(items):
            row = idx // cols
            col = idx % cols
            y = top + (row - self.scroll) * (box_h + pad)
            x = left + col * (box_w + pad)
            rect = pygame.Rect(x, y, box_w, box_h)

            # only draw if visible region
            if rect.bottom < 70 or rect.top > screen.get_height() - 20:
                continue

            # background and border
            pygame.draw.rect(screen, (70, 70, 90), rect)
            border_col = (120, 120, 140)
            # highlighted if selected for recycle
            if uid in self.selected_uids:
                border_col = (0,200,0)
            # highlighted red if included in auto preview
            if self.show_auto_prompt and uid in self.auto_preview_uids:
                border_col = (200,80,80)
            pygame.draw.rect(screen, border_col, rect, 2)

            # icon area
            icon_rect = pygame.Rect(rect.x + 8, rect.y + 8, 84, rect.h - 16)
            draw_unit_icon(screen, icon_rect, unit, self.font)

            # text area
            name_text = f"{unit.__class__.__name__}"
            screen.blit(self.font.render(name_text, True, (255,255,255)), (rect.x + 100, rect.y + 10))

            # small stats lines (HP, rank)
            rank_display = getattr(unit, "level", None) or getattr(unit, "rank", None) or getattr(unit,"grade", "")
            stat_display = ""
            sort_label = InventoryScene.SORT_OPTIONS[self.sort_idx] or "none"
            if sort_label != "level" and sort_label != "none":
                stat_display = getattr(unit, sort_label, "")
                try:
                    screen.blit(self.font.render(f"{float(stat_display):.2f}", True, (200,200,200)), (rect.x + 100, rect.y + 56))
                except Exception:
                    screen.blit(self.font.render(str(stat_display), True, (200,200,200)), (rect.x + 100, rect.y + 56))
            screen.blit(self.font.render(f"Level: {rank_display}", True, (200,200,0)), (rect.x + 100, rect.y + 34))

            # grey-out overlay if locked (keeps original behaviour)
            if getattr(self.inventory, "units", {}) and self.inventory.units.get(uid) and getattr(self.inventory.units[uid], "locked", False):
                s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                s.fill((20,20,20,140))
                screen.blit(s, rect.topleft)

            # remember rect for clicks
            self.box_map.append((uid, rect))

        # instructions at bottom
        render_multiline(self.instructions, 20, screen.get_height() - 20, self.font, (180,180,180), screen)

        # show auto-recycle preview popup if active
        if self.show_auto_prompt:
            popup = pygame.Rect(120, 140, 560, 70)
            pygame.draw.rect(screen, (30,30,30), popup)
            pygame.draw.rect(screen, (200,200,200), popup, 2)
            tip = "Auto Sell: Click a unit to set cutoff rank. Click same unit again to confirm recycling."
            screen.blit(self.font.render(tip, True, (255,255,0)), (popup.x + 8, popup.y + 8))
            preview_txt = f"Preview: {len(self.auto_preview_uids)} units --> +{self.auto_preview_gold}g"
            screen.blit(self.font.render(preview_txt, True, (200,200,200)), (popup.x + 8, popup.y + 40))


class UnitDetailScene(Scene):
    PREVIEW_RECT = pygame.Rect(40, 80, 360, 420)  # left half preview
    def __init__(self, manager, inventory, uid, economy):
        self.manager = manager
        self.inventory = inventory
        self.uid = uid
        self.font = pygame.font.SysFont(None, 20)
        self.bigfont = pygame.font.SysFont(None, 28)
        self.goldfont = pygame.font.SysFont(None, 36)
        self.unit_data = inventory.units[uid]
        self.economy = economy

        # Sell button
        self.recycle_btn = Button(
            rect=(self.PREVIEW_RECT.right + 30, 400, 180, 40),
            text=f"Sell ({self.recycle_value()}g)",
            callback=self.recycle_unit
        )

        # prepare a small preview world
        self.world = World()
        preview_center = pygame.Vector2(self.PREVIEW_RECT.center)
        cls_name = self.unit_data.__class__.__name__.lower()
        sides = 3 if "triangle" in cls_name else (4 if "square" in cls_name else 5)

        if "triangle" in cls_name:
            behavior = ShooterBehavior(
                getattr(self.unit_data,"damage",5),
                getattr(self.unit_data,"rate",1.0),
                False, 0.0,
                getattr(self.unit_data,"speed",100),
                getattr(self.unit_data,"acceleration",200)
            )
        elif "square" in cls_name:
            behavior = ShooterBehavior(
                0,
                getattr(self.unit_data,"rate",1.0),
                True,
                getattr(self.unit_data,"lifetime",3.0),
                getattr(self.unit_data,"speed",120),
                getattr(self.unit_data,"acceleration",150)
            )
        else:
            behavior = HealerBehavior(
                getattr(self.unit_data,"heal",8),
                getattr(self.unit_data,"rate",0.5),
                getattr(self.unit_data,"speed",100),
                getattr(self.unit_data,"acceleration",200)
            )

        preview_unit = Unit(0, preview_center, sides=sides,
                            behavior=behavior,
                            hp=getattr(self.unit_data,"hp",100),
                            rotation_speed=40)
        self.world.units.append(preview_unit)

        class IdleBehavior:  # dummy
            def update(self, u, dt, world): pass

        if "triangle" in cls_name:
            dummy = Unit(1, pygame.Vector2(preview_center.x+140, preview_center.y),
                         sides=3, behavior=IdleBehavior(), hp=100, rotation_speed=30)
            self.world.units.append(dummy)
        elif "square" in cls_name:
            dummy = Unit(1, pygame.Vector2(preview_center.x+140, preview_center.y),
                         sides=3, behavior=ShooterBehavior(atk=1), hp=100, rotation_speed=30)
            self.world.units.append(dummy)
        else:  # healer
            friendly = Unit(0, pygame.Vector2(preview_center.x+140, preview_center.y),
                            sides=3, behavior=IdleBehavior(), hp=10, rotation_speed=30)
            self.world.units.append(friendly)

    def recycle_value(self):
        level = getattr(self.unit_data, "level", 0)
        rank_count = level // 30
        return max(1, (level + 1) * (2 ** rank_count))

    def recycle_unit(self):
        gold = self.recycle_value()
        self.economy.add(gold)
        # Remove the unit from inventory
        if self.uid in self.inventory.units:
            del self.inventory.units[self.uid]
        # Return to inventory screen
        self.manager.switch(InventoryScene(self.manager, self.inventory))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch(InventoryScene(self.manager, self.inventory))

        self.recycle_btn.handle_event(event)

    def update(self, dt):
        self.world.update(dt)

    def draw(self, screen):
        screen.fill((30, 30, 40))
        pygame.draw.rect(screen, (50,50,70), self.PREVIEW_RECT)
        self.world.draw(screen)

        right_x = self.PREVIEW_RECT.right + 30
        screen.blit(self.goldfont.render(f"Gold: {self.economy.gold}", True, (255,215,0)), (645,26))
        screen.blit(self.bigfont.render(
            f"{self.unit_data.__class__.__name__} - Rank {self.unit_data.letterrank}",
            True, (255,255,255)), (right_x, 100))

        lines = []
        if hasattr(self.unit_data, "lvlVec"):
            lvlVec = self.unit_data.lvlVec
        else:
            lvlVec = None

        # pick stats by unit type
        cls_name = self.unit_data.__class__.__name__.lower()
        if "triangle" in cls_name:
            lines = [
                f"HP: {getattr(self.unit_data,'hp',100)} ({lvlVec[0] if lvlVec else 0})",
                f"Damage: {getattr(self.unit_data,'damage',5)} ({lvlVec[1] if lvlVec else 0})",
                f"Speed: {getattr(self.unit_data,'speed',100)} ({lvlVec[2] if lvlVec else 0})",
                f"Acceleration: {getattr(self.unit_data,'acceleration',100)} ({lvlVec[3] if lvlVec else 0})",
                f"Rate: {getattr(self.unit_data,'rate',1.0):.2f} ({lvlVec[4] if lvlVec else 0})",
            ]
        elif "square" in cls_name:
            lines = [
                f"HP: {getattr(self.unit_data,'hp',100)} ({lvlVec[0] if lvlVec else 0})",
                f"Speed: {getattr(self.unit_data,'speed',120)} ({lvlVec[1] if lvlVec else 0})",
                f"Acceleration: {getattr(self.unit_data,'acceleration',150)} ({lvlVec[2] if lvlVec else 0})",
                f"Rate: {getattr(self.unit_data,'rate',1.0):.2f} ({lvlVec[3] if lvlVec else 0})",
                f"Lifetime: {getattr(self.unit_data,'lifetime',3.0)} ({lvlVec[4] if lvlVec else 0})",
            ]
        else:  
            lines = [
                f"HP: {getattr(self.unit_data,'hp',100)} ({lvlVec[0] if lvlVec else 0})",
                f"Heal: {getattr(self.unit_data,'heal',8)} ({lvlVec[1] if lvlVec else 0})",
                f"Speed: {getattr(self.unit_data,'speed',100)} ({lvlVec[2] if lvlVec else 0})",
                f"Acceleration: {getattr(self.unit_data,'acceleration',200)} (n/a)",
                f"Rate: {getattr(self.unit_data,'rate',1.0):.2f} ({lvlVec[3] if lvlVec else 0})",
            ]

        y = 150
        for ln in lines:
            screen.blit(self.font.render(ln, True, (230,230,230)), (right_x, y))
            y += 28
        # Draw recycle button
        self.recycle_btn.draw(screen, self.font)

        # Bottom instruction
        screen.blit(self.font.render("ESC: back", True, (180,180,180)), (right_x, 360))


class FormationScene(Scene):
    MAP_RECT = pygame.Rect(20, 20, 360, 560)   # left area - player half style
    INV_LEFT = 420
    INV_TOP = 40
    INV_W = 360
    INV_BOX_H = 76
    INV_BOX_W = 320

    MIN_UNIT_DIST = 55  # no overlap (center to center)

    def __init__(self, manager, inventory, formation):
        self.manager = manager
        self.inventory = inventory
        self.formation = formation

        self.font = pygame.font.SysFont(None, 20)
        self.bigfont = pygame.font.SysFont(None, 26)

        # placed units: uid >> pygame.Vector2(x,y)
        # Initialize from formation.slots if it already has pixel positions
        self.placed = {}
        for uid, pos in self.formation.slots.items():
            # pos stored previously might be (x,y) pixel coords; if not adapt here
            self.placed[uid] = pygame.Vector2(pos)

        # inventory lock state (True if placed or being dragged)
        self.inventory_locked = {uid: (uid in self.placed) for uid in self.inventory.units.keys()}

        # Drag state
        self.dragging = None  # (uid, offset Vector2, from_inventory:bool)
        self.mouse_pos = pygame.Vector2(0,0)

        # inventory UI
        self.scroll = 0
        self.sort_idx = 0
        self.sort_asc = False
        self.filter_idx = 0

        self.warning = ""   # shown if cannot exit (overlap)
        self.warning_time = 0

    # ---------- helper utilities ----------
    def get_sorted_filtered_items(self):
        items = list(self.inventory.units.items())

        fil = InventoryScene.FILTER_OPTIONS[self.filter_idx]
        if fil:
            lower = fil.lower()
            items = [(uid, u) for uid, u in items if lower in u.__class__.__name__.lower()]

        # sort
        key = InventoryScene.SORT_OPTIONS[self.sort_idx] or None
        if key:
            def keyfn(kv):
                uid, u = kv
                v = getattr(u, key, 0)
                try:
                    return float(v)
                except Exception:
                    return 0
            items.sort(key=keyfn, reverse=not self.sort_asc)

        return items

    def world_pos_inside_map(self, pos):
        return self.MAP_RECT.collidepoint(pos.x, pos.y)
    

    def sync_with_inventory(self):
        # Remove any placed UIDs that no longer exist in inventory.units.
        # Keeps self.placed, self.inventory_locked, and formation.slots consistent.
        if not hasattr(self.inventory, "units"):
            return

        removed = [uid for uid in list(self.placed.keys()) if uid not in self.inventory.units]
        if not removed:
            return

        for uid in removed:
            # remove from placed and any locked state
            self.placed.pop(uid, None)
            self.inventory_locked.pop(uid, None)

        # reflect this change back into formation.slots (store pixel coords)
        self.formation.slots = {uid: (int(pos.x), int(pos.y)) for uid, pos in self.placed.items()}

        # give brief feedback
        self.warning = f"Removed {len(removed)} missing unit(s) from formation."
        self.warning_time = time.time()

    def unit_count(self):
        return sum(1 for uid in self.placed.keys() if uid in getattr(self.inventory, "units", {}))



    def is_overlap(self, pos, ignore_uid=None):
        for uid, p in self.placed.items():
            if uid == ignore_uid:
                continue
            if uid not in getattr(self.inventory, "units", {}):
                continue
            if p.distance_to(pos) < FormationScene.MIN_UNIT_DIST:
                return True
        return False

    def pick_placed_uid_at(self, pos):
        # iterate reversed so the most recently-placed get priority
        for uid, p in reversed(list(self.placed.items())):
            if uid not in getattr(self.inventory, "units", {}):
                continue
            if p.distance_to(pos) < FormationScene.MIN_UNIT_DIST/1.2:
                return uid
        return None

    def handle_event(self, event):
        self.sync_with_inventory()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # prevent exit if overlapping
                if self.any_overlaps():
                    self.warning = "Cannot exit: some units overlap!"
                    self.warning_time = time.time()
                else:
                    # save placed units back into formation.slots (pixel coords)
                    self.formation.slots = {uid: (int(pos.x), int(pos.y)) for uid,pos in self.placed.items()}
                    self.manager.switch(MainMenu(self.manager, self.manager.gacha, self.inventory))
                return
            elif event.key == pygame.K_DOWN:
                self.scroll += 1
            elif event.key == pygame.K_UP:
                self.scroll = max(0, self.scroll-1)
            elif event.key == pygame.K_s:
                self.sort_idx = (self.sort_idx + 1) % len(InventoryScene.SORT_OPTIONS)
            elif event.key == pygame.K_o:
                self.sort_asc = not self.sort_asc
            elif event.key == pygame.K_f:
                self.filter_idx = (self.filter_idx + 1) % len(InventoryScene.FILTER_OPTIONS)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx,my = event.pos
            mpos = pygame.Vector2(mx,my)
            self.mouse_pos = mpos

            if event.button == 1:
                # check inventory boxes first
                for idx, (uid, rect) in enumerate(self.get_inventory_box_rects()):
                    if rect.collidepoint(mx,my):
                        if self.inventory_locked.get(uid, False):
                            # box is locked -> not interactable
                            return
                        # start dragging from inventory: compute offset from mouse to icon center
                        self.dragging = (uid, pygame.Vector2(0,0), True)
                        # lock the inventory box for this uid (grayed out)
                        self.inventory_locked[uid] = True
                        return

                # check if user clicked a placed unit: pick it up
                if self.MAP_RECT.collidepoint(mx,my):
                    uid = self.pick_placed_uid_at(mpos)
                    if uid:
                        self.dragging = (uid, pygame.Vector2(0,0), False)
                        self.placed.pop(uid, None)
                        # keep inventory_locked True while dragging
                        self.inventory_locked[uid] = True
                        return

            # right click
            elif event.button == 3:
                # cancel current drag
                if self.dragging:
                    uid, offset, from_inv = self.dragging
                    # if dragging from inventory and canceled -> unlock box
                    if from_inv:
                        self.inventory_locked[uid] = False
                    else:
                        # was placed originally - return to original area center (optional)
                        # place back at mouse pos if valid
                        self.placed[uid] = mpos.clamp(self.MAP_RECT.topleft, self.MAP_RECT.bottomright)
                        self.inventory_locked[uid] = True
                    self.dragging = None

        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = pygame.Vector2(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:
                uid, offset, from_inv = self.dragging
                drop_pos = pygame.Vector2(event.pos) + offset
                # if dropped inside map, test overlap
                if self.world_pos_inside_map(drop_pos):
                    if self.unit_count() >= 8 and uid not in self.placed:
                        self.warning = "Unit cap reached!"
                        self.warning_time = time.time()
                        if from_inv:
                            self.inventory_locked[uid] = False
                        self.dragging = None
                        return
                    # ensure keep inside bounds with margin
                    margin = 16
                    x = max(self.MAP_RECT.left + margin, min(drop_pos.x, self.MAP_RECT.right - margin))
                    y = max(self.MAP_RECT.top + margin, min(drop_pos.y, self.MAP_RECT.bottom - margin))
                    pos = pygame.Vector2(x,y)

                    # check non-overlap
                    if not self.is_overlap(pos, ignore_uid=uid):
                        # place it
                        self.placed[uid] = pos
                        self.inventory_locked[uid] = True
                        # update formation.slots immediately (optional)
                        self.formation.place_unit(uid, (int(pos.x), int(pos.y)))
                    else:
                        # cannot place because overlap: cancel placement and unlock if from inventory
                        self.warning = "Overlap! Choose another spot."
                        self.warning_time = time.time()
                        if from_inv:
                            self.inventory_locked[uid] = False
                        else:
                            # put back to a reasonable non-overlapping fallback: try to find nearest free spot
                            placed_ok = False
                            for r in range(20, 300, 10):
                                for a in range(0,360,30):
                                    candidate = pygame.Vector2(pos.x + r*math.cos(math.radians(a)),
                                                              pos.y + r*math.sin(math.radians(a)))
                                    if self.MAP_RECT.collidepoint(candidate) and not self.is_overlap(candidate, ignore_uid=uid):
                                        self.placed[uid] = candidate
                                        placed_ok = True
                                        break
                                if placed_ok: break
                            if not placed_ok:
                                # give back to inventory (unlock)
                                self.inventory_locked[uid] = False
                    self.dragging = None
                    return

                # dropped outside map & not in bin -> cancel
                if from_inv:
                    # return to inventory: unlock
                    self.inventory_locked[uid] = False
                else:
                    # previously placed: put back at last known spot if we removed earlier, else unlock
                    # simple behavior: return to inventory if dropped outside
                    self.inventory_locked[uid] = False
                self.dragging = None

        # mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            if event.y < 0:
                self.scroll += 1
            elif event.y > 0:
                self.scroll = max(0, self.scroll - 1)

    def get_inventory_box_rects(self):
        """Compute visible inventory box rects after sort/filter and scroll. Returns list of (uid, rect)."""
        items = self.get_sorted_filtered_items()
        box_rects = []
        x = self.INV_LEFT + 10
        y = self.INV_TOP + 10
        for i, (uid, unit) in enumerate(items):
            y_i = y + (i - self.scroll) * (self.INV_BOX_H + 8)
            rect = pygame.Rect(x, y_i, self.INV_BOX_W, self.INV_BOX_H)
            if rect.bottom > 550: 
                continue
            if rect.top < self.INV_TOP + 10: 
                continue
            
            box_rects.append((uid, rect))
        return box_rects

    def any_overlaps(self):
        uids = list(self.placed.keys())
        for i in range(len(uids)):
            for j in range(i+1, len(uids)):
                if self.placed[uids[i]].distance_to(self.placed[uids[j]]) < FormationScene.MIN_UNIT_DIST:
                    return True
        return False

    def draw(self, screen):
        self.sync_with_inventory()
        screen.fill((26,26,30))
        max_reached = self.unit_count() >= 8
        pygame.draw.rect(screen, (40,40,60), self.MAP_RECT)
        pygame.draw.rect(screen, (80,80,100), self.MAP_RECT, 2)
        screen.blit(self.bigfont.render("Placement Map", True, (220,220,220)), (self.MAP_RECT.left + 6, self.MAP_RECT.top + 6))

        # draw placed units
        for uid, pos in self.placed.items():
            unit = self.inventory.units.get(uid)
            if not unit: continue
            # draw shape icon at pos
            icon_rect = pygame.Rect(pos.x-18, pos.y-18, 55, 55)
            draw_unit_icon(screen, icon_rect, unit, self.font)
            # small center dot
            pygame.draw.circle(screen, (0,0,0), (int(pos.x), int(pos.y)), 1)

        # draw dragging ghost on top (if any)
        if self.dragging:
            uid, offset, from_inv = self.dragging
            # ghost position
            ghost_pos = self.mouse_pos + offset
            # ghost color: semi-transparent rectangle or icon
            unit = self.inventory.units.get(uid)
            if unit:
                # draw semi-transparent icon
                ghost_rect = pygame.Rect(ghost_pos.x-18, ghost_pos.y-18, 55, 55)
                s = pygame.Surface((ghost_rect.w, ghost_rect.h), pygame.SRCALPHA)
                s.fill((255,255,255,0))
                draw_unit_icon(s, pygame.Rect(0,0,ghost_rect.w, ghost_rect.h), unit, self.font)
                s.set_alpha(180)
                screen.blit(s, ghost_rect.topleft)
                # show overlap hint
                valid = self.world_pos_inside_map(ghost_pos) and not self.is_overlap(ghost_pos, ignore_uid=uid)
                color = (0,200,0) if valid else (200,0,0)
                pygame.draw.circle(screen, color, (int(ghost_pos.x), int(ghost_pos.y)), 6, 2)

        # draw inventory panel header
        title = self.font.render("Inventory (drag into map)", True, (255,255,255))
        screen.blit(title, (self.INV_LEFT, 2))
        
        # Filter + Sort info
        sort_label = InventoryScene.SORT_OPTIONS[self.sort_idx] or "None"
        filter_label = InventoryScene.FILTER_OPTIONS[self.filter_idx] or "None"
        header = self.font.render(
            f"Sort: {sort_label}{' Asc' if self.sort_asc else ' Desc'} | Filter: {filter_label}",
            True, (200,200,200)
        )
        screen.blit(header, (self.INV_LEFT, 20))

        # draw inventory boxes
        self.box_map = []
        for uid, rect in self.get_inventory_box_rects():
            unit = self.inventory.units.get(uid)
            if not unit: continue
            # box bg
            locked = self.inventory_locked.get(uid, False) or (max_reached and uid not in self.placed)
            bg = (70,70,80) if not locked else (50,50,60)
            pygame.draw.rect(screen, bg, rect)
            pygame.draw.rect(screen, (110,110,120), rect, 2)

            # icon rect
            icon_rect = pygame.Rect(rect.x + 6, rect.y + 6, 64, rect.h - 12)
            draw_unit_icon(screen, icon_rect, unit, self.font)

            # text
            if unit.__class__.__name__ == "Triangle":
                stats_text = f"HP: {unit.hp}     ATK: {unit.damage}     RLD: {unit.rate:.2f}\nSPD: {unit.speed}     ACC: {unit.acceleration}"
            elif unit.__class__.__name__ == "Square":
                stats_text = f"HP: {unit.hp}     DUR: {unit.lifetime}     RLD: {unit.rate:.2f}\nSPD: {unit.speed}     ACC: {unit.acceleration}"
            else:
                stats_text = f"HP: {unit.hp}     HL: {unit.heal}     RLD: {unit.rate:.2f}\nSPD: {unit.speed}     ACC: {unit.acceleration}"
            render_multiline(stats_text, rect.x + 80, rect.y + 20, self.font, (230,230,230), screen)

            # show filtered stat if filter active
            fil = InventoryScene.FILTER_OPTIONS[self.filter_idx]
            stat_label = ""
            if fil:
                if fil == "triangle" or fil == "square" or fil == "pentagon":
                    # if filtering by type, show rank instead
                    stat_label = getattr(unit, "letterrank", getattr(unit,"rank", getattr(unit,"grade","")))
                else:
                    stat_val = getattr(unit, fil, None)
                    if stat_val is not None:
                        # format numeric
                        try:
                            stat_label = f"{float(stat_val):.2f}"
                        except Exception:
                            stat_label = str(stat_val)
            if stat_label:
                screen.blit(self.font.render(stat_label, True, (200,200,160)), (rect.x + 80, rect.y + 34))

            # grey-out overlay if locked
            if self.inventory_locked.get(uid, False):
                s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                s.fill((20,20,20,140))
                screen.blit(s, rect.topleft)

            self.box_map.append((uid, rect))

        # warning text (temporary)
        if self.warning and time.time() - self.warning_time < 2.5:
            wsurf = self.bigfont.render(self.warning, True, (220,60,60))
            screen.blit(wsurf, (self.MAP_RECT.left + 6, self.MAP_RECT.bottom))

        # bottom instructions
        instr = "Click+drag a unit into the map. Right-click to cancel drag. ESC to return (blocked if overlaps)."
        screen.blit(self.font.render(instr, True, (180,180,180)), (20, self.MAP_RECT.bottom + 36))
        count_txt = self.bigfont.render(f"Units: {self.unit_count()}/8", True, (255,255,180))
        screen.blit(count_txt, (self.INV_LEFT, 560))

class CampaignPreviewScene(Scene):
    def __init__(self, manager, formation, campaign):
        self.manager = manager
        self.inventory = self.manager.inventory
        self.formation = formation
        self.campaign = campaign
        self.font = pygame.font.SysFont(None, 24)

        # Make preview world
        self.world = World()
        # Add player units (already arranged formation)
        instantiatedummy(self.formation, 0, self.inventory, self.world)
        # Add campaign enemies
        instantiatedummy(campaign.enemy_formation, 1, campaign.enemy_inventory, self.world)

        # Buttons
        self.buttons = [
            Button((50, 500, 200, 40), "Change Formation", self.change_formation),
            Button((300, 500, 200, 40), "Begin Battle", self.begin_battle),
            Button((550, 500, 200, 40), "Main Menu", self.back_to_menu)
        ]

    def change_formation(self):
        self.manager.switch(FormationScene(self.manager, self.inventory, self.formation))

    def begin_battle(self):
        self.manager.switch(BattleScene(self.manager, self.campaign, self.formation))

    def back_to_menu(self):
        self.manager.switch(MainMenu(self.manager, self.manager.gacha, self.inventory))

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt):
        self.world.update(dt)

    def draw(self, screen):
        screen.fill((20,20,30))
        self.world.draw(screen)

        y = 30
        screen.blit(self.font.render(f"Campaign Level {self.campaign.level}", True, (255,255,0)), (30, y))
        for uid, slot in self.campaign.enemy_formation.slots.items():
            unit = self.campaign.enemy_inventory.units[uid]
            txt = unit.info()
            render_multiline(txt, slot.x - 85, slot.y-5, pygame.font.SysFont(None, 12), (200,200,200), screen)
        for btn in self.buttons:
            btn.draw(screen, self.font)


class BattleScene(Scene):
    def __init__(self, manager, campaign, formation):
        self.world = World()
        self.manager = manager
        self.campaign = campaign
        self.formation = formation
        self.finished = False
        self.result = None
        self.txt = None
        self.reward_txt = None
        self.buttons = []

        # Player team
        self.player_units = instantiate(
            self.formation, team=0,
            inventory=self.manager.inventory,
            wrld=self.world
        )

        # Enemy team    
        self.enemy_units = instantiate(
            self.campaign.enemy_formation, team=1,
            inventory=self.campaign.enemy_inventory,
            wrld=self.world
        )
        self.units = self.player_units + self.enemy_units

    def back_to_menu(self):
        self.manager.switch(
            MainMenu(self.manager, self.manager.gacha, self.manager.inventory)
        )

    def next_level(self):
        self.manager.switch(
            CampaignPreviewScene(self.manager, self.formation, self.campaign)
        )

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt):
        if not self.finished:
            self.world.update(dt)

            # Check end condition
            alive_player = [u for u in self.player_units if u.hp > 0]
            alive_enemy = [u for u in self.enemy_units if u.hp > 0]

            if not alive_player and not alive_enemy:
                self.finish_battle("tie")
            elif not alive_enemy:
                self.finish_battle("win")
            elif not alive_player:
                self.finish_battle("lose")

    def finish_battle(self, result):
        self.finished = True
        self.result = result
        font = pygame.font.SysFont(None, 72)

        if result == "win":
            self.buttons = [
                Button((425, 500, 200, 40), "Next Level", self.next_level),
                Button((175, 500, 200, 40), "Main Menu", self.back_to_menu),
            ]
            self.txt = font.render("You Won!", True, (0, 255, 0))
            reward = self.campaign.reward()
            self.manager.economy.add(reward)
            self.reward_txt = pygame.font.SysFont(None, 44).render(
                f"+ {reward}g", True, (255, 215, 0)
            )
            self.campaign.advance_level()

        elif result == "lose":
            self.buttons = [
                Button((175, 500, 200, 40), "Main Menu", self.back_to_menu),
                Button((425, 500, 200, 40), "Try Again", self.next_level),
            ]
            self.txt = font.render("You Lost...", True, (255, 0, 0))
            self.reward_txt = None

        else:  # tie
            self.buttons = [
                Button((175, 500, 200, 40), "Main Menu", self.back_to_menu),
                Button((425, 500, 200, 40), "Try Again", self.next_level),
            ]
            self.txt = font.render("Tie", True, (255, 255, 0))
            self.reward_txt = None

    def draw(self, screen):
        screen.fill((0, 0, 0))
        self.world.draw(screen)

        if self.finished:
            if self.txt:
                screen.blit(self.txt, (280, 200))
            if self.reward_txt:
                screen.blit(self.reward_txt, (350, 300))

            font_small = pygame.font.SysFont(None, 24)
            for btn in self.buttons:
                btn.draw(screen, font_small)

class Economy:
    def __init__(self, gold=0):
        self.gold = gold

    def add(self, amount):
        self.gold += amount

    def spend(self, amount):
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def to_dict(self):
        return {"gold": self.gold}

    @classmethod
    def from_dict(cls, data):
        return cls(gold=data["gold"])


def main():
    pygame.init()
    screen = pygame.display.set_mode((800,600))
    clock = pygame.time.Clock()

    gacha_systems = {
        "triangle": GachaBanner(Triangle,5),
        "square": GachaBanner(Square,5),
        "pentagon": GachaBanner(Pentagon,4),
    }

    manager = SceneManager(None, gacha_systems, Inventory(), Formation(), Economy(300))
    manager.current = SaveMenu(manager)  # start at save menu

    running = True
    while running:
        dt = clock.tick(60)/1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            manager.current.handle_event(event)

        manager.current.update(dt)
        manager.current.draw(screen)
        pygame.display.flip()

        # Auto-save after each frame (cheap since JSON small)
        manager.save()

    pygame.quit()

if __name__ == "__main__":
    main()
