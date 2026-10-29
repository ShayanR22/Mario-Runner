"""Behavioral regression tests; all runs use isolated SDL and save data."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
import pygame as pg
from runner.app import Game
from runner.assets import Assets
from runner.audio import Audio
from runner.animation import player_pose
from runner.config import STEP,GROUND,ROOT
from runner.enemies import Enemy
from runner.levels import LEVELS
from runner.model import World,Player,Coin
from runner.storage import SaveData

def autoplay(world,assets,timing=.30,limit=90):
    while not world.dead and not world.finished and not world.victory and world.elapsed<limit:
        upcoming=[e for e in world.enemies if e.state=="alive" and e.x(world)>world.player.x-32]
        if upcoming:
            e=upcoming[0]
            if e.kind!="bullet" and world.player.grounded and e.x(world)-world.player.x<world.speed*timing:
                world.player.request_jump()
        world.update(STEP,assets)
    return bool(world.finished or world.victory)

class PhysicsTests(unittest.TestCase):
    def test_two_jumps_landing_and_buffer(self):
        p=Player()
        p.request_jump()
        self.assertEqual(p.update(STEP),1)
        for _ in range(20): p.update(STEP)
        p.request_jump()
        self.assertEqual(p.update(STEP),2)
        p.request_jump()
        self.assertEqual(p.update(STEP),0)
        for _ in range(200): p.update(STEP)
        self.assertEqual((p.bottom,p.jumps,p.velocity),(GROUND,0,0))
        p.bottom,p.velocity,p.jumps=GROUND-1,200,2
        p.request_jump();p.update(STEP)
        self.assertEqual(p.update(STEP),1)

    def test_tap_is_lower_but_clears_goomba(self):
        heights=[]
        for released in (True,False):
            p=Player();p.request_jump()
            if released:p.release_jump()
            height=0
            for _ in range(150):
                p.update(STEP);height=max(height,GROUND-p.bottom)
            heights.append(height)
        self.assertGreater(heights[0],55)
        self.assertGreater(heights[1],heights[0]+55)

    def test_animation_is_independent_of_body(self):
        p=Player()
        body=p.body.copy()
        for idle in (False,True):
            player_pose(p,1,idle)
            self.assertEqual(body,p.body)
        p.request_jump();p.update(STEP)
        self.assertEqual(player_pose(p,99)[0],"jump")
        self.assertLess(player_pose(p,99)[1],.02)

    def test_level_gaps_and_checkpoint_safety(self):
        for level in LEVELS:
            gaps=[b.at-a.at for a,b in zip(level.encounters,level.encounters[1:])]
            self.assertGreaterEqual(min(gaps)/level.speed_at(level.length),1.8)
            self.assertTrue(all(abs(e.at-level.checkpoint)>=800 for e in level.encounters))
            self.assertGreater(level.length-level.encounters[-1].at,1000)
            self.assertLessEqual(level.speed_at(level.length),370)

class StorageTests(unittest.TestCase):
    def test_legacy_migration(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"save.json"
            p.write_text('{"best":1234,"volume":0.75,"reduced_motion":true}')
            s=SaveData(p)
            self.assertEqual((s.best,s.volume,s.reduced_motion,s.unlocked),(0,.75,True,1))
            self.assertEqual(s.legacy["best"],1234)
            s.write()
            self.assertEqual(json.loads(p.read_text())["version"],4)

    def test_unlocks_scores_and_checkpoint_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"nested/save.json"
            s=SaveData(p);s.finish(0,1400,1400)
            s.resume={"level":1,"checkpoint":True,"coins":8,"stomps":2,"elapsed":19.5,"base":1400,"cleared":5}
            s.write();s=SaveData(p)
            self.assertEqual(s.unlocked,2)
            self.assertEqual(s.stage_bests,[1400,0,0,0])
            self.assertTrue(s.completed[0])
            self.assertEqual(s.resume["coins"],8)
            s.record(20)
            self.assertEqual(SaveData(p).best,1400)

    def test_invalid_data_and_atomic_write_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"save.json"
            for text in ('[]','null','{broken','{"best":true,"volume":NaN,"unlocked":99,"resume":{"level":9}}'):
                p.write_text(text);s=SaveData(p)
                self.assertEqual((s.best,s.volume,s.unlocked,s.resume),(0,.35,1,None))
            with patch("runner.storage.os.replace",side_effect=PermissionError):
                s.record(100)
                self.assertTrue(s.error)
                self.assertEqual(s.best,100)
                self.assertEqual(list(Path(d).glob("*.tmp")),[])

class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pg.init();pg.display.set_mode((960,540))
        cls.assets=Assets()

    @classmethod
    def tearDownClass(cls):
        pg.quit()

    def test_production_assets_and_alignment(self):
        self.assertEqual(self.assets.missing,[])
        manifest=json.loads((ROOT/"assets/sheets/manifest.json").read_text())
        self.assertEqual(manifest["anchor"],[16,38])
        for name,spec in manifest["sheets"].items():
            sheet=pg.image.load(str(ROOT/"assets/sheets"/spec["file"]))
            for clip in spec["clips"].values():
                for index in clip["frames"]:
                    cell=sheet.subsurface((index%8*32,index//8*40,32,40))
                    bounds=cell.get_bounding_rect()
                    self.assertGreater(bounds.width,0)
                    self.assertLessEqual(bounds.bottom,38)
                    self.assertLessEqual(bounds.right,32)
        for biome in ("grass","cave","sky","castle"):
            tile=self.assets.grounds[biome]
            # The horizontal repeat is periodic in the tile's geometry.
            self.assertEqual(tile.get_size(),(128,64))
        self.assertGreater(self.assets.font(32,True).size("MARIO")[0],0)

    def test_every_course_and_retry_is_clearable(self):
        for index in range(4):
            for timing in (.27,.30,.34):
                with self.subTest(level=index,timing=timing):
                    w=World(index)
                    self.assertTrue(autoplay(w,self.assets,timing))
                    self.assertIsNotNone(w.checkpoint)
                    restored=World(index,w.checkpoint)
                    self.assertTrue(autoplay(restored,self.assets,timing))
                    self.assertEqual(w.distance,w.level.length)

    def test_stomp_each_supported_enemy(self):
        for kind in ("goomba","koopa","buzzy","paratroopa","drybones"):
            with self.subTest(kind=kind):
                w=World();e=Enemy(kind,0);w.enemies=[e];w.coins=[]
                w.player.bottom=e.rect(w).top-1
                w.player.velocity=240;w.player.jumps=1
                events=w.update(STEP,self.assets)
                self.assertFalse(w.dead)
                self.assertEqual(w.stomps,1)
                self.assertLess(w.player.velocity,0)
                self.assertEqual(w.player.jumps,1)
                self.assertIn("stomp",[x[0] for x in events])

    def test_side_contacts_damage(self):
        for kind in ("goomba","koopa","buzzy","paratroopa","drybones","pipe","fire"):
            with self.subTest(kind=kind):
                w=World();e=Enemy(kind,0,age=1);w.enemies=[e];w.coins=[]
                w.update(STEP,self.assets)
                self.assertTrue(w.dead)

    def test_high_bullet_safe_on_ground_and_dangerous_in_air(self):
        for airborne in (False,True):
            w=World();w.enemies=[Enemy("bullet",0)];w.coins=[]
            if airborne:w.player.bottom=GROUND-90
            w.update(STEP,self.assets)
            self.assertEqual(w.dead,airborne)

    def test_fire_warning_active_and_cooldown(self):
        e=Enemy("fire",0)
        self.assertTrue(e.warning);self.assertFalse(e.dangerous)
        e.age=.9
        self.assertTrue(e.dangerous);self.assertFalse(e.warning)
        e.age=2.2
        self.assertFalse(e.dangerous)
        w=World();w.enemies=[e];w.coins=[]
        w.update(STEP,self.assets)
        self.assertFalse(w.dead)

    def test_drybones_rebuild_and_koopa_shell_clears_enemy(self):
        w=World();e=Enemy("drybones",0);e.stomp()
        self.assertFalse(e.dangerous)
        e.update(1.7,w)
        self.assertTrue(e.dangerous)
        shell=Enemy("koopa",0);shell.stomp()
        target=Enemy("goomba",20)
        w.enemies=[shell,target];w.coins=[]
        w.update(STEP,self.assets)
        self.assertFalse(w.dead)
        self.assertEqual(target.state,"gone")

    def test_collect_coin_once(self):
        w=World();w.enemies=[];w.coins=[Coin(0,GROUND-25)]
        w.update(STEP,self.assets);w.update(STEP,self.assets)
        self.assertEqual(w.coins_collected,1)

    def test_checkpoint_rewinds_post_checkpoint_rewards(self):
        w=World()
        w.distance=w.level.checkpoint-1;w.coins_collected=5;w.stomps=2;w.elapsed=20
        w.update(STEP,self.assets)
        checkpoint=w.checkpoint.copy()
        w.coins_collected+=9;w.stomps+=4
        restored=World(0,checkpoint)
        self.assertEqual((restored.distance,restored.coins_collected,restored.stomps),(6300,5,2))
        self.assertTrue(all(e.at>6300 for e in restored.enemies))
        self.assertEqual([e.age for e in restored.enemies],[e["age"] for e in checkpoint["enemies"]])

    def test_end_state_cannot_keep_scoring(self):
        w=World();w.distance=w.level.length-1;w.enemies=[]
        events=w.update(STEP,self.assets)
        self.assertIn("finish",[x[0] for x in events])
        score=w.score
        for _ in range(100):w.update(STEP,self.assets)
        self.assertEqual(score,w.score)

    def test_missing_assets_and_audio_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertLogs(level="WARNING"):
                a=Assets(Path(d))
            self.assertEqual(len(a.missing),7)
            self.assertGreater(a.font(24,True).size("RUN")[0],0)
            w=World();w.update(STEP,a)
        pg.mixer.quit()
        with patch("pygame.mixer.init",side_effect=pg.error("No audio device")):
            audio=Audio(.5)
        self.assertFalse(audio.available);audio.play("jump")

class AppTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.game=Game(save_path=Path(self.directory.name)/"save.json")
    def tearDown(self):
        pg.quit();self.directory.cleanup()
    def key(self,key,kind=pg.KEYDOWN):
        self.game.handle(pg.event.Event(kind,key=key))

    def test_locked_levels_and_begin_input(self):
        g=self.game
        self.assertFalse(g.start_level(1))
        self.key(pg.K_SPACE)
        self.assertEqual(g.state,"intro")
        g.update(1)
        self.assertEqual(g.world.distance,0)
        self.key(pg.K_SPACE)
        self.assertEqual(g.state,"playing")
        self.assertEqual(g.world.player.jumps,0)

    def test_pause_freezes_all_gameplay_and_modal_targets(self):
        g=self.game;g.start_level(0);g.action("begin")
        for _ in range(100):g.update(STEP)
        self.key(pg.K_ESCAPE)
        before=(g.world.distance,g.world.elapsed,g.scene.decor_distance,g.world.enemies[0].age)
        for _ in range(100):g.update(STEP)
        self.assertEqual(before,(g.world.distance,g.world.elapsed,g.scene.decor_distance,g.world.enemies[0].age))
        g.action("settings")
        self.assertEqual([b.action for b in g.ui.buttons],["volume","music","mute","motion","settings_page","settings_page","back"])
        self.key(pg.K_ESCAPE);self.assertEqual(g.state,"paused")
        self.key(pg.K_p);self.assertEqual(g.state,"playing")
        g.handle(pg.event.Event(pg.WINDOWFOCUSLOST))
        self.assertEqual(g.state,"paused")

    def test_campaign_transitions_unlock_and_completion(self):
        g=self.game
        for index in range(4):
            self.assertTrue(g.start_level(index,internal=True))
            g.action("begin")
            g.world.distance=g.world.level.length-1;g.world.enemies=[]
            g.update(STEP)
            self.assertEqual(g.state,"victory")
            self.assertTrue(g.save.completed[index])
            self.assertEqual(g.save.unlocked,min(4,index+2))
            previous=g.world.score
            if index<3:
                g.action("skip");g.action("next")
                self.assertEqual(g.state,"intro")
                self.assertEqual(g.world.base_score,previous)
        self.assertIsNone(SaveData(g.save.path).resume)

    def test_checkpoint_persists_and_retry_resets_attempt(self):
        g=self.game;g.start_level(0);g.action("begin")
        g.world.distance=6299;g.world.coins_collected=7;g.update(STEP)
        self.assertTrue(SaveData(g.save.path).resume["checkpoint"])
        g.world.distance=8000;g.world.coins_collected=20;g.world.dead=True
        g.transition("gameover");g.action("retry")
        self.assertEqual((g.world.distance,g.world.coins_collected,g.state),(6300,7,"intro"))

    def test_damage_animation_leads_to_retry(self):
        g=self.game;g.start_level(0);g.action("begin")
        g.world.enemies=[Enemy("goomba",0)];g.world.coins=[]
        g.update(STEP)
        self.assertEqual(g.state,"hurt")
        score=g.world.score
        for _ in range(70):g.update(STEP)
        self.assertEqual(g.state,"gameover")
        self.assertEqual(g.world.score,score)
        self.key(pg.K_SPACE)
        self.assertEqual(g.state,"intro")

    def test_reduced_motion_and_volume_save(self):
        g=self.game;g.action("settings");g.action("motion");g.action("volume")
        self.assertTrue(SaveData(g.save.path).reduced_motion)
        offset=g.scene.decor_distance
        g.scene.burst(10,10);g.scene.update(.1,300,True)
        self.assertEqual(g.scene.decor_distance,offset)
        self.assertEqual(g.scene.particles,[])

    def test_mouse_start_and_resize_mapping(self):
        g=self.game
        g.handle(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=(250,278)))
        self.assertEqual(g.state,"intro")
        g.window=pg.display.set_mode((1200,800),pg.RESIZABLE)
        x,y=g.logical_mouse((600,400))
        self.assertAlmostEqual(x,480);self.assertAlmostEqual(y,270)
        g.draw();g.present()

if __name__=="__main__":
    unittest.main()
