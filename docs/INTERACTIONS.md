# Enemy and ability interactions

All responses are defined in `runner/interactions.py` and exercised by the collision system. Star/Mega also grant contact immunity to hazards they do not destroy. Frozen blocks are nonblocking, kickable and shatterable; thawing next to Mario grants brief grace.

| Enemy | Stomp | Shell | Fire | Ice | Claw | Tail | Star | Mega |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GOOMBA | Defeat | Defeat | Defeat | Freeze 4s / second hit shatters | Defeat | Defeat | Defeat | Defeat |
| KOOPA | Launch shell | Defeat | Defeat | Freeze 4s / second hit shatters | Defeat | Defeat | Defeat | Defeat |
| BUZZY | Defeat | Defeat | Resists | Freeze 4s / second hit shatters | Resists | Defeat | Defeat | Defeat |
| PARATROOPA | Defeat | Defeat | Defeat | Freeze 4s / second hit shatters | Defeat | Defeat | Defeat | Defeat |
| DRYBONES | Collapse / rebuild | Defeat | Resists | Freeze 4s / second hit shatters | Collapse / rebuild | Collapse / rebuild | Defeat | Defeat |
| BULLET | Resists | Resists | Resists | Resists | Resists | Resists | Defeat | Defeat |
| FIRE | Resists | Resists | Resists | Resists | Resists | Resists | Resists | Resists |
| PIPE | Resists | Resists | Resists | Resists | Resists | Resists | Resists | Defeat |

Boomerangs and Cape use the tail response; Penguin uses ice shots and the shell response while sliding. Cat uses claws, including during its aerial dive. Tanooki uses tail. Mushroom absorbs damage without an attack. Mega only breaks ordinary enemy/pipe objects, never level structures.

Defeat rewards use an enemy ID independent of method. Collapse can award once; rebuilding, freeze/thaw cycles, repeated melee contacts, and returning-projectile contact do not award the same enemy again. Ice freezing itself gives no points; the subsequent defeat/kick chain does. Normal ability defeats are 250 base points; launched shell defeats are 500.
