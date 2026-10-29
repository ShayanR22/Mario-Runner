"""Application states and UI. Simulation, records and presentation stay separate."""
import argparse
import os
import time
import pygame as pg
from .assets import Assets
from .audio import Audio
from .config import WIDTH,HEIGHT,GROUND,STEP,FPS,INK,CREAM,GOLD,MINT
from .levels import LEVELS
from .model import World
from .scene import Scene
from .storage import SaveData
from .ui import UI
from .rendering import Presenter
from .effects import environment_lights,protect_actors,Quality
from .balance import MEDALS,medal,rank
from .replays import Ghost
from .abilities import ABILITIES

JUMP_KEYS=(pg.K_SPACE,pg.K_UP,pg.K_w)

class Game:
    def __init__(self,save_path=None,asset_dir=None,renderer="auto"):
        pg.mixer.pre_init(22050,-16,1,512);pg.init()
        self.presenter=Presenter(os.environ.get("MARIO_RUNNER_RENDERER",renderer))
        self.window=pg.display.get_surface()
        pg.display.set_caption("Mario Runner — One Adventure")
        self.canvas=pg.Surface((WIDTH,HEIGHT));self.world_canvas=self.canvas.copy()
        self.interface_canvas=pg.Surface((WIDTH,HEIGHT),pg.SRCALPHA)
        self.protection_canvas=self.canvas.copy()
        self.assets=Assets(asset_dir);self.save=SaveData(save_path)
        self.audio=Audio(0 if self.save.muted else self.save.volume)
        self.scene=Scene(self.assets);self.ui=UI(self.assets);self.world=World()
        self.state="menu";self.settings_from="menu";self.pause_from="playing"
        self.running=True;self.accumulator=0.;self.hurt_time=0.;self.result_time=0.
        self.toast="";self.toast_time=0.;self.retrying=False;self.practice=False
        self.clock=pg.time.Clock();self.settings_page=0;self.remapping=""
        self.practice_end=0;self.iris_time=0.;self.quality=Quality()
        self.iris=pg.Surface((WIDTH,HEIGHT),pg.SRCALPHA)
        self.shaken=pg.Surface((WIDTH,HEIGHT));self.shaken_mask=self.shaken.copy()
        self.draw()

    def transition(self,state):
        if state!="playing":self.iris_time=0.
        if state!=self.state and state not in ("paused","settings","hurt") and self.state not in ("paused","settings","hurt"):
            self.presenter.begin_transition(self.save.reduced_motion)
        self.state=state;self.ui.selected=0;self.accumulator=0
        self.draw()

    def start_level(self,index,resume=None,base=0,internal=False):
        if not 0<=index<4 or (index and not internal and not (resume and resume.get("level")==index)):
            return False
        self.world=World(index,resume,base)
        if not self.practice:self.world.ghost=Ghost(self.save.path.parent/f"ghost-{index}.json",index)
        self.scene.particles.clear();self.scene.decor_distance=self.world.distance
        self.hurt_time=0;self.toast_time=0;self.result_time=0
        self.retrying=bool(resume and resume.get("checkpoint"))
        if not self.practice:
            self.save.resume=self.world.checkpoint or self.world.snapshot(False)
            self.save.write()
        self.transition("intro");return True

    def continue_game(self):
        self.practice=False
        r=self.save.resume
        self.start_level(r["level"],r,r.get("base",0)) if r else self.start_level(0)

    def retry(self):
        checkpoint=self.world.checkpoint or {"level":self.world.level_index,"base":self.world.base_score,"run_id":self.world.run_id}
        checkpoint=dict(checkpoint,retries=self.world.retries+1)
        self.start_level(self.world.level_index,checkpoint,self.world.base_score,True)

    def action(self,action):
        if not action:return
        self.audio.play("select")
        if action=="continue":self.continue_game()
        elif action=="new":
            self.transition("confirm" if self.save.resume else "new")
            if self.state=="new":self.action("new_confirm")
        elif action=="new_confirm":
            self.practice=False;self.start_level(0)
        elif action=="begin":self.transition("playing")
        elif action in ("retry","restart"):
            if not self.world.victory and self.state not in ("results",):self.retry()
        elif action=="skip" and self.state=="victory":self.show_results()
        elif action=="next" and self.state=="results":
            if self.practice:self.transition("practice")
            elif self.world.level_index<3:self.continue_game()
            else:self.transition("records")
        elif action=="menu":
            self.save.write();self.transition("menu")
        elif action in ("records","cosmetics","practice"):self.transition(action)
        elif action.startswith("practice:"):
            _,index,section=action.split(":");index=int(index);section=int(section)
            starts=(0,6300,10800)
            if 0<=index<4 and 0<=section<3 and self.save.encountered[index]>starts[section]+1:
                self.practice=True;self.practice_end=min(LEVELS[index].length,starts[section]+2400)
                self.start_level(index,{"level":index,"checkpoint":True,"distance":starts[section]},0,True)
        elif action=="pause" and self.state in ("playing","victory","results"):
            self.world.player.holding_jump=False;self.world.player.buffer=0
            self.pause_from=self.state;self.transition("paused")
        elif action=="resume":self.transition(self.pause_from)
        elif action=="settings":
            self.settings_from=self.state;self.settings_page=0;self.transition("settings")
        elif action=="back":
            self.remapping="";self.save.write()
            self.transition(self.settings_from if self.state=="settings" else "menu")
        elif action=="settings_page":self.settings_page=(self.settings_page+1)%3
        elif action=="volume":self.save.volume=(round(self.save.volume*4)+1)%5/4
        elif action=="music":self.save.music_volume=(round(self.save.music_volume*4)+1)%5/4
        elif action=="mute":self.save.muted=not self.save.muted
        elif action=="motion":self.save.reduced_motion=not self.save.reduced_motion
        elif action=="graphics":self.save.enhanced_effects=not self.save.enhanced_effects
        elif action=="bloom":self.save.bloom=(round(self.save.bloom*4)+1)%5/4
        elif action in ("heat","particles","ghost","shake"):setattr(self.save,action,not getattr(self.save,action))
        elif action.startswith("remap:"):self.remapping=action.split(":")[1]
        elif action.startswith("outfit:"):
            item=action.split(":")[1]
            if item in self.save.cosmetics:self.save.outfit=item
        elif action=="quit":self.running=False
        self.audio.music_volume(0 if self.save.muted else self.save.music_volume)
        self.audio.volume=0 if self.save.muted else self.save.volume
        if self.state=="settings" or action.startswith("outfit:"):self.save.write()
        self.draw()

    def logical_mouse(self,point):
        self.window=pg.display.get_surface()
        width,height=self.window.get_size()
        scale=max(.01,min(width/WIDTH,height/HEIGHT))
        return ((point[0]-(width-WIDTH*scale)/2)/scale,(point[1]-(height-HEIGHT*scale)/2)/scale)

    def handle(self,event):
        if event.type==pg.QUIT:self.running=False
        elif event.type==pg.WINDOWFOCUSLOST and self.state in ("playing","victory","results"):
            self.action("pause")
        elif event.type==pg.KEYDOWN:
            if getattr(event,"repeat",False):return
            if self.remapping:
                other={getattr(self.save,name) for name in ("attack_key","jump_key","context_key","reserve_key") if name!=self.remapping}
                if event.key not in (*other,pg.K_ESCAPE,pg.K_p,pg.K_m,pg.K_F11,pg.K_UP,pg.K_w):
                    setattr(self.save,self.remapping,event.key);self.remapping="";self.save.write()
                elif event.key==pg.K_ESCAPE:self.remapping=""
                self.draw();return
            if event.key==pg.K_m:self.save.muted=not self.save.muted;self.audio.volume=0 if self.save.muted else self.save.volume;self.save.write()
            elif event.key==pg.K_F11:self.presenter.toggle_fullscreen();self.window=pg.display.get_surface()
            elif self.state=="playing":
                if event.key==self.save.attack_key:self.world.attack()
                elif event.key==self.save.reserve_key:self.world.abilities.swap()
                elif event.key==self.save.context_key:self.world.context()
                elif event.key in (self.save.jump_key,pg.K_UP,pg.K_w):self.world.player.request_jump()
                elif event.key in (pg.K_ESCAPE,pg.K_p):self.action("pause")
            elif self.state=="victory":
                if event.key in (pg.K_SPACE,pg.K_RETURN):self.action("skip")
                elif event.key in (pg.K_ESCAPE,pg.K_p):self.action("pause")
            elif self.state=="hurt":return
            elif event.key==pg.K_ESCAPE:
                self.action("resume" if self.state=="paused" else "back" if self.state=="settings" else "menu")
            elif self.state=="paused" and event.key==pg.K_p:self.action("resume")
            elif event.key in (pg.K_DOWN,pg.K_s,pg.K_RIGHT,pg.K_TAB):self.ui.navigate(1)
            elif event.key in (pg.K_UP,pg.K_w,pg.K_LEFT):self.ui.navigate(-1)
            elif event.key in (pg.K_RETURN,pg.K_KP_ENTER):self.action(self.ui.activate())
            elif event.key==pg.K_SPACE:
                self.action({"menu":"continue" if self.save.resume else "new","intro":"begin","gameover":"retry","results":"next"}.get(self.state))
            elif event.key==pg.K_r and self.state in ("paused","gameover"):self.action("retry")
        elif event.type==pg.KEYUP and event.key in (self.save.jump_key,pg.K_UP,pg.K_w) and self.state=="playing":self.world.player.release_jump()
        elif event.type==pg.MOUSEMOTION:self.ui.hovered(self.logical_mouse(event.pos))
        elif event.type==pg.MOUSEBUTTONDOWN and event.button==3 and self.state=="playing":self.world.attack()
        elif event.type==pg.MOUSEBUTTONDOWN and event.button==2 and self.state=="playing":self.world.context()
        elif event.type==pg.MOUSEWHEEL and self.state=="playing":self.world.abilities.swap()
        elif event.type==pg.MOUSEBUTTONDOWN and event.button==1:
            pos=self.logical_mouse(event.pos);action=self.ui.hovered(pos)
            if action:self.action(action)
            elif self.state=="playing" and 0<=pos[0]<WIDTH and 0<=pos[1]<HEIGHT:self.world.player.request_jump()
        elif event.type==pg.MOUSEBUTTONUP and event.button==1 and self.state=="playing":self.world.player.release_jump()

    def show_results(self):
        self.world.finished=True
        self.result_time=0;self.transition("results")

    def update(self,dt):
        if self.state in ("menu","intro","records","cosmetics","practice","confirm"):
            self.scene.update(dt,35,self.save.reduced_motion);return
        if self.state=="hurt":
            self.hurt_time+=dt
            if self.hurt_time>=.55:self.transition("gameover")
            return
        if self.state=="victory":
            self.scene.update(dt,0,self.save.reduced_motion)
            self.world.victory.update(dt,self.world.player,self.save.reduced_motion)
            if self.world.victory.phase=="done":self.show_results()
            return
        if self.state=="results":
            if self.practice:return
            self.result_time+=dt
            if self.result_time>=6 and self.world.level_index<3:self.action("next")
            return
        if self.state!="playing":return
        if self.iris_time>0:
            self.iris_time=max(0,self.iris_time-dt);return
        self.toast_time=max(0,self.toast_time-dt)
        for name,x,y in self.world.update(dt,self.assets):
            if name.startswith("pickup:"):
                self.audio.play(name.split(":")[1])
                self.toast=name.split(":")[1].upper()+" READY  /  X TO ATTACK";self.toast_time=2.5
                continue
            if name.startswith("score:"):
                self.scene.popup(x,y,"+"+name.split(":")[1])
                continue
            self.audio.play(name)
            if name=="pipe" and not self.save.reduced_motion:self.iris_time=.3
            if name in ("stomp","damage") and self.save.shake and not self.save.reduced_motion:self.scene.shake_time=.14
            if not self.save.reduced_motion and self.save.particles:
                self.scene.burst(x,y,MINT if name in ("double","checkpoint") else GOLD,18 if name=="stomp" else 10)
            if name=="checkpoint":
                if not self.practice:
                    self.save.resume=self.world.checkpoint.copy();self.save.write()
                self.toast="CHECKPOINT SAVED";self.toast_time=2.5
            elif name=="hit":self.hurt_time=0;self.transition("hurt")
            elif name=="finish":
                if self.save.outfit=="confetti" and self.save.particles and not self.save.reduced_motion:
                    for color in (GOLD,MINT,(245,139,168)):self.scene.burst(self.world.player.x,GROUND-180,color,14)
                if not self.practice:
                    self.world.result.update(self.save.finish(self.world.level_index,self.world.score,self.world.stage_score,f"{self.world.run_id}:{self.world.level_index}",sorted(self.world.challenges)))
                    if self.world.full_run and self.world.result.get("improvement",0)>0:
                        self.world.recorder.save(self.save.path.parent/f"ghost-{self.world.level_index}.json",self.world.level_index,self.world.stage_score)
                self.transition("victory")
        if self.practice and self.world.distance>=self.practice_end and self.state=="playing":
            self.world.result={};self.show_results()
        if not self.practice:self.save.encountered[self.world.level_index]=max(self.save.encountered[self.world.level_index],self.world.distance)
        if self.state=="playing":self.scene.update(dt,self.world.speed,self.save.reduced_motion)

    def backdrop(self,menu=False):
        self.scene.backdrop(self.canvas,LEVELS[0] if menu else self.world.level,self.scene.decor_distance if menu else self.world.distance,self.save.reduced_motion)

    def menu(self):
        s,u=self.canvas,self.ui;self.backdrop(True);s.blit(self.scene.tint,(0,0))
        u.panel(s,(38,30,454,454),244)
        u.text(s,"ONE ADVENTURE / FOUR WORLDS",(66,53),20,MINT)
        u.text(s,"MARIO",(62,85),60,CREAM,True);u.text(s,"RUNNER",(62,149),60,GOLD,True)
        u.text(s,"Find your rhythm. Keep the combo.",(66,222),23)
        buttons=[]
        if self.save.resume:buttons.append(("CONTINUE","continue"))
        buttons.extend((("NEW GAME","new"),("RECORDS & COSMETICS","records"),("SETTINGS","settings"),("QUIT","quit")))
        for i,(label,action) in enumerate(buttons):u.button(s,label,action,(66,263+i*40,398,32),i==0)
        for i,level in enumerate(LEVELS):
            x=525+i%2*209;y=57+i//2*171
            s.blit(self.assets.thumbnails[level.biome],(x,y));pg.draw.rect(s,level.accent,(x,y,198,118),2)
            u.panel(s,(x,y+88,198,30));u.text(s,f"{i+1} / {level.subtitle}",(x+8,y+97),18,level.accent)
        u.text(s,f"CAMPAIGN BEST  {self.save.best:,}",(540,417),25,GOLD)
        u.text(s,"Grasslands > Caves > Sky > Castle",(540,453),21)
        u.text(s,"SPACE / CLICK  Jump     X / RIGHT CLICK  Ability     P  Pause",(480,513),21,center=True)

    def records(self):
        s,u=self.canvas,self.ui;self.backdrop(True);s.blit(self.scene.tint,(0,0))
        u.panel(s,(45,28,870,450),245)
        u.text(s,"YOUR ADVENTURE",(480,67),36,GOLD,True,True)
        for i,l in enumerate(LEVELS):
            y=120+i*62
            u.text(s,f"0{i+1}  {l.subtitle}",(80,y),25,l.accent)
            u.text(s,f"{self.save.stage_bests[i]:,}  /  {self.save.medals[i]}",(488,y),25)
        u.text(s,f"BEST CAMPAIGN {self.save.best:,}    {rank(self.save.best)}",(80,383),25,GOLD)
        u.text(s,f"Legacy best: {self.save.legacy.get('best',0):,}  /  previous scoring rules",(80,425),21)
        u.button(s,"COSMETICS","cosmetics",(70,493,252,34))
        u.button(s,"PRACTICE","practice",(354,493,252,34))
        u.button(s,"BACK","menu",(638,493,252,34))

    def cosmetics(self):
        s,u=self.canvas,self.ui;self.backdrop(True);s.blit(self.scene.tint,(0,0));u.panel(s,(44,28,872,440),246)
        u.text(s,"MAKE IT YOUR RUN",(480,69),34,GOLD,True,True)
        items=(("classic","CLASSIC","Always available"),("ice","AQUA","Silver medal"),("sunset","SUNSET","Gold medal"),("trail","COMET TRAIL","Any challenge"),("confetti","CELEBRATION","Finish campaign"))
        for i,(item,label,requirement) in enumerate(items):
            x=68+i*168
            u.text(s,label,(x+75,133),21,GOLD,center=True)
            image=self.assets.player(self.world.player,self.scene.time,True,form="classic",outfit=item)
            s.blit(image,(x+42,174))
            if item=="trail":
                for j in range(5):pg.draw.rect(s,MINT,(x+12-j*3,222+j*4,4,4))
            if item=="confetti":
                for j in range(9):pg.draw.rect(s,(236,125+j*8,113),(x+20+j*13,202+j%3*14,4,4))
            unlocked=item in self.save.cosmetics
            u.text(s,requirement,(x+75,290),19,MINT if unlocked else (153,163,180),center=True)
            if unlocked:u.button(s,"EQUIPPED" if self.save.outfit==item else "EQUIP",f"outfit:{item}",(x,340,150,40))
            else:u.text(s,"LOCKED",(x+75,362),23,center=True)
        u.text(s,"Outfits and effects are cosmetic. Their collision body is identical.",(480,430),23,center=True)
        u.button(s,"BACK TO RECORDS","records",(330,486,300,38),True)

    def practice_screen(self):
        s,u=self.canvas,self.ui;self.backdrop(True);s.blit(self.scene.tint,(0,0));u.panel(s,(44,28,872,438),247)
        u.text(s,"PRACTICE YOUR RHYTHM",(480,66),31,GOLD,True,True)
        u.text(s,"Encountered sections only / no records, rewards or campaign changes",(480,107),23,MINT,center=True)
        for index,level in enumerate(LEVELS):
            y=153+index*72;u.text(s,level.subtitle,(70,y+13),22,level.accent)
            for section,(label,start) in enumerate((("OPENING",0),("MIDPOINT",6300),("FINALE",10800))):
                x=300+section*194
                if self.save.encountered[index]>start+1:u.button(s,label,f"practice:{index}:{section}",(x,y,176,40))
                else:u.text(s,"UNEXPLORED",(x+88,y+23),20,(137,150,171),center=True)
        u.button(s,"BACK TO RECORDS","records",(330,486,300,38),True)

    def hud(self):
        s,u,w=self.canvas,self.ui,self.world
        u.panel(s,(16,14,232,82));u.text(s,f"{w.level_index+1:02} / {w.level.subtitle}",(30,24),19,w.level.accent)
        u.text(s,f"{w.score:06d}",(30,48),31,CREAM,True)
        u.panel(s,(265,14,434,82))
        u.text(s,f"{w.scoring.multiplier}x COMBO",(281,25),24,GOLD)
        pg.draw.rect(s,(61,76,93),(282,55,180,6))
        pg.draw.rect(s,GOLD if w.scoring.remaining>1.2 else (255,150,120),(282,55,int(180*w.scoring.remaining/4.5),6))
        target=next((v for v in MEDALS if v>w.stage_score),None)
        u.text(s,f"{target-w.stage_score:,} TO {medal(target)}" if target else "GOLD MEDAL",(480,31),20,MINT)
        pg.draw.rect(s,(61,76,93),(282,76,398,5));pg.draw.rect(s,w.level.accent,(282,76,int(398*w.progress),5))
        a=w.abilities
        active=a.equipped.upper() or "SMALL"
        status=f"{active}  /  RESERVE: {a.reserve.upper() or '-'}"
        if a.star>0:status+=f"   STAR {a.star:.1f}s"+("  ENDING" if a.star<2 else "")
        if a.mega>0:status+=f"   MEGA {a.mega:.1f}s"
        if a.definition and a.definition.projectile:status+=f"   SHOTS {sum(p.life>0 for p in w.projectiles)}/{1 if a.definition.projectile=='boomerang' else 3}"
        u.text(s,status,(24,465),21,MINT)
        u.text(s,f"RED {len(w.red_ids)}/6",(790,103),21,(255,161,148))
        clean="CLEAN" if not w.damage_count and not w.retries else "RETRY FOR CLEAN"
        u.text(s,clean,(790,129),17,MINT if clean=="CLEAN" else GOLD)
        u.button(s,"II PAUSE","pause",(780,17,160,37))
        u.text(s,f"COINS {w.coins_collected:02}",(790,70),21,GOLD)
        u.panel(s,(16,493,928,32));u.text(s,f"{pg.key.name(self.save.jump_key).upper()} / W  Jump     {pg.key.name(self.save.attack_key).upper()}  Attack     {pg.key.name(self.save.reserve_key).upper()}  Reserve     {pg.key.name(self.save.context_key).upper()}  Pipe / Context",(480,510),21,center=True)
        warning=self.scene.warning(w)
        if warning and self.state=="playing":
            u.panel(s,(280,111,470,30));u.text(s,warning,(515,127),21,w.level.accent,center=True)
        if self.toast_time>0:
            u.panel(s,(285,153,390,33));u.text(s,self.toast,(480,171),23,MINT,center=True)

    def modal(self):
        s,u,w=self.canvas,self.ui,self.world;s.blit(self.scene.tint,(0,0));u.panel(s,(177,87,606,377),248)
        if self.state=="intro":
            u.text(s,f"WORLD {w.level_index+1} / {w.level.subtitle}",(480,120),24,w.level.accent,center=True)
            u.text(s,w.level.name.upper(),(480,166),28,CREAM,True,True)
            lines=self.wrap(w.level.lesson,510,24)
            for i,line in enumerate(lines):u.text(s,line,(480,217+i*27),24,center=True)
            u.text(s,"Checkpoint restored." if self.retrying else "Midpoint and finale checkpoints save your adventure.",(480,314),23,MINT,center=True)
            u.button(s,"LET'S GO / SPACE","begin",(227,351,506,46),True)
            u.button(s,"MAIN MENU","menu",(337,414,286,30))
        elif self.state=="paused":
            u.text(s,"TAKE A BREATHER",(480,140),31,GOLD,True,True)
            u.button(s,"RESUME","resume",(227,207,506,44),True)
            u.button(s,"SETTINGS","settings",(227,271,242,40))
            u.button(s,"RESUME" if w.victory else "RETRY CHECKPOINT","resume" if w.victory else "retry",(491,271,242,40))
            u.button(s,"MAIN MENU","menu",(227,337,506,42));u.text(s,"P / ESC  Resume",(480,424),22,MINT,center=True)
        elif self.state=="gameover":
            u.text(s,"ONE MORE TRY?",(480,143),34,GOLD,True,True)
            u.text(s,f"{w.score:,}",(480,208),44,CREAM,True,True)
            u.text(s,"Retry restores score, items and abilities at the checkpoint.",(480,273),22,center=True)
            u.button(s,"RETRY / SPACE","retry",(227,323,506,45),True);u.button(s,"MAIN MENU","menu",(227,394,506,40))
        elif self.state=="results":
            result=w.result or {}
            u.text(s,"PRACTICE COMPLETE" if self.practice else "CAMPAIGN COMPLETE" if w.level_index==3 else "WORLD COMPLETE",(480,125),30,GOLD,True,True)
            u.text(s,f"{medal(w.stage_score)}   /   {w.stage_score:,} POINTS",(480,181),30,CREAM,center=True)
            u.text(s,f"Flag +{result.get('flag',0):,}   Clear +{result.get('clear',0):,}   Clean +{result.get('clean',0):,}",(480,227),22,MINT,center=True)
            comparison=f"New best: +{result.get('improvement',0):,}" if result.get('improvement',0)>0 else "Personal best unchanged"
            u.text(s,f"{comparison}    Total: {w.score:,}",(480,268),25,center=True)
            target=next(((value,label) for value,label in ((16000,"ADVENTURER"),(32000,"EXPERT"),(52000,"SUPERSTAR")) if w.score<value),None)
            rank_text=f"{rank(w.score)} / {target[0]-w.score:,} TO {target[1]}" if target else "SUPERSTAR / TOP RANK"
            detail="Practice leaves your campaign checkpoint intact." if self.practice else rank_text if w.level_index==3 else f"Next: {LEVELS[w.level_index+1].name} / auto in {max(0,6-int(self.result_time))}s"
            u.text(s,detail,(480,307),23,GOLD,center=True)
            u.button(s,"PRACTICE MENU" if self.practice else "RECORDS" if w.level_index==3 else "NEXT WORLD / SPACE","next",(227,351,506,43),True)
            u.button(s,"MAIN MENU","menu",(337,414,286,30))
        elif self.state=="confirm":
            u.text(s,"START A NEW ADVENTURE?",(480,142),26,GOLD,True,True)
            u.text(s,"This replaces your current campaign checkpoint.",(480,219),25,center=True)
            u.text(s,"Your records and cosmetic unlocks stay saved.",(480,258),24,MINT,center=True)
            u.button(s,"KEEP CURRENT ADVENTURE","menu",(227,323,506,43),True)
            u.button(s,"START NEW GAME","new_confirm",(227,391,506,40))

    def settings(self):
        s,u=self.canvas,self.ui;self.backdrop(True);s.blit(self.scene.tint,(0,0));u.panel(s,(108,24,744,493),248)
        u.text(s,"SETTINGS",(480,61),35,GOLD,True,True)
        on=lambda value:"ON" if value else "OFF"
        if self.settings_page==0:
            specs=[(f"SFX VOLUME {int(self.save.volume*100)}%","volume"),(f"MUSIC {int(self.save.music_volume*100)}%","music"),(f"MUTE {on(self.save.muted)}","mute"),(f"REDUCED MOTION {on(self.save.reduced_motion)}","motion"),("REMAP CONTROLS ON THIRD PAGE","settings_page")]
        elif self.settings_page==1:
            specs=[(f"ENHANCED EFFECTS {on(self.save.enhanced_effects)}","graphics"),(f"BLOOM {int(self.save.bloom*100)}%","bloom"),(f"HEAT DISTORTION {on(self.save.heat)}","heat"),(f"PARTICLES {on(self.save.particles)}","particles"),(f"GHOST {on(self.save.ghost)}","ghost"),(f"CAMERA SHAKE {on(self.save.shake)}","shake")]
        else:
            specs=[(f"{label}: {pg.key.name(getattr(self.save,key)).upper()}",f"remap:{key}") for label,key in (("JUMP","jump_key"),("ATTACK","attack_key"),("CONTEXT / PIPE","context_key"),("RESERVE","reserve_key"))]
        for i,(label,action) in enumerate(specs):u.button(s,label,action,(146,99+i*49,668,38))
        text="Press a key (ESC cancels). P, M, F11, UP, W reserved." if self.remapping else "GPU active" if self.presenter.accelerated else "Software renderer / all gameplay available"
        u.text(s,text,(480,415),21,MINT,center=True)
        u.button(s,"NEXT SETTINGS PAGE","settings_page",(146,452,320,40));u.button(s,"BACK","back",(494,452,320,40),True)

    def wrap(self,text,width,size):
        lines=[""]
        for word in text.split():
            candidate=(lines[-1]+" "+word).strip()
            if self.assets.font(size).size(candidate)[0]>width:lines.append(word)
            else:lines[-1]=candidate
        return lines

    def draw(self):
        self.scene.reduced=self.save.reduced_motion
        self.scene.quality=self.quality.level
        self.scene.outfit=self.save.outfit;self.scene.ghost_visible=self.save.ghost;self.scene.atmosphere=self.save.particles
        final=self.canvas;self.ui.begin();self.interface_canvas.fill((0,0,0,0));self.protection_canvas.fill((0,0,0))
        screens={"menu":self.menu,"records":self.records,"settings":self.settings,"cosmetics":self.cosmetics,"practice":self.practice_screen}
        if self.state in screens:
            screens[self.state]();self.world_canvas.blit(final,(0,0))
        else:
            self.backdrop();self.scene.actors(self.canvas,self.world,idle=self.state in ("intro","confirm"),hurt_time=self.hurt_time if self.state in ("hurt","gameover") else None)
            self.world_canvas.blit(final,(0,0));protect_actors(self.protection_canvas,self.world)
            if self.scene.shake_time>0 and self.save.shake and not self.save.reduced_motion:
                offset=2 if int(self.scene.shake_time*80)%2 else -2
                self.shaken.blit(self.world_canvas,(0,0));self.world_canvas.blit(self.shaken,(offset,0))
                self.shaken_mask.blit(self.protection_canvas,(0,0));self.protection_canvas.blit(self.shaken_mask,(offset,0))
            self.canvas=self.interface_canvas;self.hud()
            if self.state=="victory":
                self.ui.text(self.canvas,"WORLD CLEAR!  SPACE / ENTER  Skip celebration",(480,220),28,GOLD,center=True)
                self.ui.button(self.canvas,"SKIP","skip",(760,445,168,34))
            elif self.state not in ("playing","hurt"):
                self.ui.begin();self.modal()
            else:
                if self.state=="hurt":self.ui.begin()
            if self.iris_time>0 and not self.save.reduced_motion:
                self.iris.fill((9,19,31,255))
                pg.draw.circle(self.iris,(0,0,0,0),(150,GROUND),int((1-self.iris_time/.3)*1200))
                self.interface_canvas.blit(self.iris,(0,0))
            self.canvas=final;final.blit(self.world_canvas,(0,0));final.blit(self.interface_canvas,(0,0))
        if self.save.error:
            self.ui.text(self.interface_canvas,"Save unavailable; progress is kept for this session.",(480,480),21,GOLD,center=True)
            final.blit(self.interface_canvas,(0,0))

    def present(self):
        self.presenter.bloom=self.save.bloom;self.presenter.heat=self.save.heat
        self.window=pg.display.get_surface()
        active=self.state not in ("menu","records","settings","cosmetics","practice")
        self.presenter.present(self.canvas,self.world_canvas,self.interface_canvas,self.protection_canvas,self.world.level.biome,self.scene.time,environment_lights(self.world,self.scene),self.save.enhanced_effects and active,self.save.reduced_motion)

    def run(self,frames=None):
        count=0
        while self.running and (frames is None or count<frames):
            dt=min(self.clock.tick(FPS)/1000,.1);self.presenter.tick(dt,self.save.reduced_motion)
            for event in pg.event.get():self.handle(event)
            self.accumulator+=dt
            while self.accumulator>=STEP:
                self.accumulator-=STEP;self.update(STEP)
            started=time.perf_counter();self.draw();self.present()
            self.quality.update(time.perf_counter()-started,dt);count+=1
        self.save.write()

def main():
    parser=argparse.ArgumentParser(description="Mario Runner — One Adventure")
    parser.add_argument("--frames",type=int);parser.add_argument("--renderer",choices=("auto","software","opengl"),default="auto")
    args=parser.parse_args();game=None
    try:
        game=Game(renderer=args.renderer);game.run(args.frames)
    finally:
        if game:game.presenter.close()
        pg.quit()
