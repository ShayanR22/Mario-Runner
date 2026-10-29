"""Data-driven transformations. One equipped form, one reserve, timed overlays."""
from dataclasses import dataclass,asdict
from .storage import number
from . import balance as B

@dataclass(frozen=True)
class Ability:
    label: str
    color: tuple
    projectile: str = ""
    melee: str = ""
    cooldown: float = .3
    fall_cap: float = 0
    description: str = ""

ABILITIES={
    "mushroom":Ability("SUPER",(238,85,87),description="Absorbs one hit; safe fixed collision body"),
    "fire":Ability("FIRE",(255,155,66),"fire",description="Bouncing fireballs / 3 active"),
    "ice":Ability("ICE",(110,227,255),"ice",description="Freeze, then attack nearby blocks to kick"),
    "cat":Ability("CAT",(245,204,92),melee="claw",description="Claws; airborne dive; DOWN at marked walls"),
    "tanooki":Ability("TANOOKI",(194,145,99),melee="tail",cooldown=.38,fall_cap=135,description="Tail spin; hold jump to float"),
    "boomerang":Ability("BOOMERANG",(111,183,241),"boomerang",cooldown=.65,description="Returning arc collects coins"),
    "cape":Ability("CAPE",(255,219,89),melee="tail",cooldown=.4,fall_cap=75,description="Long glide; DOWN commits to a fast dive"),
    "penguin":Ability("PENGUIN",(121,163,219),"ice",description="Ice shots; DOWN slides safely on marked ice"),
}
PICKUPS=tuple(ABILITIES)+("star","mega")

@dataclass
class AbilityState:
    equipped: str = ""
    reserve: str = ""
    star: float = 0.
    mega: float = 0.
    grace: float = 0.
    cooldown: float = 0.
    attack_time: float = 0.
    transform_time: float = 0.
    dive: bool = False
    climb: float = 0.
    slide: float = 0.
    uses: int = 0

    @property
    def definition(self):return ABILITIES.get(self.equipped)
    @property
    def invincible(self):return self.star>0 or self.mega>0 or self.grace>0

    def activate(self,item):
        if item=="star":self.star=B.STAR_SECONDS
        elif item=="mega":self.mega=B.MEGA_SECONDS
        elif item in ABILITIES:
            if self.equipped and self.equipped!=item:self.reserve=self.equipped
            self.equipped=item
        else:return False
        self.transform_time=.35
        return True

    def swap(self):
        if self.reserve:
            self.equipped,self.reserve=self.reserve,self.equipped
            self.cooldown=0;self.transform_time=.35;self.dive=False;self.climb=0;self.slide=0

    def damage(self):
        if self.invincible:return False
        if self.equipped:
            self.equipped="";self.grace=B.GRACE;self.dive=False;self.climb=0;self.slide=0
            return True
        return False

    def update(self,dt,player,holding_jump=False):
        for attr in ("star","mega"):
            old=getattr(self,attr);setattr(self,attr,max(0.,old-dt))
            if old>0 and getattr(self,attr)==0:self.grace=max(self.grace,.65)
        for attr in ("grace","cooldown","attack_time","transform_time","slide"):
            setattr(self,attr,max(0.,getattr(self,attr)-dt))
        spec=self.definition
        if spec and spec.fall_cap and holding_jump and player.velocity>spec.fall_cap and not self.dive:
            player.velocity=spec.fall_cap
        if player.grounded:self.dive=False

    def attack(self,world):
        if self.cooldown>0:return False
        spec=self.definition
        if not spec:return False
        if spec.projectile:
            from .projectiles import Projectile
            active=[p for p in world.projectiles if p.life>0]
            limit=1 if spec.projectile=="boomerang" else B.PROJECTILE_LIMIT
            if sum(p.kind==spec.projectile for p in active)>=limit:return False
            world.projectiles.append(Projectile(spec.projectile,world.distance+28,world.player.bottom-30,world.speed+430, -100 if spec.projectile=="fire" else 0))
        if spec.melee:
            self.attack_time=.22
            if self.equipped=="cat" and not world.player.grounded:
                self.dive=True;world.player.velocity=max(650,world.player.velocity)
        self.cooldown=spec.cooldown;self.uses+=1
        return True

    def dump(self):return asdict(self)
    @classmethod
    def load(cls,value):
        if not isinstance(value,dict):return cls()
        state=cls()
        for name in ("equipped","reserve"):
            item=value.get(name);setattr(state,name,item if isinstance(item,str) and item in ABILITIES else "")
        for name in ("star","mega","grace","cooldown","attack_time","transform_time","climb","slide"):
            setattr(state,name,number(value.get(name),0,30))
        state.dive=value.get("dive") is True
        from .storage import integer
        state.uses=integer(value.get("uses"))
        return state
