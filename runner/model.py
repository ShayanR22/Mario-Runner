"""Fixed-step physics, finite stages, checkpoints and collision rules."""
from dataclasses import dataclass, asdict
import uuid
from .scoring import Score
from .victory import Victory
from . import balance as B
from .storage import number, integer
import pygame as pg
from .config import GROUND, WIDTH
from .levels import LEVELS
from .enemies import Enemy
from .abilities import AbilityState,ABILITIES
from .interactions import response
from .routes import platforms,support
from .secrets import BonusRoom
from .replays import Recorder

@dataclass
class Player:
    x: float = 150
    bottom: float = GROUND
    previous_bottom: float = GROUND
    velocity: float = 0
    jumps: int = 0
    buffer: float = 0
    released: bool = False
    land_time: float = 0
    double_time: float = 0
    air_time: float = 0
    on_platform: bool = False
    coyote: float = .09
    holding_jump: bool = False

    @property
    def grounded(self):
        return self.bottom >= GROUND or self.on_platform

    @property
    def body(self):
        return pg.Rect(round(self.x)-16, round(self.bottom)-60, 32,60)

    def request_jump(self):
        self.holding_jump = True
        self.buffer = .12
        self.released = False

    def release_jump(self):
        self.holding_jump = False
        self.released = True
        if self.velocity < -480:
            self.velocity = -480

    def bounce(self, surface_top):
        self.bottom = min(self.bottom, surface_top)
        self.velocity = -410
        self.jumps = 1
        self.buffer = 0
        self.double_time = 0
        self.air_time = 0

    def update(self, dt):
        self.previous_bottom = self.bottom
        self.land_time = max(0, self.land_time-dt)
        self.double_time = max(0, self.double_time-dt)
        jump = 0
        was_grounded = self.grounded
        self.coyote=.09 if was_grounded else max(0,self.coyote-dt)
        if not was_grounded and self.coyote<=0 and self.jumps==0:self.jumps=1
        if self.buffer > 0 and self.jumps < 2:
            self.on_platform=False
            self.jumps += 1
            self.velocity = -680 if self.jumps == 1 else -570
            if self.released:
                self.velocity = max(self.velocity,-480)
            self.buffer = 0
            self.land_time = 0
            self.air_time = 0
            jump = self.jumps
            if jump == 2:
                self.double_time = .24
        self.buffer = max(0,self.buffer-dt)
        self.velocity += 1850*dt
        self.bottom += self.velocity*dt
        self.air_time += dt
        if self.bottom >= GROUND:
            self.bottom = GROUND
            self.velocity = 0
            self.jumps = 0
            self.air_time = 0
            if not was_grounded:
                self.land_time = .18
        return jump

@dataclass
class Coin:
    at: float
    y: float
    collected: bool = False
    identity: str = ""
    red: bool = False

