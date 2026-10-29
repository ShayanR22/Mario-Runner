"""Editable pixel art source. All coordinates are on a 32 x 40 source grid.
Exported PNG sheets are used in normal play; these functions also provide fallbacks.
"""
import math
import pygame as pg

O = (31,34,55)
RED = (219,51,62)
RHI = (255,99,92)
BLUE = (39,92,175)
BHI = (74,151,224)
SKIN = (255,191,120)
SHADE = (218,128,76)
WHITE = (255,249,218)
BROWN = (103,55,40)
GOLD = (255,208,80)

PLAYER_CLIPS = {"idle":(4,.18,True), "run":(6,.085,True),
                "jump":(2,.12,False), "double":(4,.06,False),
                "fall":(2,.14,True), "land":(3,.06,False), "damage":(3,.12,False)}
PLAYER_CLIPS.update({name:(3,.10,True) for name in ("attack","transform","flag","climb","glide","dive")})
ENEMY_CLIPS = {name:(4,.13,True) for name in
              ("goomba","koopa","buzzy","paratroopa","bullet","drybones","fire","pipe","shell","bones","vent")}
PROP_CLIPS = {"coin":(6,.09,True),"flag":(4,.15,True),"checkpoint":(4,.15,True),
              "crystal":(4,.2,True),"cloud":(1,1,True)}

def surface(size=(32,40)):
    return pg.Surface(size,pg.SRCALPHA)

def box(s,color,rect,outline=True):
    if outline:
        pg.draw.rect(s,O,rect)
        x,y,w,h=rect
        pg.draw.rect(s,color,(x+1,y+1,max(1,w-2),max(1,h-2)))
    else:
        pg.draw.rect(s,color,rect)

def limb(s,a,b,color,width=4):
    pg.draw.line(s,O,a,b,width+2)
    pg.draw.line(s,color,a,b,width)

def mario(pose,frame):
    s=surface()
    run=pose=="run"
    crouch=3-frame if pose=="land" else 0
    bob=(frame%2 if pose in ("idle","run") else 0)+max(0,crouch)
    lean=-2 if pose=="damage" else 0
    # Legs and shoes are drawn first; the visual sole is always row 37.
    if run:
        strides=((-5,3),(0,0),(4,-4),(5,-3),(0,0),(-4,4))
        a,b=strides[frame%6]
        feet=((12+a,36),(20+b,32 if frame%3==2 else 36))
    elif pose in ("jump","double","fall","damage"):
        feet=((9,34),(23,31 if pose in ("jump","double") else 35))
    else:
        feet=((12,36),(21,36))
    for hip,foot in zip(((13,30),(20,30)),feet):
        limb(s,hip,foot,BLUE,5)
        box(s,BROWN,(foot[0]-3,foot[1]-2,8,4))
        box(s,(174,102,56),(foot[0]-2,foot[1]-1,5,1),False)
    # Arms have deliberately different silhouettes in every animation.
    if pose in ("attack","climb","flag","glide","dive","transform"):
        hands=((5,18+frame%2*3),(28,21-frame%2*3))
    elif pose in ("jump","double"):
        hands=((6,23-frame%2*2),(25,10+frame%2*3))
    elif pose=="fall":
        hands=((5,23+frame),(27,23-frame))
    elif pose=="damage":
        hands=((5,17),(27,16))
    elif run:
        hands=((7,25+frame%3*2),(25,29-frame%3*3))
    else:
        hands=((7,29+bob),(25,29+bob))
    for shoulder,hand in zip(((11,24+bob),(22,24+bob)),hands):
        limb(s,shoulder,hand,RED,4)
        box(s,WHITE,(hand[0]-2,hand[1]-2,5,5))
    box(s,RED,(9+lean,22+bob,15,11))
    box(s,BLUE,(12+lean,26+bob,11,8))
    box(s,BHI,(14+lean,27+bob,3,5),False)
    box(s,BLUE,(11+lean,23+bob,3,7),False)
    box(s,BLUE,(20+lean,23+bob,3,7),False)
    box(s,GOLD,(13+lean,27+bob,2,2),False)
    box(s,GOLD,(20+lean,27+bob,2,2),False)
    # Face: blue eye, large nose, sideburn, ear and stepped moustache.
    head=surface()
    box(head,SKIN,(9,9,15,14))
    box(head,SHADE,(10,19,11,3),False)
    box(head,SKIN,(21,13,7,6))
    box(head,BROWN,(8,10,5,9),False)
    box(head,SKIN,(10,14,4,5),False)
    box(head,SHADE,(11,15,1,2),False)
    box(head,WHITE,(19,10,3,6),False)
    box(head,(30,67,113),(21,11,1,4),False)
    box(head,BROWN,(17,18,9,3),False)
    box(head,BROWN,(16,17,3,3),False)
    box(head,SKIN,(17,21,5,1),False)
    pg.draw.polygon(head,O,[(8,9),(8,5),(11,2),(20,2),(23,5),(23,7),(28,7),(28,10),(8,10)])
    pg.draw.polygon(head,RED,[(9,8),(9,5),(12,3),(20,3),(22,5),(22,8),(27,8),(27,9),(9,9)])
    box(head,RHI,(12,4,7,2),False)
    box(head,WHITE,(17,4,5,5),False)
    box(head,RED,(18,5,1,3),False)
    box(head,RED,(20,5,1,3),False)
    box(head,RED,(19,6,1,1),False)
    s.blit(head,(lean,bob))
    if pose in ("jump","double"):
        hand=(28,6+frame%2*3)
        limb(s,(23,24+bob),hand,RED,3)
        box(s,WHITE,(hand[0]-2,hand[1]-2,5,5))
    if pose=="damage":
        box(s,WHITE,(3+frame,13+frame,4,4))
    return s

