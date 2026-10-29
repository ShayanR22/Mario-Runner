"""Versioned noninteractive ghosts; validated samples and atomic writes."""
import json,os,tempfile,math
from pathlib import Path
from .balance import PHYSICS_VERSION,SCORING_VERSION
from .levels import LEVELS

REPLAY_VERSION=3

def signature(index):
    level=LEVELS[index]
    return f"{REPLAY_VERSION}:{PHYSICS_VERSION}:{SCORING_VERSION}:{index}:{level.length}:routes4:{','.join(f'{e.at}-{e.kind}' for e in level.encounters)}"

class Recorder:
    def __init__(self):self.frames=[];self.next_time=0.
    def sample(self,world):
        if world.elapsed+1e-8<self.next_time:return
        p=world.player
        from .animation import player_pose
        pose=player_pose(p,world.elapsed)[0]
        a=world.abilities
        if a.climb:pose="climb"
        elif a.dive:pose="dive"
        elif a.attack_time:pose="attack"
        elif a.transform_time:pose="transform"
        elif a.definition and a.definition.fall_cap and p.holding_jump and p.velocity>0:pose="glide"
        self.frames.append([round(world.elapsed,3),round(world.distance,2),round(p.bottom,2),a.equipped,round(p.velocity,1),p.jumps,pose,round(p.x,2)])
        self.next_time=world.elapsed+1/30
        self.frames=self.frames[-12000:]
    def save(self,path,index,score):
        path=Path(path);temporary=None
        try:
            path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as f:
                temporary=Path(f.name);json.dump({'signature':signature(index),'score':score,'frames':self.frames},f)
            os.replace(temporary,path);return True
        except (OSError,ValueError):return False
        finally:
            if temporary and temporary.exists():temporary.unlink()

class Ghost:
    def __init__(self,path,index):
        self.frames=[];self.cursor=0
        try:
            path=Path(path)
            if path.stat().st_size>1800000:return
            data=json.loads(path.read_text());frames=data.get('frames')
            if data.get('signature')!=signature(index) or not isinstance(frames,list) or len(frames)>12000:return
            previous=-1
            from .abilities import ABILITIES
            for f in frames:
                if not isinstance(f,list) or len(f)!=8:return
                if any(type(f[i]) not in (int,float) or not math.isfinite(f[i]) for i in (0,1,2,4,5,7)):return
                if f[0]<=previous or not 0<=f[0]<1000 or not 0<=f[1]<=LEVELS[index].length or not -300<=f[2]<=430 or f[3] not in ('',*ABILITIES):return
                from .pixelart import PLAYER_CLIPS
                if f[6] not in PLAYER_CLIPS or not 100<=f[7]<=450:return
                previous=f[0]
            self.frames=frames
        except (OSError,ValueError,TypeError,AttributeError):pass
    def at(self,time):
        if not self.frames or time>self.frames[-1][0]:return None
        while self.cursor+1<len(self.frames) and self.frames[self.cursor+1][0]<=time:self.cursor+=1
        return self.frames[self.cursor]
