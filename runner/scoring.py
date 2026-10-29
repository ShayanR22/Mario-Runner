"""Skill scoring with stable reward IDs and opportunity-aware combo timing."""
from dataclasses import dataclass, field
from . import balance as B

@dataclass
class Score:
    points: int = 0
    actions: int = 0
    remaining: float = 0.
    awarded: set = field(default_factory=set)
    air_chain: int = 0
    last_style: str = ""

    @property
    def multiplier(self):
        return min(5, 1 + self.actions // B.COMBO_ACTIONS)

    def award(self, identity, value, action=True, style=""):
        if identity in self.awarded:
            return 0
        self.awarded.add(identity)
        amount = value * (self.multiplier if action else 1)
        self.points += amount
        if action:
            self.actions += 1
            self.remaining = B.COMBO_SECONDS
            if style and self.last_style and style != self.last_style:
                # A small fixed variety bonus, once for this already unique action.
                self.points += 50
                amount += 50
            if style:
                self.last_style = style
        return amount

    def update(self, dt, opportunity):
        if opportunity and self.remaining > 0:
            self.remaining = max(0., self.remaining - dt)
            if not self.remaining:
                self.actions = 0
                self.last_style = ""

    def damage(self):
        self.actions = 0
        self.remaining = 0.
        self.air_chain = 0
        self.last_style = ""

    def dump(self):
        return {"points": self.points, "actions": self.actions, "remaining": self.remaining,
                "awarded": sorted(self.awarded), "air_chain": self.air_chain, "last_style": self.last_style}

    @classmethod
    def load(cls, value):
        if not isinstance(value, dict):
            return cls()
        from .storage import integer, number, strings
        return cls(integer(value.get("points")), integer(value.get("actions"), upper=10000),
                   number(value.get("remaining"), 0, B.COMBO_SECONDS),
                   set(strings(value.get("awarded", []))),
                   integer(value.get("air_chain"), upper=100), str(value.get("last_style", ""))[:24])
