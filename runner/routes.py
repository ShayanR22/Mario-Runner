"""One-way optional platforms. All main courses remain safe at ground level."""
from dataclasses import dataclass
import math
import pygame as pg
from .config import GROUND

@dataclass(frozen=True)
class Platform:
    at: float
    width: float
    top: float
    moving: bool = False
    def y(self,time):return self.top+(12*math.sin(time*1.4) if self.moving else 0)
    def rect(self,world):return pg.FRect(world.screen_x(self.at),self.y(world.elapsed),self.width,18)

def platforms(index):
    return [p for start in (2400,8400) for p in (
        Platform(start,330,GROUND-88),
        Platform(start+350,340,GROUND-148,index==2),
        Platform(start+720,260,GROUND-94))]

def support(world,dt):
    """Carry a standing player with vertical motion, then check swept landings."""
    p=world.player
    for platform in world.platforms:
        rect=platform.rect(world)
        if rect.left<p.x+15 and rect.right>p.x-15:
            before=platform.y(world.elapsed-dt)
            if p.velocity>=0 and p.previous_bottom<=before+3 and p.bottom>=rect.top:
                p.bottom=float(rect.top);p.velocity=0;p.jumps=0;p.on_platform=True;p.coyote=.09
                p.land_time=.12 if p.previous_bottom<before-2 else p.land_time
                return
    p.on_platform=False
