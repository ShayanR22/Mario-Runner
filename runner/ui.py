"""Reusable panels and keyboard/mouse buttons on a logical canvas."""
from dataclasses import dataclass
import pygame as pg
from .config import INK, CREAM, GOLD, MINT


@dataclass
class Button:
    rect: pg.Rect
    label: str
    action: str


class UI:
    def __init__(self, assets):
        self.assets = assets
        self.buttons = []
        self.selected = 0

    def text(self, surface, text, pos, size=26, color=CREAM, title=False, center=False):
        rendered = self.assets.font(size, title).render(str(text), not title, color)
        rect = rendered.get_rect(center=pos) if center else rendered.get_rect(topleft=pos)
        surface.blit(rendered, rect)
        return rect

    @staticmethod
    def panel(surface, rect, alpha=235):
        layer = pg.Surface((rect[2], rect[3]), pg.SRCALPHA)
        layer.fill((*INK, alpha))
        surface.blit(layer, rect[:2])
        pg.draw.rect(surface, (79, 98, 111), rect, 2)
        pg.draw.rect(surface, GOLD, (rect[0], rect[1], 5, rect[3]))

    def begin(self):
        self.buttons = []

    def button(self, surface, label, action, rect, primary=False):
        index = len(self.buttons)
        rect = pg.Rect(rect)
        active = index == self.selected
        pg.draw.rect(surface, (7, 19, 31), rect.move(0, 4))
        color = GOLD if primary or active else (48, 65, 81)
        pg.draw.rect(surface, color, rect)
        if active:
            pg.draw.rect(surface, CREAM, rect.inflate(6, 6), 2)
        self.text(surface, label, rect.center, 26, INK if primary or active else CREAM, center=True)
        self.buttons.append(Button(rect, label, action))

    def hovered(self, pos):
        for i, button in enumerate(self.buttons):
            if button.rect.collidepoint(pos):
                self.selected = i
                return button.action
        return None

    def navigate(self, direction):
        if self.buttons:
            self.selected = (self.selected + direction) % len(self.buttons)

    def activate(self):
        return self.buttons[self.selected % len(self.buttons)].action if self.buttons else None
