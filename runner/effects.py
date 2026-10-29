"""Visual-only light placement and protection of gameplay silhouettes."""
import pygame as pg
from .config import WIDTH,GROUND

def protect_actors(surface,world):
    pg.draw.rect(surface,"white",world.player.body.inflate(44,26))
    for enemy in world.visible_enemies():
        if enemy.state!="gone":
            pg.draw.rect(surface,"white",enemy.rect(world).inflate(36,24))
    for coin in world.coins:
        x=world.screen_x(coin.at)
        if not coin.collected and -30<x<WIDTH+30:
            pg.draw.rect(surface,"white",(int(x)-22,int(coin.y)-24,44,48))
    for platform in world.platforms:
        pg.draw.rect(surface,"white",pg.Rect(platform.rect(world)).inflate(12,12))
    for item in world.pickups:
        x=world.screen_x(item["at"])
        if not item["collected"] and -50<x<WIDTH+50:pg.draw.rect(surface,"white",(int(x)-30,GROUND-65,60,65))
    for shot in world.projectiles:pg.draw.rect(surface,"white",shot.rect(world).inflate(16,16))
    # Keep the runway and flags rigid, including their edges.
    pg.draw.rect(surface,"white",(0,GROUND-5,WIDTH,110))
    for at in (world.level.checkpoint,world.level.length):
        x=world.screen_x(at)
        if -100<x<WIDTH+100:
            pg.draw.rect(surface,"white",(int(x)-32,GROUND-286,345,286))

def environment_lights(world,scene):
    lights=[]
    a=world.abilities
    if a.star>0 or a.mega>0:lights.append((world.player.x,world.player.bottom-35,.24,.85,(1.,.8,.25)))
    for shot in world.projectiles[:3]:lights.append((world.screen_x(shot.at),shot.y,.12,.8,(1.,.4,.1) if shot.kind=="fire" else (.25,.7,1.)))
    for at in (world.level.checkpoint,world.level.finale_checkpoint):
        x=world.screen_x(at)
        if 0<x<WIDTH:lights.append((x,GROUND-70,.18,.6,(.3,1.,.65)))
    if world.level.biome=="cave":
        for i in range(9):
            x=(i*149-scene.decor_distance*.3)%1341-70
            if 0<x<WIDTH:
                lights.append((x+32,GROUND-106,.17,.65,(.15,.75,1.0)))
    elif world.level.biome=="castle":
        # Broad warm pools supplement the emissive atlas and the actual vents.
        lights.extend([(240,310,.35,.55,(1.0,.30,.07)),(750,280,.32,.45,(1.0,.25,.05))])
        for enemy in world.visible_enemies():
            if enemy.kind=="fire" and enemy.dangerous:
                lights.insert(0,(enemy.x(world),GROUND-20,.20,1.2,(1.0,.40,.08)))
    return lights[:8]

class Quality:
    """Slow hysteresis; only decorative load changes, never the simulation."""
    def __init__(self):self.level=1.;self.average=.01;self.age=0.
    def update(self,cost,dt):
        self.average=self.average*.98+min(.1,cost)*.02;self.age+=dt
        if self.age>5:
            if self.average>.020:self.level=max(.35,self.level-.15);self.age=0
            elif self.average<.012 and self.age>12:self.level=min(1.,self.level+.1);self.age=0
