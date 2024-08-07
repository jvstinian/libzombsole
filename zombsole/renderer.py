import os
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from termcolor import colored

from zombsole.core import (World, Thing)
from zombsole.things import (Wall, Box, Zombie, Player, ObjectiveLocation, DeadBody)


class GameRenderer(ABC):
    @abstractmethod
    def render(self, world: World, players):
        pass

class TerminalRenderer(GameRenderer):
    def __init__(self, use_basic_icons, debug=False):
        self.use_basic_icons = use_basic_icons
        self.debug = debug

    def _position_draw(self, world, position):
        """Get the string to draw for a given position of the world."""
        # decorations first, then things over them
        thing = (world.things.get(position) or
                 world.decoration.get(position))

        if thing is not None:
            if self.use_basic_icons:
                icon = thing.icon_basic
            else:
                icon = thing.icon
            return colored(icon, thing.color)
        else:
            return u' '

    def _draw(self, world: World, players):
        """Draw the world."""
        screen = ''

        # print the world
        screen += '\n'.join(u''.join(self._position_draw(world, (x, y))
                            for x in range(world.size[0]))
                            for y in range(world.size[1]))

        # game stats
        screen += '\nticks: %i deaths: %i' % (world.t, world.deaths)

        # print player stats
        players = sorted(players, key=lambda x: x.name)
        for player in players:
            try:
                weapon_name = player.weapon.name
            except AttributeError:
                weapon_name = u'unarmed'

            if player.life > 0:
                # a small "health bar" with unicode chars, from 0 to 10 chars
                life_chars_count = int((10.0 / player.MAX_LIFE) * player.life)
                life_chars = life_chars_count * u'\u2588'
                no_life_chars = (10 - life_chars_count) * u'\u2591'
                life_bar = u'\u2665 %s%s' % (life_chars, no_life_chars)
            else:
                life_bar = u'\u2620 [dead]'

            player_stats = u'%s %s <%i %s %s>: %s' % (life_bar,
                                                      player.name,
                                                      player.life,
                                                      str(player.position),
                                                      weapon_name,
                                                      player.status or u'-')

            screen += '\n' + colored(player_stats, player.color)

        # print events (of last step) for debugging
        if self.debug:
            screen += u'\n'
            screen += u'\n'.join([colored(u'%s: %s' % (thing.name, event),
                                          thing.color)
                                  for t, thing, event in world.events
                                  if t == world.t])
        return screen

    def render(self, world: World, players):
        screen = self._draw(world, players)
        os.system('clear')
        print(screen)
    

