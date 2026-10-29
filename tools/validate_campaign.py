"""Reproducible course feasibility and medal calibration report, no player saves."""
import os,sys,json,platform
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
import pygame as pg
from runner.model import World
from runner.assets import Assets
from runner.config import STEP
from runner.balance import medal


def main():
    pg.init();pg.display.set_mode((960,540));assets=Assets();runs=[]
    for index in range(4):
        for timing in (.27,.30,.34):
            w=World(index);w.pickups=[]
            for _ in range(120*65):
                if w.dead or w.victory:break
                upcoming=[e for e in w.enemies if e.state=='alive' and e.x(w)>w.player.x-32]
                if upcoming and upcoming[0].kind!='bullet' and w.player.grounded and upcoming[0].x(w)-w.player.x<w.speed*timing:w.player.request_jump()
                if w.level.length-w.distance<w.speed*.70:
                    if w.player.grounded or w.player.jumps==1 and w.player.velocity>-30:w.player.request_jump()
                w.update(STEP,assets)
            assert w.victory and not w.dead,(index,timing,w.distance)
            runs.append({'world':index+1,'jump_lead_seconds':timing,'seconds':round(w.elapsed,2),'score':w.stage_score,'medal':medal(w.stage_score),'coins':w.coins_collected,'powerups':False,'flag_bonus':w.result['flag']})
    assert all(any(r['medal']=='GOLD' for r in runs if r['world']==i) for i in range(1,5)),runs
    report={'python':platform.python_version(),'pygame_ce':pg.version.ver,'simulation_hz':120,'runs':runs,'note':'Deterministic automated single-jump encounter policy; final pole double jump enabled. Human play remains necessary for subjective difficulty.'}
    (ROOT/'docs/course-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));pg.quit()
if __name__=='__main__':main()
