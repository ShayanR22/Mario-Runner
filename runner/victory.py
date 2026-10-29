"""Flagpole celebration. Rewards are committed before this visual state machine."""
from dataclasses import dataclass
from .config import GROUND
from . import balance as B

@dataclass
class Victory:
    grab_height: float
    phase: str = "grab"
    age: float = 0.
    phase_age: float = 0.

    @property
    def bonus(self):
        return int((500 + min(1., max(0., self.grab_height / 200)) * (B.FLAG_MAX-500)) / 100) * 100

    def update(self, dt, player, reduced=False):
        self.age += dt
        self.phase_age += dt
        phases = ("grab", "slide", "hop", "walk", "done")
        durations = {"grab": .22, "slide": .85, "hop": .4, "walk": .85}
        if reduced:
            self.phase = "done"
            player.bottom = GROUND
            return
        if self.phase == "slide":
            player.bottom = min(GROUND, GROUND-self.grab_height + self.phase_age/.85*self.grab_height)
        elif self.phase == "hop":
            t=min(1.,self.phase_age/.4)
            player.x=150+60*t
            player.bottom=GROUND-70*4*t*(1-t)
        elif self.phase == "walk":
            player.x=210+175*min(1.,self.phase_age/.85)
            player.bottom=GROUND
        if self.phase != "done" and self.phase_age >= durations[self.phase]:
            self.phase = phases[phases.index(self.phase)+1]
            self.phase_age = 0.
