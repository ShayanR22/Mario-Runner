"""Cached sheets, masks, backgrounds and fonts, with code-drawn fallbacks."""
import json
import logging
from pathlib import Path
import pygame as pg
from .config import ROOT
from .animation import Clip, player_pose
from . import pixelart
from .form_art import FORMS,transform,icon,recolor

class Assets:
    def __init__(self,directory=None):
        self.directory=Path(directory) if directory else ROOT/"assets"
        self.missing=[]
        self.fonts={}
        self.frames={}
        self.masks={}
        self.clips={}
        self.backgrounds={}
        self.grounds={}
        self.thumbnails={}
        self.body_mask=pg.Mask((32,60),fill=True)
        try:
            manifest=json.loads((self.directory/"sheets/manifest.json").read_text())
            if manifest["cell"] != [32,40] or manifest["anchor"] != [16,38]:
                raise ValueError("Incompatible atlas")
        except (OSError,ValueError,KeyError,TypeError):
            manifest=None
        for name,definitions,draw in (("mario",pixelart.PLAYER_CLIPS,pixelart.mario),
                                      ("enemies",pixelart.ENEMY_CLIPS,pixelart.enemy),
                                      ("props",pixelart.PROP_CLIPS,pixelart.prop)):
            try:
                sheet=pg.image.load(str(self.directory/f"sheets/{name}.png")).convert_alpha()
                spec=manifest["sheets"][name]
                self._sheet(name,sheet,spec)
            except (OSError,pg.error,TypeError,KeyError,ValueError):
                self.missing.append(name)
                logging.warning("Missing or invalid %s sheet; using editable pixel-art fallback",name)
                self.frames[name]=[]
                self.clips[name]={}
                for clip,(count,seconds,loop) in definitions.items():
                    ids=[]
                    for i in range(count):
                        ids.append(len(self.frames[name]))
                        self.frames[name].append(pg.transform.scale(draw(clip,i),(64,80)))
                    self.clips[name][clip]=Clip(tuple(ids),seconds,loop)
            self.masks[name]=[pg.mask.from_surface(frame,160) for frame in self.frames[name]]
        # Small Mario has a shorter torso on the same grid and fixed foot anchor.
        small_frames=[]
        for frame in self.frames["mario"]:
            small=pg.Surface((64,80),pg.SRCALPHA)
            small.blit(frame,(0,8),(0,0,64,44))
            small.blit(frame,(0,52),(0,52,64,28))
            small_frames.append(small)
        self.forms={"classic":small_frames}
        self.icons={item:pg.transform.scale(icon(item),(48,60)) for item in FORMS if item not in ("classic",)}
        self.icons["star"]=pg.transform.scale(icon("star"),(48,60))
        for form in FORMS:
            if form=="classic":continue
            self.forms[form]=[pg.transform.scale(transform(pg.transform.scale(frame,(32,40)),form),(64,80)) for frame in self.frames["mario"]]
        self.palettes={}
        self.ghost_frames={}
        for i,biome in enumerate(("grass","cave","sky","castle")):
            try:
                image=pg.image.load(str(self.directory/f"generated/{biome}.png")).convert()
            except (OSError,pg.error):
                self.missing.append(biome)
                image=self.fallback_background(i)
            self.thumbnails[biome]=pg.transform.scale(image,(198,118))
            normal=pg.transform.scale(image,(960,430))
            self.backgrounds[biome]=(normal,pg.transform.flip(normal,True,False))
            try:
                tile=pg.image.load(str(self.directory/f"sheets/ground-{biome}.png")).convert_alpha()
            except (OSError,pg.error):
                tile=pixelart.tile(biome)
            self.grounds[biome]=pg.transform.scale(tile,(128,64))

    def _sheet(self,name,sheet,spec):
        if sheet.get_width()%32 or sheet.get_height()%40:
            raise ValueError("Invalid sheet dimensions")
        frames=[]
        for y in range(0,sheet.get_height(),40):
            for x in range(0,sheet.get_width(),32):
                frames.append(pg.transform.scale(sheet.subsurface((x,y,32,40)),(64,80)))
        clips={}
        for key,clip in spec["clips"].items():
            ids=clip["frames"]
            if not ids or any(type(i)!=int or i<0 or i>=len(frames) for i in ids):
                raise ValueError("Invalid frame index")
            if not .01<=clip["seconds_per_frame"]<=2:
                raise ValueError("Invalid animation timing")
            clips[key]=Clip(tuple(ids),clip["seconds_per_frame"],clip["loop"])
        expected={"mario":pixelart.PLAYER_CLIPS,"enemies":pixelart.ENEMY_CLIPS,"props":pixelart.PROP_CLIPS}[name]
        if set(clips)!=set(expected):
            raise ValueError("Missing animation")
        self.frames[name],self.clips[name]=frames,clips

    def frame_id(self,sheet,clip,time):
        return self.clips[sheet][clip].frame(time)

    def frame(self,sheet,clip,time):
        return self.frames[sheet][self.frame_id(sheet,clip,time)]

    def player(self,player,time,idle=False,hurt_time=None,form="classic",pose=None,outfit="classic"):
        base_pose,age=player_pose(player,time,idle,hurt_time)
        index=self.frame_id("mario",pose or base_pose,age)
        key=(form,index,outfit)
        if key not in self.palettes:
            image=self.forms.get(form,self.forms["classic"])[index]
            if outfit in ("ice","sunset"):
                mapping={pixelart.BLUE:(71,166,181),pixelart.BHI:(147,241,225)} if outfit=="ice" else {pixelart.BLUE:(126,77,159),pixelart.BHI:(209,142,199)}
                image=recolor(image,mapping)
            if form=="mega":
                image=pg.transform.scale(image,(80,100))
            self.palettes[key]=image
        return self.palettes[key]

    def enemy_collision(self,enemy,world):
        index=self.frame_id("enemies",enemy.kind,enemy.age)
        return self.masks["enemies"][index],pg.Rect(round(enemy.x(world))-32,round(enemy.bottom)-76,64,80)

    def font(self,size,title=False):
        key=(size,title)
        if key not in self.fonts:
            try:
                path=str(self.directory/"original/SuperMario256.ttf") if title else None
                self.fonts[key]=pg.font.Font(path,size)
            except (OSError,pg.error):
                self.fonts[key]=pg.font.Font(None,size)
        return self.fonts[key]

    @staticmethod
    def fallback_background(index):
        palettes=(((42,151,196),(153,221,214)),((19,28,60),(57,63,111)),
                  ((66,142,214),(203,229,245)),((31,27,55),(116,59,70)))
        top,bottom=palettes[index]
        image=pg.Surface((480,215))
        for y in range(215):
            t=y/215
            color=tuple(int(a+(b-a)*t) for a,b in zip(top,bottom))
            pg.draw.line(image,color,(0,y),(480,y))
        for x in range(-20,480,90):
            pg.draw.polygon(image,bottom,[(x,215),(x+60,125),(x+120,215)])
        return image