def enemy(name,frame):
    s=surface()
    step=frame%2
    if name=="goomba":
        pg.draw.polygon(s,O,[(4,30),(7,22),(11,19),(21,19),(25,23),(28,30),(24,33),(8,33)])
        pg.draw.polygon(s,(174,95,53),[(6,29),(9,23),(13,20),(20,20),(24,24),(26,29),(23,31),(9,31)])
        box(s,(221,155,83),(11,21,9,3),False)
        box(s,(243,197,133),(10,30,12,6))
        for x in (10,19):
            box(s,WHITE,(x,25,4,6),False)
            box(s,O,(x+1,27,2,4),False)
        pg.draw.line(s,O,(8,24),(14,26),2)
        pg.draw.line(s,O,(18,26),(24,24),2)
        box(s,BROWN,(6-step,34,9,4))
        box(s,BROWN,(19+step,34,8,4))
    elif name in ("koopa","paratroopa","drybones"):
        bone=name=="drybones"
        skin=(212,216,209) if bone else (245,185,76)
        shell=(110,126,145) if bone else (65,166,87)
        if name=="paratroopa":
            for x,side in ((20,1),(9,-1)):
                pg.draw.polygon(s,O,[(x,26),(x+side*10,15-step*3),(x+side*9,28),(x,31)])
                pg.draw.polygon(s,WHITE,[(x,26),(x+side*8,18-step*3),(x+side*7,27),(x,29)])
                pg.draw.line(s,(170,207,218),(x,28),(x+side*6,22),1)
        pg.draw.ellipse(s,O,(11,20,16,16))
        pg.draw.ellipse(s,WHITE,(12,21,14,14))
        pg.draw.ellipse(s,shell,(14,21,12,12))
        pg.draw.line(s,O,(17,22),(17,31),1)
        pg.draw.line(s,O,(15,26),(24,26),1)
        box(s,skin,(7,22,8,13))
        pg.draw.ellipse(s,O,(4,12,13,15))
        pg.draw.ellipse(s,skin,(5,13,11,13))
        box(s,skin,(2,20,8,5))
        box(s,WHITE if not bone else O,(6,15,5,6),False)
        box(s,O,(6,16,2,4),False)
        box(s,SHADE if not bone else (140,151,160),(4,22,3,1),False)
        box(s,skin,(5+step,34,9,4))
        box(s,skin,(18-step,34,9,4))
        if bone:
            for y in (27,30,33):
                box(s,O,(8,y,5,1),False)
    elif name in ("buzzy","shell"):
        color=(45,73,114) if name=="buzzy" else (66,173,93)
        pg.draw.ellipse(s,O,(5,23,23,13))
        pg.draw.ellipse(s,color,(6,24,21,11))
        pg.draw.ellipse(s,(95,143,182) if name=="buzzy" else (132,220,111),(9,25,11,4))
        box(s,WHITE,(5,33,23,3))
        box(s,BROWN,(4+step,36,9,2),False)
        box(s,BROWN,(20-step,36,8,2),False)
        if name=="buzzy":
            box(s,SKIN,(2,30,7,6))
            box(s,O,(3,31,2,2),False)
        else:
            pg.draw.line(s,O,(17,25),(17,32),1)
    elif name=="bullet":
        box(s,O,(3,23,25,14),False)
        pg.draw.ellipse(s,O,(0,23,12,14))
        box(s,(67,76,99),(4,24,23,11),False)
        box(s,(132,153,173),(7,25,19,2),False)
        box(s,O,(24,24,4,11),False)
        box(s,WHITE,(4,27,6,5),False)
        box(s,O,(4,28,2,3),False)
        box(s,WHITE,(13,31,7,5))
        box(s,(184,200,207),(15,32,1,3),False)
        box(s,GOLD,(28,27,3,6),False)
    elif name=="fire":
        pts=[(6,36),(8,24),(11,29),(12,17),(16,9+step*3),(19,23),(22,19),(25,36)]
        pg.draw.polygon(s,O,pts)
        pg.draw.polygon(s,(237,76,48),[(8,35),(10,25),(13,29),(14,19),(16,13+step*3),(19,27),(22,23),(23,35)])
        pg.draw.polygon(s,(255,174,58),[(11,35),(14,26),(16,22),(18,30),(20,29),(21,35)])
        pg.draw.polygon(s,WHITE,[(14,35),(16,29),(19,35)])
        box(s,(101,93,110),(5,36,23,2),False)
    elif name in ("vent","bones"):
        if name=="vent":
            box(s,(93,87,110),(5,35,23,3))
            for x in (8,13,18,23):
                box(s,(245,137,74),(x,36,2,1),False)
        else:
            for x,y,w in ((5,34,8),(11,32,7),(17,35,9),(21,31,6)):
                box(s,(212,216,209),(x,y,w,3))
            box(s,O,(23,32,2,1),False)
    elif name=="pipe":
        box(s,(37,107,86),(5,18,22,20))
        box(s,(68,176,110),(6,19,5,18),False)
        box(s,(139,226,125),(7,19,2,18),False)
        box(s,(27,76,75),(22,19,4,18),False)
        box(s,(37,107,86),(3,15,26,7))
        box(s,(122,210,119),(4,16,20,2),False)
    return s

