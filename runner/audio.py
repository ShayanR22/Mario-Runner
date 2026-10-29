"""Short original synthesized cues; no media files or NumPy required."""
from array import array
import math
import pygame as pg


class Audio:
    def __init__(self, volume):
        self.volume = volume
        self.sounds = {}
        try:
            if not pg.mixer.get_init():
                pg.mixer.init(22050, -16, 1, 512)
            rate, _, channels = pg.mixer.get_init()
            for name, frequencies in {"jump": (440, 660), "double": (660, 880),
                                       "coin": (880, 1320), "hit": (180, 120, 80),
                                       "select": (520,), "stomp": (320, 240),
                                       "checkpoint": (520, 660, 880),
                                       "finish": (523, 659, 784, 1047),
                                       "fire": (330,660), "ice": (880,1108), "cat": (523,784),
                                       "star": (784,988,1175), "mega": (165,220,330),
                                       "mushroom": (330,440,660), "tanooki": (392,587),
                                       "cape": (440,698), "penguin": (740,988),
                                       "boomerang": (587,880,587), "attack": (220,440),
                                       "freeze": (1047,1320), "kick": (185,330),
                                       "damage": (220,165), "pipe": (392,294,196)}.items():
                samples = array("h")
                length = int(rate * 0.065)
                for frequency in frequencies:
                    for i in range(length):
                        fade = min(1, i / 80) * (1 - i / length)**2
                        value = int(math.sin(2 * math.pi * frequency * i / rate) * 7000 * fade)
                        samples.extend([value] * channels)
                self.sounds[name] = pg.mixer.Sound(buffer=samples)
            self.music_channel=pg.mixer.Channel(7)
            notes=(196,247,294,247,220,262,330,262)
            samples=array("h")
            length=int(rate*.32)
            for note in notes:
                for i in range(length):
                    t=i/rate;fade=min(1,i/300)*(1-i/length)**2
                    value=int((math.sin(2*math.pi*note*t)+.25*math.sin(2*math.pi*note*2*t))*900*fade)
                    samples.extend([value]*channels)
            self.music=pg.mixer.Sound(buffer=samples)
            self.music_channel.play(self.music,loops=-1);self.music_channel.set_volume(0)
        except pg.error:
            pass

    def music_volume(self,value):
        if hasattr(self,"music_channel"):self.music_channel.set_volume(value)

    @property
    def available(self):
        return bool(self.sounds)

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].set_volume(self.volume)
            self.sounds[name].play()
