import pygame, random, math, GameExTwoClass
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

TEAM_COLORS = [(200,50,50),(50,50,200)]
HEAL_BORDER = (255,255,255)
DMG_BORDER = (0,0,0)
UNIT_PADDING = 50
MIN_UNIT_DIST = 60

def regular_polygon(radius, sides):
    return [(math.cos(2*math.pi*i/sides)*radius, math.sin(2*math.pi*i/sides)*radius)
            for i in range(sides)]

def random_position(team, existing_units):
    max_attempts = 100
    for _ in range(max_attempts):
        if team==0: x = random.randint(UNIT_PADDING, WIDTH//2-UNIT_PADDING)
        else: x = random.randint(WIDTH//2+UNIT_PADDING, WIDTH-UNIT_PADDING)
        y = random.randint(UNIT_PADDING, HEIGHT-UNIT_PADDING)
        pos = pygame.Vector2(x,y)
        if all(pos.distance_to(u.pos)>MIN_UNIT_DIST for u in existing_units):
            return pos
    return pos

def instantiate(formation, team, inventory, wrld):
        # Turns UnitData objects into objects ready for battle
        formation.validate(inventory)
        world=wrld
        units = []
        for uid, pos in formation.slots.items():
            unit_data = inventory.units[uid]

            if isinstance(unit_data, GameExTwoClass.Triangle):
                u = Unit(team, pygame.Vector2(*pos),sides=3, behavior=ShooterBehavior(unit_data.damage, unit_data.rate, False, 0.0, unit_data.speed, unit_data.acceleration), hp=unit_data.hp, rotation_speed=30)
                world.units.append(u)
            elif isinstance(unit_data, GameExTwoClass.Square):
                u = Unit(team, pygame.Vector2(*pos),sides=4, behavior=ShooterBehavior(0, unit_data.rate, True, unit_data.lifetime, unit_data.speed, unit_data.acceleration), hp=unit_data.hp, rotation_speed=30)
                world.units.append(u)
            elif isinstance(unit_data, GameExTwoClass.Pentagon):
                u = Unit(team, pygame.Vector2(*pos),sides=5, behavior=HealerBehavior(unit_data.heal, unit_data.rate, unit_data.speed, unit_data.acceleration), hp=unit_data.hp, rotation_speed=30)
                world.units.append(u)
            units.append(u)

        return units

def instantiatedummy(formation, team, inventory, wrld):
        # Turns UnitData objects into dummies that do not shoot
        formation.validate(inventory)
        world=wrld
        units = []
        for uid, pos in formation.slots.items():
            unit_data = inventory.units[uid]

            if isinstance(unit_data, GameExTwoClass.Triangle):
                u = Unit(team, pygame.Vector2(*pos),sides=3, behavior=None, hp=unit_data.hp, rotation_speed=30)
                world.units.append(u)
            elif isinstance(unit_data, GameExTwoClass.Square):
                u = Unit(team, pygame.Vector2(*pos),sides=4, behavior=None, hp=unit_data.hp, rotation_speed=30)
                world.units.append(u)
            elif isinstance(unit_data, GameExTwoClass.Pentagon):
                u = Unit(team, pygame.Vector2(*pos),sides=5, behavior=None, hp=unit_data.hp, rotation_speed=30)
                world.units.append(u)
            units.append(u)

        return units


class Unit:
    def __init__(self, team, pos, sides, behavior, hp=100, rotation_speed=30):
        self.team = team
        self.color = TEAM_COLORS[team]
        self.pos = pygame.Vector2(pos)
        self.sides = sides
        self.shape = regular_polygon(20, sides)
        self.behavior = behavior
        self.hp = hp
        self.alive = True
        self.rotation = 0
        self.rotation_speed = rotation_speed
        self.next_corner_idx = 0
        self.vel = pygame.Vector2(0,0)
        if hp<100:
            self.max_hp = 100
        else:
            self.max_hp = self.hp

    def update(self, dt, world):
        if not self.alive: return
        self.rotation = (self.rotation+self.rotation_speed*dt)%360
        if self.behavior != None:
            self.behavior.update(self, dt, world)
        self.pos += self.vel*dt
        # Bounce off walls
        if self.pos.x<0: self.pos.x=0; self.vel.x*=-1
        if self.pos.x>WIDTH: self.pos.x=WIDTH; self.vel.x*=-1
        if self.pos.y<0: self.pos.y=0; self.vel.y*=-1
        if self.pos.y>HEIGHT: self.pos.y=HEIGHT; self.vel.y*=-1
    
    def respawn(self, existing_units):
        position = random_position(self.team, existing_units)
        u = Unit(self.team, position, self.sides, self.behavior, self.max_hp, self.rotation_speed)
        return u

    def get_corners(self):
        rad = math.radians(self.rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        return [(self.pos.x + x*cos_r - y*sin_r, self.pos.y + x*sin_r + y*cos_r) for x,y in self.shape]

    def get_next_corner(self):
        corners = self.get_corners()
        corner = pygame.Vector2(corners[self.next_corner_idx])
        self.next_corner_idx = (self.next_corner_idx+1)%len(corners)
        return corner
    
    def draw_hp_bar(screen, pos, hp, max_hp):
        base_length = 50
        length = int(base_length * (hp / 100))
        height = 6

        x = pos[0] - length // 2
        y = pos[1] + 40 

        pygame.draw.rect(screen, (100, 0, 0), (x, y, base_length, height)) 
        pygame.draw.rect(screen, (0, 200, 0), (x, y, length, height))


    def draw(self, surf):
        if not self.alive:
            return

        # draw the unit shape
        pygame.draw.polygon(surf, self.color, self.get_corners())

        # draw HP bar
        self.draw_hp_bar(surf)

    def draw_hp_bar(self, surf):
        max_length_per_100 = 30  # default bar length, height
        bar_h = 4
    
        base_length = int(max_length_per_100 * (self.max_hp / 100))
        filled_length = int(base_length * (self.hp / self.max_hp))
    
        cx, cy = self.pos
        # place bar under the unit center
        x = cx - base_length // 2
        y = cy + 5
    
        pygame.draw.rect(surf, (100, 0, 0), (x, y, base_length, bar_h))
        pygame.draw.rect(surf, (0, 200, 0), (x, y, filled_length, bar_h))
        pygame.draw.rect(surf, (0, 0, 0), (x, y, base_length, bar_h), 1)



class Projectile:
    def __init__(self, team, pos, damage=10, speed=100, acceleration = 200,
                 healing=False, defensive=False, lifetime=3.0, source_type='triangle'):
        self.team = team
        self.color = TEAM_COLORS[team]
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.max_speed = speed
        self.acceleration = acceleration
        self.healing = healing
        self.defensive = defensive
        if self.defensive:
            self.lifetime=lifetime
        self.source_type = source_type
        self.alive = True
        self.shape = [(0,-8),(-4,8),(4,8)]
        self.vel = pygame.Vector2(0,0)
        self.angle=0
        self.init_vel=speed
        self.initialized=False
        self.iframes=0.5

    def reflect_ip(self, normal):
        self.vel = self.vel - 2*self.vel.dot(normal)*normal

    def update(self, dt, world):
        if not self.alive: return
        if self.iframes >= 0:
            self.iframes -= dt

        # For square projectiles only
        if self.defensive:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.alive = False
                return
            enemy_projs=[p for p in world.projectiles if p.team!=self.team and p.alive]
            priority=['triangle','pentagon','square']
            target=None
            for kind in priority:
                kind_projs=[p for p in enemy_projs if p.source_type==kind]
                if kind_projs: target=min(kind_projs,key=lambda e:e.pos.distance_to(self.pos)); break
            if not self.initialized:
                self.vel=pygame.Vector2(0,-1)*self.init_vel
                self.initialized=True
            self.pos+=self.vel*dt

            if target:
                # Distance to target and time to reach it (rough estimate)
                dist = self.pos.distance_to(target.pos)
                if self.max_speed > 0:
                    prediction_time = dist / self.max_speed
                else:
                    prediction_time = 0

                # Predicted future position of target
                predicted_pos = target.pos + target.vel * prediction_time

                # Steer toward predicted position
                direction = (predicted_pos - self.pos)
                if direction.length_squared() > 0:  # avoid zero vector
                    direction = direction.normalize()
                    self.vel = self.vel.lerp(direction * self.max_speed, 0.2 * dt)

                # Clamp speed
                if self.vel.length() > self.max_speed:
                    self.vel.scale_to_length(self.max_speed)

            # Annihilate enemy projectiles on contact
            for p in enemy_projs:
                if self.pos.distance_to(p.pos)<12:
                    if p.defensive:
                        self.alive = False
                        p.alive = False
                        return
                    p.alive=False
            # Bounce off walls
            if self.pos.x<0 or self.pos.x>WIDTH: self.vel.x*=-1; self.pos.x=max(0,min(WIDTH,self.pos.x))
            if self.pos.y<0 or self.pos.y>HEIGHT: self.vel.y*=-1; self.pos.y=max(0,min(HEIGHT,self.pos.y))
            # Bounce off all units
            for u in world.units:
                if not u.alive: continue
                offset=self.pos-u.pos
                dist=offset.length()
                radius=20
                if dist<radius:
                    self.reflect_ip(offset.normalize())
                    self.pos+=offset.normalize()*(radius-dist)
            return

        # Other projectiles
        if self.source_type=='triangle':
            enemies=[u for u in world.units if u.team!=self.team and u.alive]
            if enemies: self.target=min(enemies,key=lambda e:e.pos.distance_to(self.pos))
        elif self.source_type=='pentagon':
            allies=[u for u in world.units if u.team==self.team and u.alive and u.hp<u.max_hp]
            self.target=min(allies,key=lambda a:(a.hp/a.max_hp)) if allies else None
            if not self.target: self.alive=False; return

        if not hasattr(self,'target') or not self.target or not self.target.alive:
            self.alive=False; return

        to_target=(self.target.pos-self.pos).normalize()

        # Bounce off units they cannot hit
        for u in world.units:
            if not u.alive: continue
            offset=self.pos-u.pos
            dist=offset.length()
            radius=20
            can_hit=False
            if self.healing and u.team==self.team: can_hit=True
            elif not self.healing and u.team!=self.team: can_hit=True
            elif self.defensive: can_hit=False
            # Triangle projectiles
            if self.source_type=='triangle' and u.team!=self.team and dist<radius:
                u.hp-=self.damage
                if u.hp<=0: u.alive=False
                self.alive=False
            # Pentagon projectiles
            elif not can_hit and dist<radius:
                self.reflect_ip(offset.normalize())
                self.pos+=offset.normalize()*(radius-dist)
            # Pentagon projectile heals and dies on friendly units
            elif self.healing and u.team==self.team and dist<radius:
                if self.iframes <= 0:
                    u.hp=min(u.max_hp,u.hp+self.damage)
                    self.alive=False

        # Avoid friendly units for triangle projectiles
        avoid=pygame.Vector2(0,0)
        if self.source_type=='triangle':
            for u in world.units:
                if u.team==self.team and u.alive:
                    offset=self.pos-u.pos
                    dist=offset.length()
                    if dist<30: avoid+=offset.normalize()*(30-dist)/30

        direction=(to_target+avoid).normalize()

        # Initial velocity
        if not self.initialized:
            self.vel=direction*self.init_vel
            self.initialized=True

        # Accelerate and move with turning limit
        max_turn = math.radians(1800) * dt

        # Only apply if current velocity is nonzero
        if self.vel.length() > 0.01:
            current_dir = self.vel.normalize()
            dot = max(-1, min(1, current_dir.x*direction.x + current_dir.y*direction.y))
            angle_diff = math.acos(dot)
            # Determine rotation direction
            cross = current_dir.x*direction.y - current_dir.y*direction.x
            if cross < 0:
                angle_diff *= -1
            # Clamp angle_diff to max_turn
            angle_diff = max(-max_turn, min(max_turn, angle_diff))
            cos_r, sin_r = math.cos(angle_diff), math.sin(angle_diff)
            new_dir = pygame.Vector2(
                current_dir.x*cos_r - current_dir.y*sin_r,
                current_dir.x*sin_r + current_dir.y*cos_r
            )
        else:
            new_dir = direction

        # Accelerate along the limited direction
        self.vel += new_dir * self.acceleration * dt
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)
        self.pos += self.vel * dt
        self.angle = math.degrees(math.atan2(new_dir.y, new_dir.x)) + 90


        # Projectile-projectile collisions
        for other in world.projectiles:
            if other is self or not other.alive: continue
            offset=self.pos-other.pos
            dist=offset.length()
            min_dist=8
            if dist<min_dist:
                # Square destroys enemy projectiles
                if self.defensive and other.team!=self.team: other.alive=False; continue
                if other.defensive and self.team!=other.team: self.alive=False; continue
                normal=offset.normalize()
                self.reflect_ip(normal)
                other.reflect_ip(-normal)
                overlap=min_dist-dist
                self.pos+=normal*(overlap/2)
                other.pos-=normal*(overlap/2)

        # Bounce off walls
        if self.pos.x<0 or self.pos.x>WIDTH: self.vel.x*=-1; self.pos.x=max(0,min(WIDTH,self.pos.x))
        if self.pos.y<0 or self.pos.y>HEIGHT: self.vel.y*=-1; self.pos.y=max(0,min(HEIGHT,self.pos.y))

    def draw(self,surf):
        if not self.alive: return
        if self.defensive:
            pygame.draw.circle(surf,self.color,(int(self.pos.x),int(self.pos.y)),5)
            pygame.draw.circle(surf,DMG_BORDER,(int(self.pos.x),int(self.pos.y)),5,1)
        else:
            rotated=[]
            rad=math.radians(self.angle)
            cos_r,sin_r=math.cos(rad),math.sin(rad)
            for x,y in self.shape:
                rx=x*cos_r - y*sin_r
                ry=x*sin_r + y*cos_r
                rotated.append((self.pos.x+rx,self.pos.y+ry))
            border_color=HEAL_BORDER if self.healing else DMG_BORDER
            pygame.draw.polygon(surf,self.color,rotated)
            pygame.draw.polygon(surf,border_color,rotated,2)

# For determining unit behaviors
class ShooterBehavior:
    def __init__(self, atk=10, rate=1.0, defensive=False, lifetime = 3.0, proj_speed=100, acceleration = 200):
        self.atk=atk
        self.rate=rate
        self.cooldown=0
        self.defensive=defensive
        self.lifetime=lifetime
        self.proj_speed=proj_speed
        self.acceleration=acceleration
    def update(self, unit, dt, world):
        self.cooldown-=dt
        if self.cooldown>0: return
        spawn_pos=unit.get_next_corner()
        proj=Projectile(unit.team,spawn_pos,
                        damage=self.atk,
                        speed=self.proj_speed,
                        acceleration=self.acceleration,
                        defensive=self.defensive,
                        lifetime=self.lifetime,
                        source_type='square' if self.defensive else 'triangle')
        world.projectiles.append(proj)
        self.cooldown=self.rate

class HealerBehavior:
    def __init__(self, heal=8, rate=0.5, speed = 100, acceleration = 200):
        self.heal=heal
        self.rate=rate
        self.speed=speed
        self.acceleration=acceleration
        self.cooldown=0
    def update(self, unit, dt, world):
        self.cooldown-=dt
        if self.cooldown>0: return
        spawn_pos=unit.get_next_corner()
        proj=Projectile(unit.team,spawn_pos,damage=self.heal,
                        healing=True,speed=self.speed,acceleration=self.acceleration,source_type='pentagon')
        world.projectiles.append(proj)
        self.cooldown=self.rate

# Battle arena
class World:
    def __init__(self):
        self.units=[]
        self.projectiles=[]
    def update(self, dt):
        for u in self.units: u.update(dt,self)
        for p in list(self.projectiles): p.update(dt,self)
        self.projectiles=[p for p in self.projectiles if p.alive]
    def draw(self,surf):
        for u in self.units: u.draw(surf)
        for p in self.projectiles: p.draw(surf)
    def team_alive(self, team):
        return any(u.alive and u.team==team for u in self.units)
    def draw_inactive(self,surf):
        for u in self.units: u.draw(surf)
    def update_inactive(self,surf,dt):
        for u in self.units: u.update(dt,self)

