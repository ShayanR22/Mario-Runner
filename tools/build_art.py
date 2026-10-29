"""Export editable pixel artwork and slice the generated biome atlas."""
import json
import os
from pathlib import Path
import sys
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import pygame as pg
from runner import pixelart
from runner.levels import LEVELS

def build():
    pg.init()
    out=ROOT/"assets"/"sheets"
    out.mkdir(parents=True,exist_ok=True)
    manifest={"cell":[32,40],"anchor":[16,38],"scale":2,"sheets":{}}
    for name,clips,draw in (("mario",pixelart.PLAYER_CLIPS,pixelart.mario),
                           ("enemies",pixelart.ENEMY_CLIPS,pixelart.enemy),
                           ("props",pixelart.PROP_CLIPS,pixelart.prop)):
        count=sum(info[0] for info in clips.values())
        sheet=pg.Surface((8*32,((count+7)//8)*40),pg.SRCALPHA)
        info={}
        index=0
        for clip,(n,seconds,loop) in clips.items():
            ids=[]
            for frame in range(n):
                art=draw(clip,frame)
                sheet.blit(art,((index%8)*32,(index//8)*40))
                ids.append(index)
                index+=1
            info[clip]={"frames":ids,"seconds_per_frame":seconds,"loop":loop}
        pg.image.save(sheet,out/f"{name}.png")
        manifest["sheets"][name]={"file":f"{name}.png","columns":8,"clips":info}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    for level in LEVELS:
        pg.image.save(pixelart.tile(level.biome),out/f"ground-{level.biome}.png")
    source=ROOT/"assets/generated/biomes-source.png"
    if source.exists():
        atlas=pg.image.load(str(source))
        w,h=atlas.get_size()
        for i,level in enumerate(LEVELS):
            rect=pg.Rect((i%2)*(w//2),(i//2)*(h//2),w//2,h//2)
            panel=pg.transform.scale(atlas.subsurface(rect),(480,215))
            pg.image.save(panel,ROOT/f"assets/generated/{level.biome}.png")
    from runner.form_art import FORMS,transform,icon
    base=pg.image.load(str(out/"mario.png"))
    for form in FORMS:
        if form!="classic":
            result=pg.Surface(base.get_size(),pg.SRCALPHA)
            for y in range(0,base.get_height(),40):
                for x in range(0,base.get_width(),32):
                    result.blit(transform(base.subsurface((x,y,32,40)),form),(x,y))
            pg.image.save(result,out/f"form-{form}.png")
    items=(*[f for f in FORMS if f!="classic"],"star")
    icons=pg.Surface((32*len(items),40),pg.SRCALPHA)
    for i,item in enumerate(items):icons.blit(icon(item),(i*32,0))
    pg.image.save(icons,out/"powerups.png")
    (out/"powerups.json").write_text(json.dumps({"cell":[32,40],"items":list(items)},indent=2))
    pg.quit()
    print("Exported new sprite sheets, manifest, seamless ground tiles and biome panels.")

if __name__=="__main__":
    build()