def prop(name,frame):
    s=surface()
    if name=="coin":
        widths=(8,6,3,2,3,6)
        w=widths[frame%6]
        pg.draw.ellipse(s,(114,67,33),(16-w,19,w*2,19))
        pg.draw.ellipse(s,GOLD,(17-w,19,max(2,w*2-2),17))
        if w>3:
            box(s,WHITE,(14,22,2,10),False)
            box(s,(213,138,41),(18,23,2,9),False)
    elif name in ("flag","checkpoint"):
        box(s,(111,91,91),(7,3,3,35))
        box(s,WHITE,(8,3,1,34),False)
        col=(110,225,169) if name=="checkpoint" else GOLD
        pg.draw.polygon(s,O,[(10,4),(27,6+frame%2),(24,18),(10,16)])
        pg.draw.polygon(s,col,[(10,5),(25,7+frame%2),(23,16),(10,15)])
        box(s,WHITE,(16,8,4,4),False)
        box(s,(123,140,154),(3,36,11,2),False)
    elif name=="crystal":
        pg.draw.polygon(s,O,[(8,36),(6,20),(13,8),(20,20),(23,32),(20,37)])
        pg.draw.polygon(s,(59,156,205),[(9,34),(8,21),(13,11),(18,21),(21,32),(19,35)])
        pg.draw.polygon(s,(120,239,242),[(9,21),(13,11),(13,34)])
        box(s,WHITE,(11+frame%2,18,2,6),False)
    else:
        for rect in ((2,28,28,8),(6,24,21,9),(12,20,10,12)):
            box(s,(222,241,245),rect,False)
        box(s,WHITE,(6,26,19,3),False)
    return s

def tile(biome):
    s=surface((64,32))
    palettes={
      "grass":((122,80,60),(84,53,52),(71,150,84),(161,219,115)),
      "cave":((52,58,87),(34,39,65),(86,96,128),(144,163,193)),
      "sky":((142,113,104),(98,88,102),(234,231,197),(255,250,225)),
      "castle":((66,54,72),(41,34,54),(113,86,98),(185,132,111))}
    base,shadow,top,light=palettes[biome]
    s.fill(base)
    box(s,top,(0,0,64,5),False)
    box(s,light,(0,0,64,2),False)
    for y in (8,20):
        box(s,shadow,(0,y,64,2),False)
        for x in range(-16 if y==20 else 0,64,32):
            box(s,shadow,(x,y,2,12),False)
            box(s,tuple(min(255,v+16) for v in base),(x+3,y+3,24,1),False)
    if biome=="grass":
        for x in range(0,64,8):
            box(s,top,(x,4,3,3),False)
    if biome=="castle":
        for x in (8,39):
            box(s,(181,87,66),(x,26,5,1),False)
    return s
