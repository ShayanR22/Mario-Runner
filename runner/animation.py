"""Animation selection never changes the physics body or foot anchor."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Clip:
    frames: tuple
    seconds_per_frame: float
    loop: bool = True

    def frame(self, seconds):
        index = int(max(0, seconds) / self.seconds_per_frame)
        index = index % len(self.frames) if self.loop else min(index, len(self.frames)-1)
        return self.frames[index]

def player_pose(player, elapsed, idle=False, hurt_time=None):
    if hurt_time is not None:
        return "damage", hurt_time
    if idle:
        return "idle", elapsed
    if player.land_time > 0:
        return "land", .18-player.land_time
    if player.grounded:
        return "run", elapsed
    if player.double_time > 0:
        return "double", .24-player.double_time
    return ("jump" if player.velocity < 0 else "fall"), player.air_time
