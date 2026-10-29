"""Explicit vulnerabilities, shared by projectiles, melee and contact effects."""
# defeat / freeze / collapse / block. No damage path depends on sprite color.
METHODS=("stomp","shell","fire","ice","claw","tail","star","mega")
ROWS={
 "goomba":("defeat","defeat","defeat","freeze","defeat","defeat","defeat","defeat"),
 "koopa":("shell","defeat","defeat","freeze","defeat","defeat","defeat","defeat"),
 "buzzy":("defeat","defeat","block","freeze","block","defeat","defeat","defeat"),
 "paratroopa":("defeat","defeat","defeat","freeze","defeat","defeat","defeat","defeat"),
 "drybones":("collapse","defeat","block","freeze","collapse","collapse","defeat","defeat"),
 "bullet":("block","block","block","block","block","block","defeat","defeat"),
 "fire":("block",)*8,
 "pipe":("block",)*7+("defeat",),
}
def response(kind,method):return ROWS.get(kind,("block",)*8)[METHODS.index(method)] if method in METHODS else "block"