class World:
    def __init__(self, level_index=0, resume=None, base_score=0):
        self.level_index = level_index
        self.level = LEVELS[level_index]
        self.player = Player()
        self.elapsed = 0.
        self.distance = 0.
        self.coins_collected = 0
        self.stomps = 0
        self.cleared = 0
        self.base_score = base_score
        self.checkpoint = None
        self.dead = False
        self.finished = False
        self.victory = None
        self.scoring = Score()
        self.run_id = str((resume or {}).get("run_id",uuid.uuid4().hex))
        self.retries = integer((resume or {}).get("retries"))
        self.damage_count = 0
        self.result = None
        self.abilities=AbilityState.load((resume or {}).get("abilities"))
        self.projectiles=[];self.platforms=platforms(level_index)
        self.pending=[];self.room=None;self.secrets=set();self.red_ids=set();self.challenges=set()
        self.recorder=Recorder();self.ghost=None
        self.full_run=not bool(resume and resume.get("checkpoint"))
        self.start_checkpoint=0.;self.skid=0.
        self.pickups=[]
        # Each transformation has a safe, reachable introduction before later use.
        loadouts=(("mushroom","fire","cat","star","tanooki"),
                  ("ice","mushroom","penguin","star","fire"),
                  ("tanooki","boomerang","cape","star","cat"),
                  ("fire","ice","mushroom","star","mega"))
        for at,kind in zip((600,3400,5400,7400,10100),loadouts[level_index]):
            self.pickups.append({"at":at,"kind":kind,"collected":False})
        if resume and resume.get("checkpoint"):
            self.distance = number(resume.get("distance"),float(self.level.checkpoint),self.level.length)
            self.elapsed = number(resume.get("elapsed"),0,10000)
            self.coins_collected = integer(resume.get("coins"))
            self.stomps = integer(resume.get("stomps"))
            self.cleared = integer(resume.get("cleared"))
            self.base_score = integer(resume.get("base"))
            self.scoring = Score.load(resume.get("scoring"))
            self.damage_count = integer(resume.get("damage_count"))
            from .storage import strings
            self.secrets=set(strings(resume.get("secrets",[])))
            self.red_ids=set(strings(resume.get("red_ids",[])))
            self.challenges=set(strings(resume.get("challenges",[])))
            self.start_checkpoint=self.distance
        self.enemies = [Enemy(e.kind,e.at,i) for i,e in enumerate(self.level.encounters) if e.at > self.distance]
        for enemy in self.enemies:
            enemy.age = self.elapsed
        self.coins = []
        for e in self.level.encounters:
            if e.at <= self.distance:
                continue
            height = 28 if e.kind == "bullet" else 112 if e.kind == "paratroopa" else 96
            for dx in (-30,25,80):
                self.coins.append(Coin(e.at+dx,GROUND-height,identity=f"coin:{e.at}:{dx}"))
        for route in (2400,8400):
            for j,offset in enumerate((110,410,760)):
                self.coins.append(Coin(route+offset,GROUND-(120 if j!=1 else 180),identity=f"red:{route}:{j}",red=True))
        self.coins=[c for c in self.coins if c.at>self.distance]
        for coin in self.coins:
            coin.collected=coin.identity in self.scoring.awarded
        for item in self.pickups:
            item["collected"]=item["at"]<self.distance or f"pickup:{item['at']}" in self.scoring.awarded
        if resume and resume.get("checkpoint"):
            # Checkpoints are at safe ground clearings. Restore state of all remaining actors.
            saved=resume.get("enemies",[])
            if isinstance(saved,list):
                for e,state in zip(self.enemies,saved):
                    if isinstance(state,dict) and state.get("index")==e.index:
                        if state.get("state") in ("alive","gone","shell","collapsed","squashed","frozen","frozen_shell"):e.state=state["state"]
                        e.timer=number(state.get("timer"),0,10);e.age=number(state.get("age"),self.elapsed,10000)
                        e.offset=number(state.get("offset"),0,3000,lower=-3000);e.frozen_y=number(state.get("frozen_y"),GROUND,GROUND)
            self.checkpoint = self.snapshot(True)

    @property
    def speed(self):
        return self.level.speed_at(self.distance)+(45 if self.abilities.slide>0 else 0)

    @property
    def score(self):
        return self.base_score + self.scoring.points

    @property
    def stage_score(self):
        return self.score-self.base_score

    @property
    def progress(self):
        return min(1,self.distance/self.level.length)

    def screen_x(self, at):
        return 150+at-self.distance

    def visible_enemies(self):
        return [e for e in self.enemies if -100 < e.x(self) < WIDTH+100]

    def snapshot(self, checkpoint=False):
        return {"level":self.level_index,"checkpoint":checkpoint,"elapsed":self.elapsed,
                "distance":self.distance,"coins":self.coins_collected,"stomps":self.stomps,
                "cleared":self.cleared,"base":self.base_score,"scoring":self.scoring.dump(),
                "run_id":self.run_id,"retries":self.retries,"damage_count":self.damage_count,
                "abilities":self.abilities.dump(),"secrets":sorted(self.secrets),"red_ids":sorted(self.red_ids),
                "challenges":sorted(self.challenges),"enemies":[asdict(e) for e in self.enemies if e.at>self.distance],
                "player":{"bottom":GROUND,"jumps":0,"velocity":0}}

    def reward(self, identity, points, x, y, events, action=True, style=""):
        amount=self.scoring.award(identity,points,action,style)
        if amount:
            events.append((f"score:{amount}",x,y))
        return amount

    def begin_finish(self):
        if self.victory is not None:
            return
        self.victory=Victory(max(0,GROUND-self.player.bottom))
        self.scoring.award("flag",self.victory.bonus,False)
        self.scoring.award("clear",B.CLEAR,False)
        if not self.damage_count and not self.retries:
            self.scoring.award("clean",B.CLEAN,False)
        if not self.damage_count and not self.retries:self.challenges.add("no_damage")
        if self.abilities.uses<=3:self.challenges.add("limited_ability")
        if self.victory.bonus==B.FLAG_MAX:self.challenges.add("flag_top")
        self.player.velocity=0
        self.result={"flag":self.victory.bonus,"clear":B.CLEAR,"clean":B.CLEAN if not self.damage_count and not self.retries else 0}


    def attack(self):
        if self.dead or self.victory or self.room:return
        # A nearby frozen block is kicked before firing another projectile.
        for e in self.visible_enemies():
            if e.state=="frozen" and 0<e.x(self)-self.player.x<115 and abs(e.bottom-self.player.bottom)<80:
                e.state="frozen_shell";e.timer=2.4;self.pending.append(("kick",e.x(self),e.bottom));return
        if self.abilities.attack(self):self.pending.append(("attack",self.player.x,self.player.bottom-35))

    def context(self):
        if self.room:
            if self.room.distance>self.room.length-350:self.exit_room()
            return
        if self.dead or self.victory:return
        if abs(self.distance-5500)<110 and "entered" not in self.secrets and self.player.grounded:
            self.room=BonusRoom();self.player.bottom=GROUND;self.player.velocity=0
            self.pending.append(("pipe",self.player.x,GROUND));return
        if self.abilities.equipped=="cat" and any(abs(self.distance-(start-80))<100 for start in (2400,8400)):
            self.abilities.climb=1.0;self.player.velocity=0
        elif self.abilities.equipped in ("cat","cape") and not self.player.grounded:
            self.abilities.dive=True;self.player.velocity=750
        elif self.abilities.equipped=="penguin" and 4000<self.distance<4800:
            self.abilities.slide=.8
        else:
            for e in self.visible_enemies():
                if e.state=="frozen" and 0<e.x(self)-self.player.x<115:
                    e.state="frozen_shell";e.timer=2.4;break

    def exit_room(self):
        if not self.room:return
        self.secrets.add("entered");self.room=None
        self.player.bottom=GROUND;self.player.velocity=0;self.player.jumps=0
        self.abilities.grace=max(self.abilities.grace,.7)
        self.pending.append(("pipe",self.player.x,GROUND))

    def affect(self,enemy,method,events):
        identity=f"enemy:{enemy.index}"
        if enemy.state=="gone":return False
        outcome=response(enemy.kind,method)
        if outcome=="block":return False
        if enemy.state=="frozen":
            outcome="defeat" if method!="stomp" else "shell"
        if outcome=="freeze":
            enemy.frozen_y=enemy.bottom;enemy.state="frozen";enemy.timer=4.
            events.append(("freeze",enemy.x(self),enemy.bottom));return True
        if outcome=="shell" and enemy.state=="frozen":enemy.state="frozen_shell";enemy.timer=2.4
        elif outcome in ("shell","collapse") or method=="stomp":enemy.stomp()
        else:enemy.state="gone"
        value=B.SHELL if method=="shell" else B.STOMP if method=="stomp" else B.ABILITY
        self.reward(identity,value,enemy.x(self),enemy.bottom-60,events,style=method)
        events.append(("stomp",enemy.x(self),enemy.bottom-40));return True

    def collect(self,coin,events):
        if coin.collected:return
        coin.collected=True;self.coins_collected+=1
        self.reward(coin.identity or f"coin:{coin.at}:{coin.y}",B.COIN,self.screen_x(coin.at),coin.y-20,events,style="coin")
        if coin.red:
            self.red_ids.add(coin.identity)
            if len(self.red_ids)==6:
                self.reward("red_set",B.RED_SET,self.player.x,self.player.bottom-100,events,False)
                self.challenges.add("red_set")
        events.append(("coin",self.screen_x(coin.at),coin.y))

    def update(self, dt, assets):
        if self.dead or self.finished or self.victory:return []
        events=self.pending;self.pending=[]
        if self.room:
            room=self.room;room.age+=dt;room.distance+=280*dt
            jumped=self.player.update(dt)
            if jumped:events.append(("jump",self.player.x,self.player.bottom))
            for at,y,identity in room.coins:
                x=self.player.x+at-room.distance
                if identity not in room.collected and self.player.body.inflate(12,12).colliderect(pg.Rect(x-10,y-12,20,24)):
                    room.collected.add(identity)
                    self.reward(identity,B.COIN,x,y,events,style="coin")
            if room.distance>=room.length:self.exit_room()
            return events
        self.elapsed+=dt
        self.abilities.update(dt,self.player,self.player.holding_jump)
        previous_distance=self.distance
        if self.abilities.climb>0:
            self.abilities.climb=max(0,self.abilities.climb-dt)
            self.player.bottom=max(GROUND-185,self.player.bottom-190*dt)
            self.player.previous_bottom=self.player.bottom;self.player.velocity=-80
            if not self.abilities.climb:self.player.velocity=-280;self.player.jumps=1;self.distance+=50
            jumped=0
        else:
            self.distance=min(self.level.length,self.distance+self.speed*dt)
            if self.player.on_platform:
                self.player.on_platform=any(p.rect(self).left<self.player.x+15 and p.rect(self).right>self.player.x-15 and abs(p.rect(self).top-self.player.bottom)<18 for p in self.platforms)
            jumped=self.player.update(dt);support(self,dt)
        if self.level_index==1 and 4000<self.distance<4800:
            if self.player.land_time>0 and self.abilities.equipped!="penguin":self.skid=20.
            self.skid=max(0.,self.skid-100*dt)
            self.player.x=min(164.,self.player.x+self.skid*dt)
        else:self.player.x=max(150.,self.player.x-35*dt)
        if jumped:events.append(("double" if jumped==2 else "jump",self.player.x,self.player.bottom))
        for enemy in self.enemies:
            thawing=enemy.state=="frozen" and enemy.timer<=dt
            enemy.update(dt,self)
            if thawing and abs(enemy.x(self)-self.player.x)<70:self.abilities.grace=max(self.abilities.grace,.5)
            if not enemy.passed and enemy.x(self)<self.player.x-60:enemy.passed=True;self.cleared+=1
        active=self.visible_enemies()
        opportunity=any(not c.collected and -30<c.at-self.distance<650 and abs(c.y-self.player.bottom)<210 for c in self.coins) or any(e.dangerous and 0<e.x(self)-self.player.x<650 for e in active)
        self.scoring.update(dt,opportunity)
        if self.player.grounded:self.scoring.air_chain=0
        for shell in active:
            if shell.state in ("shell","frozen_shell"):
                for other in active:
                    if other is not shell and other.state in ("alive","frozen") and shell.rect(self).colliderect(other.rect(self)):
                        self.affect(other,"shell",events)
        for shot in self.projectiles:
            shot.update(dt,self)
            if shot.life<=0:continue
            for enemy in active:
                if enemy.state not in ("alive","frozen") or enemy.index in shot.hit:continue
                if shot.rect(self).colliderect(enemy.rect(self)):
                    self.affect(enemy,"tail" if shot.kind=="boomerang" else shot.kind,events)
                    shot.hit.add(enemy.index)
                    if shot.kind!="boomerang":shot.life=0;break
            if shot.kind=="boomerang":
                for coin in self.coins:
                    if not coin.collected and shot.rect(self).colliderect(pg.Rect(self.screen_x(coin.at)-12,coin.y-12,24,24)):self.collect(coin,events)
        self.projectiles=[p for p in self.projectiles if p.life>0 and -80<self.screen_x(p.at)<WIDTH+100][:B.PROJECTILE_LIMIT+1]
        if self.abilities.attack_time>0 or self.abilities.dive or self.abilities.slide>0:
            spec=self.abilities.definition
            method="shell" if self.abilities.slide else spec.melee if spec else ""
            reach=self.player.body.inflate(125,50 if self.abilities.dive else 8).move(25,0)
            for enemy in active:
                if enemy.state in ("alive","frozen") and reach.colliderect(enemy.rect(self)):self.affect(enemy,method,events)
        for enemy in active:
            if (self.abilities.star>0 or self.abilities.mega>0) and self.player.body.inflate(16,12).colliderect(enemy.rect(self)):
                self.affect(enemy,"mega" if self.abilities.mega>0 else "star",events)
            if not enemy.dangerous or self.abilities.invincible:
                continue
            rect = enemy.rect(self)
            horizontal = self.player.body.right > rect.left+3 and self.player.body.left < rect.right-3
            crossed_top = self.player.previous_bottom <= enemy.previous_top+10 and self.player.bottom >= rect.top
            if enemy.stompable and horizontal and crossed_top and self.player.velocity > 0:
                self.affect(enemy,"stomp",events)
                self.player.bounce(rect.top)
                self.stomps += 1

                self.scoring.air_chain+=1
                if self.scoring.air_chain>=3:self.challenges.add("air_chain")
                if self.scoring.air_chain>1:
                    self.reward(f"chain:{enemy.index}",100*(self.scoring.air_chain-1),enemy.x(self),rect.top-45,events,False)
                events.append(("stomp",enemy.x(self),rect.top))
                continue
            if self.player.body.inflate(-4,-4).colliderect(rect.inflate(-4,-3)):
                mask,mask_rect = assets.enemy_collision(enemy,self)
                body = self.player.body
                if assets.body_mask.overlap(mask,(mask_rect.x-body.x,mask_rect.y-body.y)):
                    self.damage_count+=1
                    self.scoring.damage()
                    if self.abilities.damage():
                        events.append(("damage",self.player.x,self.player.bottom-25))
                        continue
                    self.dead = True
                    events.append(("hit",self.player.x,self.player.bottom-25))
                    return events
        for coin in self.coins:
            x=self.screen_x(coin.at)
            if not coin.collected and self.player.body.inflate(10,8).colliderect(pg.Rect(x-8,coin.y-10,16,20)):
                self.collect(coin,events)
        for item in self.pickups:
            if not item["collected"] and self.player.body.inflate(12,6).colliderect(pg.Rect(self.screen_x(item["at"])-18,GROUND-40,36,38)):
                item["collected"]=True;self.scoring.awarded.add(f"pickup:{item['at']}")
                self.abilities.activate(item["kind"]);events.append((f"pickup:{item['kind']}",self.player.x,GROUND-65))
        for checkpoint_at in (self.level.checkpoint,self.level.finale_checkpoint):
            if self.start_checkpoint<checkpoint_at and previous_distance<checkpoint_at<=self.distance:
                # Safe clearing: normalize to the ground before capturing every subsystem.
                self.player.bottom=GROUND;self.player.velocity=0;self.player.jumps=0;self.player.on_platform=False
                self.projectiles.clear();self.start_checkpoint=checkpoint_at
                self.distance=float(checkpoint_at);self.checkpoint=self.snapshot(True)
                events.append(("checkpoint",self.player.x,GROUND-80))
        self.recorder.sample(self)
        if self.distance >= self.level.length:
            self.begin_finish()
            events.append(("finish",self.player.x,GROUND-80))
        return events