class OpencvRenderer(GameRenderer):
    def __init__(self, gridwidth, gridheight, cellwidth = 10, cellheight = 10):
        self.counter = 0
        self.cellwidth = cellwidth
        self.cellheight = cellheight
        self.imagewidth = cellwidth * gridwidth
        self.imageheight = cellheight * gridheight
        self.lifebar_width = 20

    def _draw_x(self, img: ImageDraw, x: int, y: int, color, boxwidth: int=1, boxheight: int=1, width: int=1):
        img.line(
            [
                (x * self.cellwidth, y * self.cellheight),
                ((x + boxwidth) * self.cellwidth, (y + boxheight) * self.cellheight),
            ],
            fill=color,
            width=width
        )
        img.line(
            [
                ((x + boxwidth) * self.cellwidth, y * self.cellheight),
                (x * self.cellwidth, (y + boxheight) * self.cellheight),
            ],
            fill=color,
            width=width
        )

    def _render_wall(self, img: ImageDraw, x: int, y: int, color):
        img.rectangle(
            [
                (x * self.cellwidth, y * self.cellheight),
                ((x + 1) * self.cellwidth, (y + 1) * self.cellheight),
            ],
            fill=color,
            outline=None,
        )

    def _draw_rectangle(self, img: ImageDraw, x: int, y: int, color):
        img.rectangle(
            [
                (x * self.cellwidth, y * self.cellheight),
                ((x + 1) * self.cellwidth, (y + 1) * self.cellheight),
            ],
            fill=None,
            outline=color,
            width=2
        )

    def _render_box(self, img, x: int, y: int, color):
        self._draw_rectangle(img, x, y, color)
        self._draw_x(img, x, y, color)
    
    # `circle` method is introduced for ImageDraw in version 10.4.0
    # def _draw_circle(self, img, x: int, y: int, color):
    #     img.circle(
    #         (x * self.cellwidth + self.cellwidth / 2, y * self.cellheight + self.cellheight / 2),
    #         self.cellwidth / 2,
    #         fill = None,
    #         outline = color,
    #         width = 1
    #     )

    # def _draw_solid_circle(self, img, x: int, y: int, color):
    #     img.circle(
    #         (x * self.cellwidth + self.cellwidth / 2, y * self.cellheight + self.cellheight / 2),
    #         self.cellwidth / 2,
    #         fill = color,
    #         width = 1
    #     )

    def _draw_ellipse(self, img: ImageDraw, x: int, y: int, color):
        img.ellipse(
            [
                (x * self.cellwidth, y * self.cellheight),
                ((x + 1) * self.cellwidth, (y + 1) * self.cellheight),
            ],
            fill = None,
            outline = color,
            width = 1
        )

    def _draw_solid_ellipse(self, img: ImageDraw, x: int, y: int, color):
        img.ellipse(
            [
                (x * self.cellwidth, y * self.cellheight),
                ((x + 1) * self.cellwidth, (y + 1) * self.cellheight),
            ],
            fill = color,
            width = 1
        )

    def _render_zombie(self, img: ImageDraw, x: int, y: int, color):
        self._draw_solid_ellipse(img, x, y, color)

    def _render_player(self, img: ImageDraw, x: int, y: int, color):
        self._draw_solid_ellipse(img, x, y, color)

    def _render_thing(self, img: ImageDraw, x: int, y: int, thing: Thing):
        if isinstance(thing, (Wall,)):
            self._render_wall(img, x, y, thing.color)
        elif isinstance(thing, (Box,)):
            self._render_box(img, x, y, thing.color)
        elif isinstance(thing, (Zombie,)):
            self._render_zombie(img, x, y, thing.color)
        elif isinstance(thing, (Player,)):
            self._render_player(img, x, y, thing.color)
        elif isinstance(thing, (ObjectiveLocation,)):
            self._draw_rectangle(img, x, y, thing.color)
        elif isinstance(thing, (DeadBody,)):
            self._draw_ellipse(img, x, y, thing.color)
            self._draw_x(img, x, y, thing.color)

    def _render_player_lifebar(self, img, x: int, y: int, player: Player):
        life_pixels_count = int(self.lifebar_width * self.cellwidth  * player.life / player.MAX_LIFE)
        img.rectangle(
            [ 
                (x * self.cellwidth, y * self.cellheight),
                ((x + self.lifebar_width) * self.cellwidth, (y + 1) * self.cellheight)
            ],
            fill=None,
            outline=player.color if life_pixels_count > 0 else "red",
            width=2
        )
        if life_pixels_count > 0:
            # Here we use the custom life bar width, rather than coloring 
            # a specified number of cells
            img.rectangle(
                [ 
                    (x * self.cellwidth, y * self.cellheight),
                    (x * self.cellwidth + life_pixels_count, (y + 1) * self.cellheight)
                ],
                fill=player.color,
                outline=None,
                width=2
            )
        else:
            self._draw_x(img, x, y, "red", boxwidth=self.lifebar_width, boxheight=1, width=3)

    def render(self, world: World, players):
        image = Image.new("RGB", (self.imagewidth, self.imageheight), "black")
        img = ImageDraw.Draw(image)

        # print the world
        for x in range(world.size[0]):
            for y in range(world.size[1]):
                position = (x, y)
                thing = (world.things.get(position) or world.decoration.get(position))
                if thing is not None:
                    self._render_thing(img, x, y, thing)
        
        # game stats
        img.text((0, world.size[1] * self.cellheight),  f"ticks: {world.t} deaths: {world.deaths}", font=None, fill="yellow", anchor="la", font_size=14)

        # print player stats
        for idx, player in enumerate(players):
            try:
                weapon_name = player.weapon.name
            except AttributeError:
                weapon_name = u'unarmed'

            self._render_player_lifebar(
                img, 
                1,
                world.size[1] + 2 + 1 * idx,
                player
            )

            player_stats = u'%s <%i %s %s>: %s' % (player.name,
                                                   player.life,
                                                   str(player.position),
                                                   weapon_name,
                                                   player.status or u'-')

            img.text(((1 + self.lifebar_width + 1) * self.cellwidth, (world.size[1] + 2 + 1 * idx) * self.cellheight),  player_stats, font=None, fill=player.color, anchor="la", font_size=8)

        open_cv_image = np.array(image)
        # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()

        cv2.imshow("zombsole", open_cv_image)
        cv2.waitKey(100)

