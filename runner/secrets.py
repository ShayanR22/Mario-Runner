"""Short optional room; main encounters and distance remain frozen."""
from dataclasses import dataclass,field
from .config import GROUND

@dataclass
class BonusRoom:
    distance: float = 0.
    age: float = 0.
    collected: set = field(default_factory=set)
    return_bottom: float = GROUND
    length: float = 1650.

    @property
    def coins(self):return [(250+i*100,GROUND-35-(i%3)*32,f"secret:{i}") for i in range(12)]
