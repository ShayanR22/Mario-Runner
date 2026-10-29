"""Validated, versioned atomic saves; permanent records and campaign are separate."""
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from .balance import SCORING_VERSION

SAVE_VERSION = 4

def default_path():
    override=os.environ.get("MARIO_RUNNER_SAVE")
    if override:
        return Path(override)
    if sys.platform=="darwin":
        base=Path.home()/"Library"/"Application Support"
    elif sys.platform=="win32":
        base=Path(os.environ.get("LOCALAPPDATA",Path.home()))
    else:
        base=Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))
    return base/"MarioRunner"/"save.json"

def integer(value, default=0, upper=10**9):
    return value if type(value) is int and 0<=value<=upper else default

def number(value, default=0., upper=100000., lower=0.):
    return float(value) if type(value) in (int,float) and math.isfinite(value) and lower<=value<=upper else default

def strings(value, limit=2000):
    return [s for s in value[:limit] if isinstance(s,str) and len(s)<100] if isinstance(value,list) else []

def valid_resume(value, unlocked=4):
    if not isinstance(value,dict) or type(value.get("level")) is not int or not 0<=value["level"]<4:
        return None
    if len(json.dumps(value))>600000:
        return None
    # Model-specific nested state is validated by World and its subsystem loaders.
    result=dict(value)
    result["distance"]=number(value.get("distance"),0,16000)
    result["elapsed"]=number(value.get("elapsed"),0,10000)
    result["base"]=integer(value.get("base"))
    result["run_id"]=str(value.get("run_id","migrated"))[:64]
    result["checkpoint"]=value.get("checkpoint") is True
    return result

class SaveData:
    def __init__(self,path=None):
        self.path=Path(path) if path else default_path()
        self.best=0;self.volume=.35;self.music_volume=.15;self.muted=False
        self.reduced_motion=False;self.enhanced_effects=True
        self.bloom=.6;self.heat=True;self.particles=True;self.shake=True;self.ghost=True
        self.attack_key=120;self.jump_key=32;self.context_key=1073741905;self.reserve_key=99
        self.unlocked=1;self.stage_bests=[0]*4;self.completed=[False]*4
        self.medals=["NONE"]*4;self.cosmetics=["classic"];self.outfit="classic"
        self.resume=None;self.legacy={};self.commits=[];self.last_result=None
        self.encountered=[0.]*4;self.error=False
        try:
            data=json.loads(self.path.read_text())
            if not isinstance(data,dict):
                return
            self.volume=number(data.get("volume"),.35,1)
            self.music_volume=number(data.get("music_volume"),.15,1)
            for field in ("reduced_motion","muted"):
                setattr(self,field,data.get(field) is True)
            for field in ("enhanced_effects","heat","particles","shake","ghost"):
                setattr(self,field,data.get(field,True) is not False)
            self.bloom=number(data.get("bloom"),.6,1)
            assigned=set()
            for name,default in (("attack_key",120),("jump_key",32),("context_key",1073741905),("reserve_key",99)):
                value=integer(data.get(name),default,2147483647) or default
                if value in assigned or value in (27,112,109,1073741892):value=default
                assigned.add(value);setattr(self,name,value)
            self.unlocked=max(1,integer(data.get("unlocked"),1,4))
            completed=data.get("completed",[])
            if isinstance(completed,list) and len(completed)==4:
                self.completed=[v is True for v in completed]
            for key in ("stage_bests","encountered"):
                values=data.get(key,[])
                if isinstance(values,list) and len(values)==4:
                    setattr(self,key,[integer(v) if key=="stage_bests" else number(v,0,16000) for v in values])
            self.best=integer(data.get("best"))
            self.legacy=data.get("legacy",{}) if isinstance(data.get("legacy"),dict) else {}
            if data.get("scoring_version")!=SCORING_VERSION:
                self.legacy={"best":self.best,"stage_bests":self.stage_bests.copy()}
                self.best=0;self.stage_bests=[0]*4
                # Old checkpoints lack a full skill-scoring snapshot: restart that world.
                old=valid_resume(data.get("resume"))
                if old:
                    old={"level":old["level"],"base":0,"checkpoint":False,"run_id":"migrated"}
                self.resume=old
                self.encountered=[14400. if done else 0. for done in self.completed]
            else:
                self.resume=valid_resume(data.get("resume"))
                self.commits=strings(data.get("commits",[]),200)
                from .balance import medal
                self.medals=[medal(v) for v in self.stage_bests]
                self.cosmetics=list(dict.fromkeys(["classic"]+[s for s in strings(data.get("cosmetics",[]),12) if s in ("ice","sunset","trail","confetti")]))
                self.outfit=data.get("outfit") if isinstance(data.get("outfit"),str) and data.get("outfit") in self.cosmetics else "classic"
                self.last_result=data.get("last_result") if isinstance(data.get("last_result"),dict) else None
        except (OSError,ValueError,TypeError,AttributeError,OverflowError):
            pass

    def write(self):
        temporary=None
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fields=("best","volume","music_volume","muted","reduced_motion","enhanced_effects","bloom","heat","particles","shake","ghost","attack_key","jump_key","context_key","reserve_key","unlocked","stage_bests","completed","resume","legacy","commits","last_result","medals","cosmetics","outfit","encountered")
            data={k:getattr(self,k) for k in fields}
            data.update(version=SAVE_VERSION,scoring_version=SCORING_VERSION)
            with tempfile.NamedTemporaryFile(mode="w",dir=self.path.parent,suffix=".tmp",delete=False) as f:
                temporary=Path(f.name)
                json.dump(data,f,allow_nan=False)
                f.flush();os.fsync(f.fileno())
            os.replace(temporary,self.path)
            self.error=False
        except (OSError,ValueError):
            self.error=True
        finally:
            if temporary and temporary.exists():
                try: temporary.unlink()
                except OSError: pass

    def record(self,score):
        previous=self.best
        self.best=max(self.best,int(score));self.write()
        return score>previous

    def finish(self,index,total,stage_score,token=None,challenges=()):
        from .balance import medal,rank
        token=token or f"legacy:{index}:{total}"
        if token in self.commits:
            return self.last_result
        previous=self.stage_bests[index]
        self.best=max(self.best,total)
        self.stage_bests[index]=max(previous,stage_score)
        self.medals[index]=medal(self.stage_bests[index])
        self.completed[index]=True;self.unlocked=max(self.unlocked,min(4,index+2))
        self.encountered[index]=14400.
        self.commits=(self.commits+[token])[-200:]
        if self.medals[index] in ("SILVER","GOLD") and "ice" not in self.cosmetics:self.cosmetics.append("ice")
        if self.medals[index]=="GOLD" and "sunset" not in self.cosmetics:self.cosmetics.append("sunset")
        if challenges and "trail" not in self.cosmetics:self.cosmetics.append("trail")
        if index==3 and "confetti" not in self.cosmetics:self.cosmetics.append("confetti")
        self.resume={"level":index+1,"checkpoint":False,"base":total,"run_id":token.rsplit(":",1)[0]} if index<3 else None
        self.last_result={"world":index,"score":stage_score,"total":total,"medal":medal(stage_score),"improvement":max(0,stage_score-previous),"rank":rank(total),"challenges":list(challenges)}
        self.write()
        return self.last_result
