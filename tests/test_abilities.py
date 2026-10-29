"""Interaction and movement tests use actual fixed-step collision geometry."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
import pygame as pg
from runner.assets import Assets
from runner.model import World,Player,Coin
from runner.enemies import Enemy
from runner.abilities import AbilityState,ABILITIES
from runner.interactions import ROWS,METHODS,response
from runner.config import STEP,GROUND
from runner.routes import support

class AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):pg.init();pg.display.set_mode((960,540));cls.assets=Assets()
    @classmethod
    def tearDownClass(cls):pg.quit()
    def world(self):
        w=World();w.enemies=[];w.coins=[];w.pickups=[];return w
    def advance(self,w,seconds):
        for _ in range(int(seconds/STEP)):w.update(STEP,self.assets)
    def test_all_forms_serialize_and_reserve_swap(self):
        a=AbilityState()
        for item in ABILITIES:
            a.activate(item);self.assertEqual(a.equipped,item)
            self.assertEqual(AbilityState.load(a.dump()).dump(),a.dump())
        equipped,reserve=a.equipped,a.reserve;a.swap()
        self.assertEqual((a.equipped,a.reserve),(reserve,equipped))
    def test_mushroom_absorbs_one_hit_then_grace_expires(self):
        w=self.world();w.abilities.activate('mushroom');w.enemies=[Enemy('goomba',0)]
        w.update(STEP,self.assets)
        self.assertFalse(w.dead);self.assertEqual(w.abilities.equipped,'');self.assertGreater(w.abilities.grace,1)
        w.enemies=[Enemy('goomba',w.distance,1)];w.update(STEP,self.assets);self.assertFalse(w.dead)
        w.abilities.grace=0;w.enemies=[Enemy('goomba',w.distance,2)];w.update(STEP,self.assets);self.assertTrue(w.dead)
    def test_fire_limit_cooldown_and_resistance(self):
        w=self.world();w.abilities.activate('fire')
        for _ in range(10):w.attack();w.abilities.cooldown=0
        self.assertEqual(len(w.projectiles),3)
        events=[];goomba=Enemy('goomba',100,0);buzzy=Enemy('buzzy',130,1)
        self.assertTrue(w.affect(goomba,'fire',events));self.assertEqual(goomba.state,'gone')
        self.assertFalse(w.affect(buzzy,'fire',events));self.assertEqual(buzzy.state,'alive')
        score=w.score;w.affect(goomba,'fire',events);self.assertEqual(w.score,score)
    def test_actual_fire_and_ice_projectile_collision(self):
        for ability in ('fire','ice'):
            w=self.world();w.abilities.activate(ability);w.enemies=[Enemy('goomba',185)]
            w.attack();self.advance(w,.35)
            self.assertEqual(w.enemies[0].state,'gone' if ability=='fire' else 'frozen')
            self.assertFalse(w.dead)
    def test_freeze_kick_shatter_thaw_and_farming(self):
        w=self.world();e=Enemy('goomba',90,0);w.enemies=[e];events=[]
        w.affect(e,'ice',events);self.assertEqual(e.state,'frozen');self.assertEqual(w.score,0)
        w.attack();self.assertEqual(e.state,'frozen_shell')
        target=Enemy('koopa',110,1);w.enemies.append(target);w.update(STEP,self.assets)
        self.assertEqual(target.state,'gone');self.assertGreaterEqual(w.score,500)
        e=Enemy('drybones',500,3);w.affect(e,'ice',events);e.update(4.1,w);self.assertEqual(e.state,'alive')
        w.affect(e,'ice',events);w.affect(e,'ice',events);self.assertEqual(e.state,'gone')
        before=w.score;w.affect(e,'tail',events);self.assertEqual(w.score,before)
    def test_cat_climb_exits_automatically_and_claw_dive(self):
        w=self.world();w.distance=2320;w.abilities.activate('cat');w.context()
        self.assertGreater(w.abilities.climb,0);self.advance(w,.8)
        self.assertAlmostEqual(w.distance,2320);self.assertLess(w.player.bottom,GROUND-100)
        self.advance(w,.5);self.assertEqual(w.abilities.climb,0);self.assertGreater(w.distance,2370)
        w.player.bottom=300;w.player.on_platform=False;w.player.jumps=1;w.attack()
        self.assertTrue(w.abilities.dive);self.assertGreater(w.player.velocity,600)
    def test_star_and_mega_expire_with_grace_keep_equipment(self):
        for item in ('star','mega'):
            w=self.world();w.abilities.activate('fire');w.abilities.activate(item)
            setattr(w.abilities,item,STEP/2);w.enemies=[Enemy('goomba',0)]
            w.update(STEP,self.assets);self.assertFalse(w.dead);self.assertGreater(w.abilities.grace,.5)
            self.assertEqual(w.abilities.equipped,'fire')
        w=self.world();w.abilities.activate('mega');w.enemies=[Enemy('pipe',0)]
        w.update(STEP,self.assets);self.assertEqual(w.enemies[0].state,'gone');self.assertFalse(w.dead)
    def test_tanooki_float_and_cape_dive_are_distinct(self):
        velocities=[]
        for form in ('tanooki','cape'):
            w=self.world();w.abilities.activate(form);w.player.bottom=150;w.player.velocity=450
            w.player.jumps=2;w.player.holding_jump=True;w.update(STEP,self.assets);velocities.append(w.player.velocity)
        self.assertLess(velocities[1],velocities[0]);self.assertLess(velocities[0],160)
    def test_moving_platform_and_coyote_jump(self):
        w=World(2);platform=w.platforms[1];w.distance=platform.at+100;w.elapsed=.2
        w.player.previous_bottom=platform.y(w.elapsed-STEP)-1;w.player.bottom=platform.y(w.elapsed)+4;w.player.velocity=100
        support(w,STEP);self.assertTrue(w.player.grounded);self.assertEqual(w.player.jumps,0)
        w.player.on_platform=False;w.player.coyote=.06;w.player.request_jump()
        self.assertEqual(w.player.update(STEP),1)
    def test_ability_and_enemy_state_survive_checkpoint(self):
        w=self.world();w.distance=6300;w.abilities.activate('fire');w.abilities.activate('ice');w.abilities.star=2.4
        w.enemies=[Enemy('goomba',7100,5,state='frozen',timer=2.1)]
        snap=w.snapshot(True);restored=World(0,snap)
        self.assertEqual(restored.abilities.dump(),w.abilities.dump())
        self.assertEqual(restored.enemies[0].state,'frozen');self.assertAlmostEqual(restored.enemies[0].timer,2.1)
    def test_all_enemy_ability_pairs_are_defined(self):
        self.assertEqual(set(ROWS),{'goomba','koopa','buzzy','paratroopa','drybones','bullet','fire','pipe'})
        for kind in ROWS:
            for method in METHODS:self.assertIn(response(kind,method),('block','defeat','freeze','collapse','shell'))

class SecondaryAbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):pg.init();pg.display.set_mode((960,540));cls.assets=Assets()
    @classmethod
    def tearDownClass(cls):pg.quit()
    def test_boomerang_returns_collects_and_hits_each_enemy_once(self):
        w=World();w.enemies=[];w.pickups=[];w.coins=[Coin(110,GROUND-30,identity='boom-coin')]
        w.abilities.activate('boomerang');w.attack();w.attack();self.assertEqual(len(w.projectiles),1)
        for _ in range(200):w.update(STEP,self.assets)
        self.assertTrue(w.coins[0].collected);self.assertEqual(w.coins_collected,1);self.assertFalse(w.projectiles)
    def test_penguin_slide_and_ice_traction(self):
        x=[]
        for form in ('fire','penguin'):
            w=World(1);w.enemies=[];w.pickups=[];w.distance=4300;w.abilities.activate(form);w.player.land_time=.15
            for _ in range(15):w.update(STEP,self.assets)
            x.append(w.player.x)
            if form=='penguin':w.context();self.assertGreater(w.abilities.slide,0)
        self.assertGreater(x[0],x[1]);self.assertEqual(x[1],150)
    def test_mega_cannot_destroy_structures(self):
        w=World();before=w.platforms.copy();w.abilities.activate('mega')
        w.distance=6300;w.update(STEP,self.assets)
        self.assertEqual(w.platforms,before);self.assertEqual(w.level.checkpoint,6300)
    def test_cape_context_dive_preserves_double_jump(self):
        w=World();w.abilities.activate('cape');w.player.request_jump();w.update(STEP,self.assets)
        w.player.request_jump();w.update(STEP,self.assets);self.assertEqual(w.player.jumps,2)
        w.context();self.assertTrue(w.abilities.dive);self.assertEqual(w.player.velocity,750)
