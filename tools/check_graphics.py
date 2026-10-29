"""Native GPU conformance and screenshot check. Requires an actual display."""
from pathlib import Path
import sys,tempfile,time,json
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import pygame as pg
from runner.app import Game

def rgb(surface):
    return pg.image.tobytes(surface,"RGB")

def main():
    report={}
    with tempfile.TemporaryDirectory() as directory:
        game=Game(save_path=Path(directory)/"save.json",renderer="opengl")
        try:
            game.save.unlocked=4
            pipe=game.presenter.pipeline
            report["renderer"]=pipe.ctx.info["GL_RENDERER"]
            report["pygame_ce"]=pg.version.ver
            for index in range(4):
                game.start_level(index,internal=True);game.action("begin")
                game.world.distance=2700;game.scene.decor_distance=2700
                for enemy in game.world.enemies:enemy.age=1
                game.scene.time=0
                game.save.enhanced_effects=False;game.draw();game.presenter.tick(1);game.present()
                baseline=game.presenter.capture(game.canvas)
                delta=max(abs(a-b) for a,b in zip(rgb(baseline),rgb(game.canvas)))
                assert delta<=2,("Baseline orientation / alpha mismatch",index,delta)
                game.save.enhanced_effects=True;game.present()
                enhanced=game.presenter.capture(game.canvas)
                assert rgb(enhanced)!=rgb(baseline),"Effects did not change the world"
                assert enhanced.get_at((800,35))==baseline.get_at((800,35)),"HUD was modified"
                if index in (1,3):
                    pg.image.save(enhanced,ROOT/f"docs/enhanced-{'cave' if index==1 else 'castle'}.png")
                    pg.image.save(baseline,ROOT/f"docs/standard-{'cave' if index==1 else 'castle'}.png")
                if index==3:
                    game.scene.time=1;game.present()
                    animated=game.presenter.capture(game.canvas)
                    body=game.world.player.body.inflate(36,16)
                    assert rgb(enhanced.subsurface(body))==rgb(animated.subsurface(body)),"Heat moved the player"
                    assert rgb(enhanced)!=rgb(animated),"Heat distortion did not animate"
                    game.save.reduced_motion=True;game.present();still=game.presenter.capture(game.canvas)
                    game.scene.time=4;game.present()
                    assert rgb(still)==rgb(game.presenter.capture(game.canvas)),"Reduced motion still animated heat"
                    game.save.reduced_motion=False
                report[f"world_{index+1}"]="orientation, alpha, HUD and effects OK"
            # Resize the actual window while retaining its GL context and buffers.
            window=pg.Window.from_display_module()
            window.size=(1100,700)
            pg.event.pump()
            game.present()
            assert pipe.ctx.error=="GL_NO_ERROR"
            report["resize"]="OK"
            window.size=(960,540)
            game.presenter.toggle_fullscreen()
            game.draw();game.present()
            assert pg.display.get_surface() is not None
            assert game.presenter.accelerated,"Fullscreen lost the GPU context"
            assert game.presenter.pipeline.ctx.error=="GL_NO_ERROR"
            game.presenter.toggle_fullscreen();game.draw();game.present()
            pipe=game.presenter.pipeline
            report["fullscreen"]="enter, present, restore OK"
            # Measure the native renderer in a controlled two-second gameplay sample.
            game.start_level(3,internal=True);game.action("begin")
            frames=120;start=time.perf_counter()
            for _ in range(frames):
                for event in pg.event.get():
                    if event.type==pg.QUIT:raise RuntimeError("GPU check closed by user")
                game.presenter.tick(1/60)
                game.update(1/120);game.update(1/120);game.draw();game.present()
            elapsed=time.perf_counter()-start
            report["uncapped_render_fps"]=round(frames/elapsed,1)
            report["gl_error"]=pipe.ctx.error
            assert pipe.ctx.error=="GL_NO_ERROR"
            cave=pg.image.load(str(ROOT/"docs/enhanced-cave.png"))
            castle=pg.image.load(str(ROOT/"docs/enhanced-castle.png"))
            comparison=pg.Surface((960,540))
            for i,image in enumerate((pg.image.load(str(ROOT/"docs/standard-cave.png")),cave,
                                      pg.image.load(str(ROOT/"docs/standard-castle.png")),castle)):
                comparison.blit(pg.transform.scale(image,(480,270)),((i%2)*480,(i//2)*270))
            pg.image.save(comparison,ROOT/"docs/graphics-comparison.png")
            (ROOT/"docs/graphics-check.json").write_text(json.dumps(report,indent=2))
            print(json.dumps(report,indent=2))
        finally:
            game.presenter.close();pg.quit()

if __name__=="__main__":
    main()
