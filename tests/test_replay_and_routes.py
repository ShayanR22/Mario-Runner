import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import tempfile,json,unittest
from pathlib import Path
import pygame as pg
from runner.app import Game
from runner.model import World,Coin
from runner.enemies import Enemy
from runner.assets import Assets
from runner.config import STEP,GROUND
from runner.replays import Ghost,Recorder
from runner.balance import MEDALS

class ReplayAndRouteTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.g=Game(Path(self.d.name)/'save.json',renderer='software')
    def tearDown(self):self.g.presenter.close();pg.quit();self.d.cleanup()
    def test_practice_isolation_and_unexplored_lock(self):
        g=self.g;g.action('new');g.action('begin');g.save.encountered[0]=1000
        before=g.save.resume.copy();records=g.save.stage_bests.copy();cosmetics=g.save.cosmetics.copy()
        g.action('practice:2:0');self.assertFalse(g.practice)
        g.action('practice:0:0');self.assertTrue(g.practice);g.action('begin')
        g.world.distance=g.practice_end-1;g.world.enemies=[];g.update(STEP)
        self.assertEqual(g.state,'results');self.assertEqual(g.save.resume,before)
        self.assertEqual(g.save.stage_bests,records);self.assertEqual(g.save.cosmetics,cosmetics)
    def test_pipe_freezes_main_course_and_cannot_duplicate_rewards(self):
        g=self.g;g.action('new');g.action('begin');w=g.world;w.distance=5500;w.context()
        self.assertIsNotNone(w.room);distance=w.distance;age=w.enemies[0].age
        for _ in range(40):w.update(STEP,g.assets)
        self.assertEqual(w.distance,distance);self.assertEqual(w.enemies[0].age,age)
        w.scoring.award('secret:0',100);w.exit_room();w.context();self.assertIsNone(w.room)
        points=w.score;w.scoring.award('secret:0',100);self.assertEqual(w.score,points)
        restored=World(0,w.snapshot(True));restored.context();self.assertIsNone(restored.room)
    def test_red_coins_set_once_and_retry_rollback(self):
        w=World();events=[]
        for coin in [c for c in w.coins if c.red]:w.collect(coin,events)
        self.assertEqual(len(w.red_ids),6);self.assertIn('red_set',w.challenges)
        score=w.score
        for coin in w.coins:
            if coin.red:w.collect(coin,events)
        self.assertEqual(w.score,score)
        r=World(0,w.snapshot(True));self.assertEqual(r.red_ids,w.red_ids)
    def test_ghost_roundtrip_version_and_corruption(self):
        w=World();p=Path(self.d.name)/'ghost.json'
        for _ in range(40):w.update(STEP,self.g.assets)
        self.assertTrue(w.recorder.save(p,0,100));ghost=Ghost(p,0)
        self.assertTrue(ghost.frames);self.assertIsNotNone(ghost.at(.1))
        data=json.loads(p.read_text());data['signature']='old';p.write_text(json.dumps(data));self.assertFalse(Ghost(p,0).frames)
        for bad in ('{broken','[]','{"signature":null,"frames":7}'):
            p.write_text(bad);self.assertFalse(Ghost(p,0).frames)
    def test_all_routes_land_using_actual_double_jump(self):
        for index in range(4):
            for start in (2400,8400):
                w=World(index);w.enemies=[];w.pickups=[];w.distance=start-110;w.player.request_jump()
                landed=False
                for _ in range(160):
                    # A second jump near the apex reaches the upper reward lane.
                    if w.player.jumps==1 and w.player.velocity>-70:w.player.request_jump()
                    w.update(STEP,self.g.assets)
                    if w.player.on_platform:landed=True;break
                self.assertTrue(landed,(index,start,w.distance,w.player.bottom))
    def test_full_courses_and_both_checkpoint_retries_without_powerups(self):
        report=[]
        for index in range(4):
            for timing in (.27,.30,.34):
                w=World(index);w.pickups=[]
                checkpoints=[]
                for _ in range(120*65):
                    if w.victory or w.dead:break
                    upcoming=[e for e in w.enemies if e.state=='alive' and e.x(w)>w.player.x-32]
                    if upcoming and upcoming[0].kind!='bullet' and w.player.grounded and upcoming[0].x(w)-w.player.x<w.speed*timing:w.player.request_jump()
                    events=w.update(STEP,self.g.assets)
                    if any(e[0]=='checkpoint' for e in events):checkpoints.append(w.checkpoint)
                self.assertFalse(w.dead,(index,timing,w.distance));self.assertIsNotNone(w.victory)
                self.assertEqual(len(checkpoints),2)
                for snap in checkpoints:
                    r=World(index,snap);r.pickups=[]
                    for _ in range(120*40):
                        if r.victory or r.dead:break
                        upcoming=[e for e in r.enemies if e.state=='alive' and e.x(r)>r.player.x-32]
                        if upcoming and upcoming[0].kind!='bullet' and r.player.grounded and upcoming[0].x(r)-r.player.x<r.speed*timing:r.player.request_jump()
                        r.update(STEP,self.g.assets)
                    self.assertFalse(r.dead,(index,timing,'retry',r.distance));self.assertIsNotNone(r.victory)
                report.append(w.stage_score)
        self.assertTrue(all(score>=MEDALS[0] for score in report),report)

    def test_every_red_route_is_traversable_with_actual_enemies(self):
        for index in range(4):
            for start in (2400,8400):
                w=World(index);w.pickups=[];w.distance=start-110;w.player.request_jump();second=False
                for _ in range(700):
                    if w.distance>start+230 and not second and w.player.grounded:
                        w.player.request_jump();second=True
                    w.update(STEP,self.g.assets)
                    if w.distance>start+1050 or w.dead:break
                self.assertFalse(w.dead,(index,start,w.distance))
                self.assertEqual(len(w.red_ids),3,(index,start,w.red_ids))

    def test_top_flag_reward_reachable_with_real_double_jump(self):
        for index in range(4):
            w=World(index);w.enemies=[];w.pickups=[];w.distance=w.level.length-w.speed*.70
            for _ in range(120):
                if w.victory:break
                if w.player.grounded or w.player.jumps==1 and w.player.velocity>-30:w.player.request_jump()
                w.update(STEP,self.g.assets)
            self.assertIsNotNone(w.victory);self.assertEqual(w.result['flag'],3000)
            self.assertIn('flag_top',w.challenges)
