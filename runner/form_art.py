"""Original code-drawn transformation details on the established 32x40 grid."""
import pygame as pg
from . import pixelart as P
from .abilities import ABILITIES

FORMS=("classic",*ABILITIES,"mega")

def recolor(image,mapping):
    result=image.copy()
    for y in range(result.get_height()):
        for x in range(result.get_width()):
            c=result.get_at((x,y))
            if c.a and tuple(c[:3]) in mapping:result.set_at((x,y),(*mapping[tuple(c[:3])],c.a))
    return result

def transform(image,form):
    c=ABILITIES[form].color if form in ABILITIES else P.RED
    mapping={}
    if form=="fire":mapping={P.RED:P.WHITE,P.RHI:(255,255,246),P.BLUE:(212,65,54),P.BHI:(255,142,79)}
    elif form=="ice":mapping={P.RED:(101,216,249),P.RHI:(204,251,255),P.BLUE:(65,113,211),P.BHI:(143,192,250)}
    elif form in ("cat","tanooki","penguin","boomerang"):
        mapping={P.RED:c,P.RHI:tuple(min(255,v+25) for v in c),P.BLUE:tuple(int(v*.75) for v in c),P.BHI:c}
    s=recolor(image,mapping)
    if form=="cat":
        for x in (8,22):
            pg.draw.polygon(s,P.O,[(x-2,7),(x-2,0),(x+5,5)])
            pg.draw.polygon(s,c,[(x-1,5),(x-1,2),(x+3,5)])
        pg.draw.lines(s,c,False,[(7,29),(3,25),(2,19)],3)
        pg.draw.circle(s,P.GOLD,(19,24),2)
    elif form=="tanooki":
        pg.draw.polygon(s,P.O,[(7,31),(1,31),(0,22),(4,19),(8,25)])
        pg.draw.polygon(s,c,[(6,30),(2,30),(1,23),(4,21),(7,26)])
        for y in (24,28):pg.draw.line(s,P.BROWN,(1,y),(5,y),2)
        for x in (8,22):pg.draw.rect(s,P.BROWN,(x,1,5,5))
    elif form=="cape":
        pg.draw.polygon(s,P.O,[(10,20),(3,23),(0,35),(13,33)])
        pg.draw.polygon(s,P.GOLD,[(9,21),(4,24),(2,33),(12,32)])
    elif form=="penguin":
        pg.draw.ellipse(s,P.WHITE,(12,25,11,9));pg.draw.rect(s,(240,180,61),(21,15,7,3))
    elif form=="boomerang":pg.draw.rect(s,(233,238,250),(9,6,17,2))
    elif form=="mushroom":pg.draw.rect(s,P.GOLD,(19,5,2,3))
    return s

def icon(item,frame=0):
    s=P.surface();c=ABILITIES[item].color if item in ABILITIES else P.GOLD if item=="star" else (166,224,104)
    if item in ("mushroom","mega"):
        pg.draw.rect(s,P.O,(7,24,18,13));pg.draw.rect(s,P.WHITE,(9,25,14,11))
        pg.draw.ellipse(s,P.O,(2,8,28,23));pg.draw.ellipse(s,c,(3,9,26,20))
        for x,y in ((8,18),(15,12),(24,19)):pg.draw.rect(s,P.WHITE,(x-2,y-2,5,5))
    elif item in ("fire","ice","boomerang"):
        pg.draw.rect(s,(75,175,110),(14,20,4,17));pg.draw.ellipse(s,P.O,(3,5,26,24));pg.draw.ellipse(s,c,(5,7,22,20));pg.draw.ellipse(s,P.WHITE,(10,12,13,10))
        if item=="boomerang":pg.draw.lines(s,P.O,False,[(8,22),(18,16),(24,20)],3)
    elif item=="star":
        pg.draw.polygon(s,P.O,[(16,4),(20,14),(31,15),(24,23),(26,35),(16,29),(6,35),(8,23),(1,15),(12,14)])
        pg.draw.polygon(s,c,[(16,7),(19,16),(27,17),(21,23),(23,31),(16,26),(9,31),(11,23),(5,17),(13,16)])
    elif item=="cat":
        pg.draw.polygon(s,P.O,[(4,29),(5,9),(14,16),(23,8),(28,29)])
        pg.draw.polygon(s,c,[(6,27),(7,13),(14,20),(22,12),(26,27)])
        pg.draw.circle(s,P.GOLD,(16,30),5)
    elif item=="tanooki":
        pg.draw.ellipse(s,P.O,(3,11,26,24));pg.draw.ellipse(s,c,(5,13,22,20))
        for x in (8,17,24):pg.draw.line(s,P.BROWN,(x,15),(x-1,31),3)
    elif item=="cape":
        pg.draw.polygon(s,P.O,[(6,35),(10,14),(26,4),(25,24),(16,30)])
        pg.draw.polygon(s,c,[(8,32),(12,15),(24,7),(23,23),(15,28)])
    else:
        pg.draw.ellipse(s,P.O,(5,8,23,28));pg.draw.ellipse(s,c,(7,10,19,24));pg.draw.ellipse(s,P.WHITE,(11,20,12,13))
    if item in ("mushroom","star","mega"):
        for x in (13,19):pg.draw.rect(s,P.O,(x,22,2,5))
    return s
