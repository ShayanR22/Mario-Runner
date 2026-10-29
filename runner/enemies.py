"""Predictable enemies share scrolling; special movement is bounded."""
from dataclasses import dataclass
import math
import pygame as pg
from .config import GROUND

SIZES = {"goomba":(40,36), "koopa":(36,50), "buzzy":(40,30),
         "paratroopa":(38,46), "bullet":(48,28), "drybones":(36,50),
         "fire":(32,54), "pipe":(48,44)}

@dataclass
class Enemy:
    kind: str
    at: float
    index: int = 0
    age: float = 0
    state: str = "alive"
    timer: float = 0
    offset: float = 0
    passed: bool = False
    previous_top: float = 0
    frozen_y: float = GROUND

    @property
    def bottom(self):
        if self.state in ("frozen","frozen_shell"):
            return self.frozen_y
        if self.kind == "bullet":
            return GROUND-92
        if self.kind == "paratroopa":
            return GROUND-24+math.sin(self.age*2.5)*8
        return GROUND

    @property
    def fire_phase(self):
        # Warning 0.8s, active 1.25s, cooling 1.2s; pad stays visible.
        return (self.age+self.index*.31) % 3.25

    @property
    def warning(self):
        return self.kind == "fire" and self.fire_phase < .8

    @property
    def dangerous(self):
        return self.state == "alive" and (self.kind != "fire" or .8 <= self.fire_phase < 2.05)

    @property
    def stompable(self):
        return self.kind in ("goomba","koopa","buzzy","paratroopa","drybones")

    def x(self, world):
        return world.screen_x(self.at)+self.offset

    def rect(self, world):
        w,h = SIZES[self.kind]
        return pg.Rect(round(self.x(world)-w/2), round(self.bottom-h), w,h)

    def update(self, dt, world):
        self.previous_top = self.bottom-SIZES[self.kind][1]
        self.age += dt
        if self.state == "frozen":
            self.timer-=dt
            if self.timer<=0:self.state="alive"
        elif self.state in ("shell","frozen_shell"):
            self.offset += 520*dt
            self.timer -= dt
            if self.timer <= 0:
                self.state = "gone"
        elif self.state in ("collapsed","squashed"):
            self.timer -= dt
            if self.timer <= 0:
                self.state = "alive" if self.state == "collapsed" else "gone"

    def stomp(self):
        if self.kind == "koopa":
            self.state,self.timer = "shell",2.4
        elif self.kind == "drybones":
            self.state,self.timer = "collapsed",1.6
        else:
            self.state,self.timer = "squashed",.35

    def sprite(self):
        if self.state in ("shell","collapsed"):
            return "shell" if self.state == "shell" else "bones"
        if self.kind == "fire" and not self.dangerous:
            return "vent"
        return self.kind
