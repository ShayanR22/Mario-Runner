"""Tunable campaign rules. Changing scoring/physics invalidates old ghosts."""
SCORING_VERSION = 3
PHYSICS_VERSION = 3
COIN = 100
STOMP = 250
SHELL = 500
ABILITY = 250
COMBO_SECONDS = 4.5
COMBO_ACTIONS = 5
RED_SET = 2400
CLEAR = 1000
CLEAN = 1000
FLAG_MAX = 3000
MEDALS = (4000, 8000, 13000)
GRACE = 1.25
STAR_SECONDS = 8.
MEGA_SECONDS = 6.
PROJECTILE_LIMIT = 3


def medal(score):
    return ("NONE", "BRONZE", "SILVER", "GOLD")[sum(score >= t for t in MEDALS)]


def rank(score):
    return "SUPERSTAR" if score >= 52000 else "EXPERT" if score >= 32000 else "ADVENTURER" if score >= 16000 else "EXPLORER"
