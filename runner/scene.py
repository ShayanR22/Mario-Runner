"""Layered biome rendering and bounded effects. Rendering never advances physics."""
from dataclasses import dataclass
import random
import pygame as pg
from .config import WIDTH,HEIGHT,GROUND,GOLD,CREAM,INK,MINT
from .levels import LEVELS,ENEMY_HINTS

@dataclass
class Particle:
    x:float
    y:float
    vx:float
    vy:float
    life:float
    color:tuple
    size:int

class Scene:
    def __init__(self,assets):
        self.assets=assets
        self.time=0.
        self.decor_distance=0.
        self.particles=[]
        self.popups=[]
        self.rng=random.Random(21)
        self.outfit="classic";self.ghost_visible=True;self.atmosphere=True;self.quality=1.;self.reduced=False
        self.ghost_cache={}
        self.outline_cache={}
        self.shake_time=0.
        self.tint=pg.Surface((WIDTH,HEIGHT),pg.SRCALPHA)
        self.tint.fill((10,18,39,100))
        self.cloud=pg.Surface((112,40),pg.SRCALPHA)
        for rect in ((0,22,112,14),(16,12,78,22),(35,4,39,28)):
            pg.draw.rect(self.cloud,(238,249,246,175),rect)

    def burst(self,x,y,color=GOLD,amount=12):
        for _ in range(amount):
            self.particles.append(Particle(x,y,self.rng.uniform(-90,90),
                self.rng.uniform(-150,-35),self.rng.uniform(.25,.65),color,self.rng.choice((2,4,6))))
        self.particles=self.particles[-160:]

    def popup(self,x,y,text):
        self.popups.append([x,y,str(text),.85])
        self.popups=self.popups[-16:]

    def update(self,dt,speed,reduced=False):
        self.shake_time=max(0,self.shake_time-dt)
        for label in self.popups:
            label[3]-=dt
            if not reduced:label[1]-=26*dt
        self.popups=[p for p in self.popups if p[3]>0]
        if not reduced:
            self.time+=dt
            self.decor_distance+=speed*dt
        else:
            self.particles.clear()
        for p in self.particles:
            p.life-=dt
            p.vy+=370*dt
            p.x+=p.vx*dt
            p.y+=p.vy*dt
        self.particles=[p for p in self.particles if p.life>0]

    def backdrop(self,s,level,distance,reduced=False):
        decor=self.decor_distance
        pair=self.assets.backgrounds[level.biome]
        offset=int(decor*.075)
        tile_index=offset//WIDTH
        shift=offset%WIDTH
        s.blit(pair[tile_index%2],(-shift,0))
        s.blit(pair[(tile_index+1)%2],(WIDTH-shift,0))
        if self.atmosphere and not reduced:
            count=int(18*self.quality)
            color={"grass":(238,234,156),"cave":(125,146,170),"sky":(229,245,250),"castle":(211,140,111)}[level.biome]
            for i in range(count):
                px=int((i*163+self.time*(8 if level.biome!="sky" else 32)-decor*.04)%WIDTH)
                py=int(170+(i*79+self.time*(5 if level.biome!="castle" else -18))%210)
                pg.draw.rect(s,color,(px//2*2,py//2*2,2,2))
        # Additional layers are separate from the generated distant scenery.
        if level.biome in ("grass","sky"):
            for i in range(6):
                x=(i*230+50-decor*.17-self.time*5)%1380-112
                y=110+i%3*42
                s.blit(self.cloud,(int(x)//2*2,y))
        elif level.biome=="cave":
            for i in range(9):
                x=(i*149-decor*.3)%1341-70
                image=self.assets.frame("props","crystal",self.time+i)
                s.blit(image,(int(x)//2*2,GROUND-144))
        elif self.atmosphere:
            # Embers remain behind the gameplay silhouettes.
            for i in range(22):
                x=(i*71-decor*.12)%WIDTH
                y=GROUND-((self.time*22+i*47)%310)
                pg.draw.rect(s,(243,140,90),(int(x)//2*2,int(y)//2*2,2,4))
        tile=self.assets.grounds[level.biome]
        ground_offset=int(distance)//2*2%128
        if level.biome=="sky":
            s.fill((141,199,223),(0,GROUND,WIDTH,HEIGHT-GROUND))
            for i in range(10):
                s.blit(self.cloud,(i*118-int(decor*.3)%118,GROUND+45+i%2*8))
        else:
            s.fill((25,28,44),(0,GROUND,WIDTH,HEIGHT-GROUND))
        rows=1 if level.biome=="sky" else 2
        for row in range(rows):
            for x in range(-ground_offset,WIDTH,128):
                if row:
                    s.blit(tile,(x,GROUND+row*64),(0,8,128,56))
                else:
                    s.blit(tile,(x,GROUND))
        # Strong light edge cleanly separates the playable floor from scenery.
        pg.draw.line(s,level.accent,(0,GROUND),(WIDTH,GROUND),2)

    def flags(self,s,world):
        for at in (world.level.checkpoint,world.level.finale_checkpoint):
            x=world.screen_x(at)
            if -100<x<WIDTH+100:
                image=self.assets.frame("props","checkpoint",self.time)
                s.blit(pg.transform.scale(image,(96,120)),(round(x)-24,GROUND-114))
        x=world.screen_x(world.level.length)
        if -120<x<WIDTH+120:
            pg.draw.rect(s,(238,235,210),(round(x)-3,GROUND-270,6,270))
            pg.draw.circle(s,GOLD,(round(x),GROUND-274),8)
            drop=0
            if world.victory and world.victory.phase not in ("grab",):
                drop=210*min(1,world.victory.age/1.1)
            pg.draw.polygon(s,(238,90,94),[(x+3,GROUND-262+drop),(x+73,GROUND-240+drop),(x+3,GROUND-218+drop)])
            pg.draw.rect(s,(202,195,164),(x-19,GROUND-7,38,7))
            # Exit is reached by the automatic walk after sliding and hopping.
            pg.draw.rect(s,(100,109,132),(x+180,GROUND-122,126,122))
            for dx in range(0,127,28):pg.draw.rect(s,(160,173,185),(x+180+dx,GROUND-142,18,26))
            pg.draw.rect(s,INK,(x+211,GROUND-68,40,68))
            pg.draw.rect(s,(180,194,206),(x+201,GROUND-78,60,12))

    def actors(self,s,world,idle=False,hurt_time=None):
        if world.room:
            self.bonus_room(s,world,idle,hurt_time)
            return
        self.routes(s,world)
        self.flags(s,world)
        self.ghost_actor(s,world)
        for coin in world.coins:
            x=world.screen_x(coin.at)
            if not coin.collected and -40<x<WIDTH+40:
                image=self.assets.frame("props","coin",world.elapsed)
                if coin.red:
                    pg.draw.circle(s,(227,73,84),(round(x),round(coin.y)),12)
                    pg.draw.circle(s,(255,222,173),(round(x),round(coin.y)),9,2)
                    pg.draw.line(s,(255,242,209),(x-4,coin.y),(x+4,coin.y),3)
                    pg.draw.line(s,(255,242,209),(x,coin.y-4),(x,coin.y+4),3)
                else:s.blit(image,(int(x)-32,int(coin.y)-56))
        for e in world.visible_enemies():
            if e.state=="gone":
                continue
            x=int(e.x(world))//2*2
            bottom=int(e.bottom)//2*2
            # All frames share the same (32,76) display anchor.
            image=self.assets.frame("enemies",e.sprite(),e.age)
            if e.state in ("frozen","frozen_shell"):
                r=e.rect(world).inflate(8,6)
                pg.draw.rect(s,(80,171,217),r)
                pg.draw.rect(s,(194,246,255),r,3)
                pg.draw.line(s,(216,251,255),r.topleft,r.bottomright,2)
                u=self.assets.font(19).render("!" if e.timer<1 else "ICE",True,(17,52,81))
                s.blit(u,u.get_rect(center=r.center))
                continue
            if e.state=="squashed":
                image=pg.transform.scale(image,(64,20))
                s.blit(image,(x-32,bottom-19))
            else:
                s.blit(image,(x-32,bottom-76))
            if e.warning:
                pg.draw.rect(s,GOLD,(x-17,GROUND-65,34,22))
                font=self.assets.font(22)
                mark=font.render("!",True,INK)
                s.blit(mark,mark.get_rect(center=(x,GROUND-54)))
            if e.kind=="bullet" and e.state=="alive":
                length=10+int(e.age*18)%3*4
                pg.draw.polygon(s,GOLD,[(x+27,bottom-22),(x+27+length,bottom-15),(x+27,bottom-8)])
        player=world.player
        shadow_w=max(16,42-(GROUND-player.bottom)/6)
        pg.draw.ellipse(s,(42,61,55),(int(player.x-shadow_w/2),GROUND-5,int(shadow_w),5))
        self.player_actor(s,world,idle,hurt_time)
        for x,y,text,life in self.popups:
            label=self.assets.font(24).render(text,True,GOLD)
            s.blit(label,(int(x)-label.get_width()//2,int(y)))
        for p in self.particles:
            pg.draw.rect(s,p.color,(int(p.x)//2*2,int(p.y)//2*2,p.size,p.size))

    def player_actor(self,s,world,idle=False,hurt_time=None):
        a,p=world.abilities,world.player
        spec=a.definition
        form="mega" if a.mega>0 else a.equipped or "classic"
        pose="flag" if world.victory and world.victory.phase in ("grab","slide") else "run" if world.victory and world.victory.phase=="walk" else "climb" if a.climb else "transform" if a.transform_time else "dive" if a.dive else "attack" if a.attack_time else "glide" if spec and spec.fall_cap and p.holding_jump and p.velocity>0 else None
        image=self.assets.player(p,world.elapsed if not idle else self.time,idle,hurt_time,form,pose,self.outfit)
        x=round(p.x)-image.get_width()//2;y=round(p.bottom)-int(image.get_height()*.95)
        if a.star>0 or a.grace>0 or a.mega>0:
            key=(form,pose or "run",int(world.elapsed*10)%6,image.get_size())
            if key not in self.outline_cache:
                # A cached silhouette outline, no flashing or full-screen recoloring.
                mask=pg.mask.from_surface(image)
                self.outline_cache[key]=mask.outline(3)
            color=(255,226,112) if a.star>0 else (140,224,243)
            points=self.outline_cache[key]
            if len(points)>2:pg.draw.lines(s,color,True,[(x+px,y+py) for px,py in points],3)
        if not (world.victory and world.victory.phase=="done"):
            s.blit(image,(x,y))
        if a.attack_time>0:
            color=spec.color if spec else GOLD
            pg.draw.arc(s,color,(p.x+5,p.bottom-65,90,65),-.9,1.1,5)
            if a.equipped=="cat":
                for dy in (0,8,16):pg.draw.line(s,CREAM,(p.x+43,p.bottom-62+dy),(p.x+76,p.bottom-49+dy),2)
        if self.outfit=="trail" and not p.grounded and not self.reduced:
            for i in range(4):pg.draw.rect(s,(126,221,210),(int(p.x)-38-i*12,int(p.bottom)-20+i*3,4,4))

    def ghost_actor(self,s,world):
        if not self.ghost_visible or not world.ghost or world.room:return
        frame=world.ghost.at(world.elapsed)
        if not frame:return
        _,distance,bottom,form,velocity,jumps,pose,screen_x=frame
        x=screen_x+distance-world.distance
        if not -80<x<WIDTH+80:return
        image=self.assets.forms.get(form,self.assets.forms["classic"])[self.assets.frame_id("mario",pose,frame[0])]
        key=(form,pose,self.assets.frame_id("mario",pose,frame[0]))
        if key not in self.ghost_cache:
            ghost=image.copy();ghost.fill((119,227,255,120),special_flags=pg.BLEND_RGBA_MULT);ghost.set_alpha(100)
            self.ghost_cache[key]=ghost
        ghost=self.ghost_cache[key]
        s.blit(ghost,(round(x)-32,round(bottom)-76))
        pg.draw.circle(s,(139,225,255),(round(x),round(bottom)-85),4,1)

    def routes(self,s,world):
        for platform in world.platforms:
            rect=platform.rect(world)
            if rect.right<0 or rect.left>WIDTH:continue
            rect=pg.Rect(rect)
            pg.draw.rect(s,(38,52,68),rect.move(0,3))
            pg.draw.rect(s,(121,148,142),rect)
            pg.draw.rect(s,world.level.accent,(rect.x,rect.y,rect.w,5))
            for dx in range(6,rect.w,24):pg.draw.rect(s,(214,231,201),(rect.x+dx,rect.y+8,8,3))
            if platform.moving:
                pg.draw.line(s,(163,196,207),(rect.centerx,rect.y-32),(rect.centerx,rect.y-12),2)
                pg.draw.polygon(s,CREAM,[(rect.centerx-4,rect.y-27),(rect.centerx,rect.y-32),(rect.centerx+4,rect.y-27)])
        for start in (2400,8400):
            x=world.screen_x(start-80)
            if -30<x<WIDTH:
                pg.draw.rect(s,(81,129,118),(x-6,GROUND-180,12,180))
                for y in range(GROUND-170,GROUND-12,22):pg.draw.line(s,MINT,(x-4,y+7),(x+4,y),2)
                if 0<x<WIDTH-150:s.blit(self.assets.font(18).render("CAT: DOWN  /  JUMP FOR HIGH ROUTE",True,CREAM),(x-5,GROUND-205))
        if world.level_index==1:
            left=world.screen_x(4000);right=world.screen_x(4800)
            if right>0 and left<WIDTH:
                pg.draw.rect(s,(167,225,239),(left,GROUND+2,right-left,8))
                s.blit(self.assets.font(20).render("ICE  /  PENGUIN: DOWN TO SLIDE",True,CREAM),(max(15,left),GROUND+20))
        x=world.screen_x(5500)
        if -120<x<WIDTH+120:
            pg.draw.rect(s,(36,126,105),(x-30,GROUND-42,60,42));pg.draw.rect(s,(110,216,145),(x-35,GROUND-46,70,10))
            s.blit(self.assets.font(20).render("DOWN: SECRET PIPE",True,CREAM),(x-66,GROUND-75))
        for item in world.pickups:
            x=world.screen_x(item['at'])
            if not item['collected'] and -50<x<WIDTH+50:
                image=self.assets.icons[item['kind']]
                s.blit(image,(round(x)-24,GROUND-55))
                color=(255,219,123)
                pg.draw.rect(s,color,(round(x)-25,GROUND-58,50,58),1)
        for shot in world.projectiles:
            x=round(world.screen_x(shot.at));y=round(shot.y)
            if shot.kind=="boomerang":pg.draw.lines(s,(132,201,252),False,[(x-8,y+7),(x,y-7),(x+8,y+4)],5)
            else:
                color=(255,167,73) if shot.kind=="fire" else (134,231,255)
                pg.draw.circle(s,color,(x,y),9);pg.draw.circle(s,CREAM,(x+2,y-2),4)
                for i in range(3):pg.draw.rect(s,color,(x-15-i*9,y+i%2*3,3,3))

    def bonus_room(self,s,world,idle,hurt_time):
        room=world.room
        s.blit(self.tint,(0,0))
        for at,y,identity in room.coins:
            x=150+at-room.distance
            if identity not in room.collected and -30<x<WIDTH:
                s.blit(self.assets.frame("props","coin",room.age),(int(x)-32,int(y)-56))
        exit_x=150+room.length-room.distance
        pg.draw.rect(s,(47,156,123),(exit_x-25,GROUND-70,50,70))
        self.player_actor(s,world,idle,hurt_time)
        label=self.assets.font(27).render("BONUS ROOM  /  Main course paused. Run to the exit.",True,GOLD)
        s.blit(label,label.get_rect(center=(480,170)))

    def warning(self,world):
        if world.room:return None
        if world.distance>world.level.finale_checkpoint and world.distance<world.level.length-800:
            return ("FINALE: STOMP THE KOOPA, THEN GOOMBA", "FINALE: PIPE & BEETLE / JUMP OR FREEZE", "FINALE: STAY LOW, THEN JUMP", "FINALE: FIRE AND BONES / TIME YOUR JUMPS")[world.level_index]
        for e in world.visible_enemies():
            if e.kind=="bullet" and e.state=="alive" and e.x(world)>world.player.x+100:return "BULLET BILL INCOMING >  STAY LOW"
        for e in world.visible_enemies():
            if e.state=="alive" and world.player.x+80<e.x(world)<WIDTH-25:
                return ENEMY_HINTS[e.kind]
        return None
