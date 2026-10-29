"""Fallback, settings and visual-layer regression tests (no GPU required)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
import pygame as pg
from runner.app import Game
from runner.rendering import Presenter,viewport
from runner.effects import environment_lights
from runner.storage import SaveData

class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.game=Game(save_path=Path(self.directory.name)/"save.json",renderer="software")
    def tearDown(self):
        self.game.presenter.close()
        pg.quit()
        self.directory.cleanup()

    def test_ce_migration(self):
        self.assertTrue(pg.IS_CE)

    def test_software_and_dummy_fallback(self):
        self.assertFalse(self.game.presenter.accelerated)
        auto=Presenter("auto")
        self.assertFalse(auto.accelerated)
        with self.assertRaisesRegex(RuntimeError,"dummy"):
            Presenter("opengl")

    def test_layers_preserve_software_composition_and_protect_actors(self):
        g=self.game
        g.start_level(0);g.action("begin");g.update(1/120);g.draw()
        composite=g.world_canvas.copy();composite.blit(g.interface_canvas,(0,0))
        self.assertEqual(pg.image.tobytes(composite,"RGB"),pg.image.tobytes(g.canvas,"RGB"))
        self.assertEqual(g.interface_canvas.get_at((400,300)).a,0)
        self.assertEqual(g.protection_canvas.get_at((150,400)).r,255)
        self.assertEqual(g.protection_canvas.get_at((300,450)).r,255)
        self.assertEqual(g.protection_canvas.get_at((500,200)).r,0)

    def test_transition_and_reduced_motion(self):
        g=self.game;g.present()
        g.action("continue")
        self.assertEqual(g.presenter.fade,0)
        g.presenter.tick(.12)
        self.assertAlmostEqual(g.presenter.fade,.5)
        g.presenter.tick(.01,True)
        self.assertEqual(g.presenter.fade,1)
        g.presenter.begin_transition(True)
        self.assertEqual(g.presenter.fade,1)

    def test_graphics_preference_survives_legacy_save(self):
        path=Path(self.directory.name)/"legacy.json"
        path.write_text('{"best":250,"volume":0.5}')
        save=SaveData(path)
        self.assertTrue(save.enhanced_effects)
        save.enhanced_effects=False;save.write()
        self.assertFalse(SaveData(path).enhanced_effects)
        self.assertEqual(SaveData(path).legacy["best"],250)

    def test_runtime_gpu_failure_falls_back(self):
        g=self.game
        broken=Mock()
        broken.render.side_effect=RuntimeError("context lost")
        g.presenter.mode="auto";g.presenter.pipeline=broken
        with self.assertLogs(level="WARNING"):
            g.present()
        self.assertIsNone(g.presenter.pipeline)
        broken.close.assert_called_once()
        self.assertEqual(pg.display.get_surface().get_size(),(960,540))

    def test_fullscreen_failure_falls_back(self):
        with patch("pygame.display.toggle_fullscreen",side_effect=pg.error("unavailable")):
            self.game.presenter.toggle_fullscreen()
        self.assertFalse(self.game.presenter.accelerated)
        self.game.present()

    def test_light_limit_and_letterboxing(self):
        g=self.game;g.save.unlocked=4;g.start_level(1,internal=True)
        self.assertLessEqual(len(environment_lights(g.world,g.scene)),8)
        self.assertEqual(viewport((1200,800)),(0,62,1200,675))
        self.assertEqual(viewport((960,540)),(0,0,960,540))
