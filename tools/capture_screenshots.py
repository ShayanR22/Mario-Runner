"""Capture real game frames using isolated saves. Optional Pillow creates a GIF."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import pygame as pg
from runner.app import Game
from runner.config import STEP,GROUND
from runner.abilities import ABILITIES
from runner.enemies import Enemy


def steer(game):
    w=game.world
    upcoming=[e for e in w.enemies if e.state=='alive' and e.x(w)>w.player.x-32]
    if upcoming and upcoming[0].kind!='bullet' and w.player.grounded and upcoming[0].x(w)-w.player.x<w.speed*.30:w.player.request_jump()
    game.update(STEP)


def main():
    out=ROOT/'docs';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        game=Game(Path(d)/'save.json',renderer='software')
        def capture(name):
            game.draw();pg.image.save(game.canvas,out/f'{name}.png')
        capture('menu')
        for i,form in enumerate(('fire','ice','tanooki','star')):
            game.start_level(i,internal=True);capture(f'intro-{i+1}');game.action('begin')
            game.world.distance=2850;game.scene.decor_distance=2850
            game.world.abilities.activate(form)
            game.world.abilities.transform_time=0
            game.world.player.bottom=GROUND-100;game.world.player.velocity=-120;game.world.player.jumps=1
            if form in ('fire','ice'):game.world.attack()
            capture(f'world-{i+1}')
        montage=pg.Surface((960,540))
        for i in range(4):montage.blit(pg.transform.scale(pg.image.load(str(out/f'world-{i+1}.png')),(480,270)),((i%2)*480,(i//2)*270))
        pg.image.save(montage,out/'four-worlds.png')
        for form in (*ABILITIES,'star','mega'):
            index=1 if form in ('ice','penguin') else 2 if form in ('cape','tanooki','boomerang') else 0
            game.start_level(index,internal=True);game.action('begin')
            w=game.world;w.distance=2350;game.scene.decor_distance=2350
            w.abilities.activate(form);w.abilities.transform_time=0
            if form in ('cat','cape','tanooki'):
                w.player.bottom=GROUND-95;w.player.velocity=120;w.player.jumps=1;w.player.holding_jump=True
            if form=='cat':w.attack()
            if form in ('fire','ice','penguin','boomerang'):w.attack()
            capture(f'ability-{form}')
        game.action('pause');capture('paused');game.action('settings');capture('settings')
        game.action('settings_page');capture('graphics-settings');game.action('menu')
        game.save.cosmetics=['classic','ice','sunset','trail','confetti'];game.action('cosmetics');capture('cosmetics')
        game.save.encountered=[14400]*4;game.action('practice');capture('practice');game.action('records');capture('records')
        game.start_level(0,internal=True);game.action('begin');w=game.world;w.distance=5500;w.context();capture('secret-room');w.exit_room()
        w.distance=w.level.length-1;w.enemies=[];w.player.bottom=GROUND-200;w.player.velocity=0
        game.update(STEP);capture('flagpole');game.action('skip');capture('complete')
        frames=[]
        try:
            from PIL import Image
        except ImportError:Image=None
        if Image:
            game.start_level(0,internal=True);game.action('begin');game.world.abilities.activate('fire');game.save.shake=False
            for tick in range(120*16):
                if tick%42==0:game.world.attack()
                steer(game)
                if tick%10==0:
                    game.draw();small=pg.transform.scale(game.canvas,(480,270))
                    frames.append(Image.frombytes('RGB',small.get_size(),pg.image.tobytes(small,'RGB')))
            frames[0].save(out/'gameplay.gif',save_all=True,append_images=frames[1:],duration=[90 if i%3==0 else 80 for i in range(len(frames))],loop=0,optimize=True)
        game.presenter.close();pg.quit()
    print(f'Captured four worlds, ten abilities, menus, results and {len(frames)} gameplay frames in {out}')

if __name__=='__main__':main()
