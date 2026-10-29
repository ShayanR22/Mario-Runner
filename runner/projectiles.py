"""Bounded projectiles in world coordinates; deterministic fixed-step motion."""
from dataclasses import dataclass,field
import math
import pygame as pg
from .config import GROUND

@dataclass
class Projectile:
    kind: str
    at: float
    y: float
    vx: float
    vy: float = 0.
    life: float = 2.1
    age: float = 0.
    hit: set = field(default_factory=set)

    def rect(self,world):return pg.Rect(round(world.screen_x(self.at))-9,round(self.y)-9,18,18)

    def update(self,dt,world):
        self.life-=dt;self.age+=dt
        if self.kind=="boomerang":
            self.vx=world.speed+(430 if self.age<.48 else -350)
            self.y=world.player.bottom-35-35*math.sin(min(1.,self.age/1.1)*math.pi)
            if self.age>.6 and self.at<world.distance+18:self.life=0
        elif self.kind=="fire":
            self.vy+=850*dt;self.y+=self.vy*dt
            if self.y>=GROUND-9:self.y=GROUND-9;self.vy=-310
        self.at+=self.vx*dt
