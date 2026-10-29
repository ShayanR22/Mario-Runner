"""Hand-paced encounter data. Distances are in world pixels."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Encounter:
    at: int
    kind: str

@dataclass(frozen=True)
class Level:
    name: str
    subtitle: str
    biome: str
    accent: tuple
    speed: int
    lesson: str
    encounters: tuple
    length: int = 14400
    checkpoint: int = 6300
    finale_checkpoint: int = 10800

    def speed_at(self, distance):
        return self.speed + min(20, max(0, distance) / self.length * 20)

POSITIONS = (1100, 2000, 3000, 3900, 4800, 7100, 8000, 8900, 9800, 11900, 13000)
def course(kinds):
    return tuple(Encounter(at, kind) for at, kind in zip(POSITIONS, kinds))

LEVELS = (
    Level("Emerald Meadows", "GRASSLANDS", "grass", (139,230,143), 290,
          "Jump over enemies. Land on their heads to stomp and bounce.",
          course(("goomba","goomba","koopa","koopa","goomba","koopa","goomba","koopa","goomba","koopa","goomba"))),
    Level("Crystal Hollow", "UNDERGROUND", "cave", (104,221,246), 310,
          "Buzzy Beetles have hard shells. Stomp from above; jump over pipes.",
          course(("buzzy","buzzy","pipe","pipe","buzzy","buzzy","pipe","goomba","buzzy","pipe","buzzy"))),
    Level("Cloudway Crossing", "SKY", "sky", (255,219,148), 330,
          "Paratroopas bob low. High Bullet Bills pass safely overhead.",
          course(("paratroopa","paratroopa","bullet","bullet","paratroopa","bullet","paratroopa","bullet","paratroopa","bullet","paratroopa"))),
    Level("Ember Keep", "CASTLE", "castle", (255,157,112), 350,
          "Dry Bones rebuild after stomps. Watch the vents, then jump over fire.",
          course(("drybones","drybones","fire","fire","drybones","fire","drybones","fire","drybones","fire","drybones"))),
)
ENEMY_HINTS = {
    "goomba":"GOOMBA  /  Jump or stomp", "koopa":"KOOPA  /  Stomp to launch its shell",
    "buzzy":"BUZZY BEETLE  /  Stomp from above", "pipe":"PIPE  /  Jump over it",
    "paratroopa":"PARATROOPA  /  Hold jump for height", "bullet":"BULLET BILL  /  Stay low",
    "drybones":"DRY BONES  /  Stomp to collapse", "fire":"FIRE VENT  /  Watch the warning; jump",
}
