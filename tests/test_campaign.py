"""Campaign/scoring contracts, independent of GPU and personal save files."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import tempfile,json,unittest
import pygame as pg
from runner.app import Game
from runner.model import World,Coin
from runner.scoring import Score
from runner.storage import SaveData
from runner.config import STEP,GROUND

class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.g=Game(Path(self.d.name)/'save.json',renderer='software')
    def tearDown(self):
        self.g.presenter.close();pg.quit();self.d.cleanup()
    def test_sequence_and_finish_is_transactional(self):
        g=self.g
        self.assertFalse(g.start_level(2));g.action('new');g.action('begin')
        total=0
        for index in range(4):
            self.assertEqual(g.world.level_index,index)
            self.assertEqual(g.world.base_score,total)
            g.world.distance=g.world.level.length-1;g.world.enemies=[]
            g.update(STEP)
            self.assertEqual(g.state,'victory')
            total=g.world.score
            saved=SaveData(g.save.path)
            self.assertEqual(len(saved.commits),index+1)
            self.assertEqual(saved.stage_bests[index],g.world.stage_score)
            for _ in range(50):g.update(STEP)
            self.assertEqual(g.world.score,total)
            g.action('skip');self.assertEqual(g.state,'results')
            if index<3:
                g.update(6.1);self.assertEqual(g.state,'intro');g.action('begin')
        self.assertIsNone(SaveData(g.save.path).resume)
    def test_checkpoint_rollback_full_score_and_combo(self):
        g=self.g;g.action('new');g.action('begin');w=g.world
        w.distance=w.level.checkpoint-1
        w.scoring.award('earlier',700)
        w.update(STEP,g.assets);snap=w.checkpoint
        w.scoring.award('later',900)
        restored=World(0,snap)
        self.assertEqual(restored.scoring.dump(),snap['scoring'])
        self.assertNotIn('later',restored.scoring.awarded)
    def test_new_game_confirmation_preserves_records(self):
        g=self.g;g.action('new');g.save.best=7000;g.save.cosmetics=['classic','ice']
        old=g.world.run_id;g.action('menu');g.action('new')
        self.assertEqual(g.state,'confirm');self.assertEqual(g.world.run_id,old)
        g.action('new_confirm');self.assertNotEqual(g.world.run_id,old)
        self.assertEqual(g.save.best,7000);self.assertIn('ice',g.save.cosmetics)
    def test_commit_twice_or_close_during_celebration(self):
        g=self.g;g.action('new');g.action('begin');w=g.world
        w.distance=w.level.length-1;w.enemies=[];g.update(STEP)
        first=g.save.stage_bests.copy()
        g.save.finish(0,w.score,w.stage_score,f'{w.run_id}:0')
        self.assertEqual(g.save.stage_bests,first)
        other=Game(g.save.path,renderer='software');other.action('continue')
        self.assertEqual(other.world.level_index,1);other.presenter.close()
    def test_legacy_records_labelled_and_settings_preserved(self):
        p=Path(self.d.name)/'legacy.json';p.write_text(json.dumps({'version':2,'best':1234,'stage_bests':[300,500,0,0],'volume':.75,'unlocked':2,'resume':{'level':1,'checkpoint':True}}))
        s=SaveData(p);self.assertEqual(s.best,0);self.assertEqual(s.legacy['best'],1234)
        self.assertEqual(s.volume,.75);self.assertFalse(s.resume['checkpoint'])
        s.write();self.assertEqual(SaveData(p).legacy,s.legacy)
    def test_pause_freezes_finish(self):
        g=self.g;g.action('new');g.action('begin');g.world.distance=g.world.level.length-1;g.world.enemies=[];g.update(STEP)
        g.action('pause');before=g.world.victory.age;g.update(3)
        self.assertEqual(g.world.victory.age,before)
        g.action('resume');g.save.reduced_motion=True;g.update(STEP);self.assertEqual(g.state,'results')

class ScoreTests(unittest.TestCase):
    def test_multiplier_unique_rewards_and_safe_gap(self):
        s=Score()
        for i in range(5):s.award(str(i),100)
        self.assertEqual(s.multiplier,2);self.assertEqual(s.award('0',100),0)
        s.update(20,False);self.assertEqual(s.multiplier,2)
        s.update(5,True);self.assertEqual(s.multiplier,1)
        s.award('fixed',1000,False);self.assertEqual(s.points,1500)
        self.assertEqual(Score.load(s.dump()).dump(),s.dump())
    def test_flag_rewards_height_without_multiplier(self):
        low=World();low.begin_finish()
        high=World();high.player.bottom=GROUND-240;high.scoring.actions=20;high.begin_finish()
        self.assertEqual(high.result['flag'],3000);self.assertEqual(low.result['flag'],500)
        self.assertEqual(high.scoring.points,5000)
        high.begin_finish();self.assertEqual(high.scoring.points,5000)

class HardeningTests(unittest.TestCase):
    def test_nested_corrupt_checkpoint_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'save.json'
            p.write_text(json.dumps({'version':4,'scoring_version':3,'resume':{'level':0,'checkpoint':True,'distance':6300,'scoring':{'awarded':4,'actions':[]},'abilities':{'equipped':[],'reserve':{}},'enemies':42,'secrets':False}}))
            g=Game(p,renderer='software');g.action('continue');g.action('begin');g.update(STEP)
            self.assertEqual(g.world.distance,6300+g.world.level.speed_at(6300)*STEP)
            self.assertEqual(g.world.abilities.equipped,'');g.presenter.close();pg.quit()
    def test_remapping_and_all_mouse_ability_equivalents(self):
        with tempfile.TemporaryDirectory() as d:
            g=Game(Path(d)/'save.json',renderer='software');g.action('settings');g.action('remap:attack_key')
            g.handle(pg.event.Event(pg.KEYDOWN,key=pg.K_z));self.assertEqual(SaveData(g.save.path).attack_key,pg.K_z)
            g.action('new_confirm');g.action('begin');g.world.abilities.activate('fire')
            g.handle(pg.event.Event(pg.KEYDOWN,key=pg.K_z));self.assertEqual(len(g.world.projectiles),1)
            g.world.abilities.cooldown=0;g.handle(pg.event.Event(pg.MOUSEBUTTONDOWN,button=3,pos=(300,300)))
            self.assertEqual(len(g.world.projectiles),2)
            g.world.abilities.reserve='ice';g.handle(pg.event.Event(pg.MOUSEWHEEL,y=1,x=0))
            self.assertEqual(g.world.abilities.equipped,'ice');g.presenter.close();pg.quit()
    def test_retry_during_committed_celebration_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            g=Game(Path(d)/'save.json',renderer='software');g.action('new');g.action('begin')
            g.world.distance=g.world.level.length-1;g.world.enemies=[];g.update(STEP)
            saved=g.save.resume.copy();g.action('pause');g.action('retry')
            self.assertEqual(g.state,'paused');self.assertEqual(g.save.resume,saved)
            g.presenter.close();pg.quit()
