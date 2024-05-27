# coding: utf-8
from __future__ import print_function

import os
import sys
import time

from termcolor import colored

from zombsole.core import World
from zombsole.things import Box, Wall, Zombie, ObjectiveLocation, Player


def get_creator(module_name):
    """Get the create() function from a module."""
    module = __import__(module_name, fromlist=['create', ])
    create_function = getattr(module, 'create')

    return create_function

# More or less following the approach for player and rules
def create_agent(agent_id, rules_name, objectives):
    from zombsole.weapons import Rifle
    creator = get_creator('zombsole.players.agent')
    return creator(agent_id, Rifle(), rules_name, objectives)

def create_player(name, rules_name, objectives):
    creator = get_creator('zombsole.players.' + name)
    return creator(rules_name, objectives)


def create_rules(name, game):
    creator = get_creator('zombsole.rules.' + name)
    return creator(game)


class Rules(object):
    """Rules to decide when a game ends, and when it's won."""
    def __init__(self, game):
        self.game = game

    def players_alive(self):
        """Are there any alive players?"""
        for player in (self.game.players + self.game.agents):
            if player.life > 0:
                return True
        return False

    def game_ended(self):
        """Has the game ended?"""
        return not self.players_alive()

    def game_won(self):
        """Was the game won?"""
        if self.players_alive():
            # never should happen, but illustrative
            return True, u'you won a game that never ends (?!)'
        else:
            return False, u'everybody is dead :('


class Map(object):
    """A map for a world."""
    def __init__(self, size, things, player_spawns=None, zombie_spawns=None,
                 objectives=None):
        self.size = size
        self.things = things
        self.player_spawns = player_spawns
        self.zombie_spawns = zombie_spawns
        self.objectives = objectives

    @classmethod
    def from_file(cls, file_path):
        """Import data from a utf-8 map file."""
        zombie_spawns = []
        player_spawns = []
        objectives = []
        things = []

        max_row = 0
        max_col = 0

        # read the file
        encoding = 'utf-8'
        if sys.version_info > (3,):
            with open(file_path, encoding=encoding) as map_file:
                lines = map_file.read().split('\n')
        else:
            with open(file_path) as map_file:
                lines = map_file.read().decode(encoding).split('\n')

        # for each char, create the corresponding object
        for row_index, line in enumerate(lines):
            max_row = row_index

            for col_index, char in enumerate(line):
                if char:
                    max_col = max(col_index, max_col)

                position = (col_index, row_index)
                if char in (Box.ICON, 'b', 'B'):
                    things.append(Box(position))
                elif char in (Wall.ICON, 'w', 'W'):
                    things.append(Wall(position))
                elif char.lower() == 'p':
                    player_spawns.append(position)
                elif char.lower() == 'z':
                    zombie_spawns.append(position)
                elif char.lower() == 'o':
                    objectives.append(position)
                    things.append(ObjectiveLocation(position))

        return Map((max_col, max_row),
                   things,
                   player_spawns,
                   zombie_spawns,
                   objectives)


class Game(object):
    """An instance of game controls the flow of the game.

       This includes player and zombies spawning, game main loop, deciding when
       to stop, importing map data, drawing each update, etc.
    """
    def __init__(self, rules_name, player_names, map_, initial_zombies=0,
                 minimum_zombies=0, debug=False,
                 use_basic_icons=False, use_arduino=False,
                 arduino_device='/dev/ttyACM0', arduino_bauds=9600,
                 agent_ids = []):
        self.players = []
        self.arduino_serial = None

        self.rules_name = rules_name
        self.rules = get_creator('zombsole.rules.' + rules_name)(self)
        self.map = map_
        self.initial_zombies = initial_zombies
        self.minimum_zombies = minimum_zombies
        self.debug = debug
        self.use_basic_icons = use_basic_icons
        self.use_arduino = use_arduino
        self.arduino_device = arduino_device
        self.arduino_bauds = arduino_bauds

        self.player_names = player_names
        self.agent_ids = agent_ids
        
        self.thing_labels = {
            '@': 1,
            '=': 2,
            '*': 3,
            '#': 4,
            'x': 5,
            'P': 6,
            'A': 7,
        }
        self.weapon_labels = {
            'ZombieClaws': 1,
            'Knife': 10,
            'Axe': 11,
            'Gun': 12,
            'Rifle': 13,
            'Shotgun': 14
        }

        # Initialize world, players, agents
        self.__initialize_world__()

    def __initialize_world__(self):
        self.world = World(self.map.size, debug=self.debug)

        for thing in self.map.things:
            self.world.spawn_thing(thing)

        self.players = [create_player(name, self.rules_name,
                                      self.map.objectives)
                        for name in self.player_names]

        if self.agent_ids:
            self.agents = [create_agent(agent_id, self.rules_name, self.map.objectives)
                           for agent_id in self.agent_ids]
        else:
            self.agents = []

        self.spawn_players()
        self.spawn_agents()
        self.spawn_zombies(self.initial_zombies)

        if self.use_arduino:
            self.initialize_arduino()

    def get_agents_health(self):
        return sum([thing.life for thing in self.agents])

    def get_players_health(self):
        return sum([thing.life for thing in self.players])

    def initialize_arduino(self):
        """Initialize serial connection with arduino screen."""
        from serial import Serial
        self.arduino_serial = Serial(self.arduino_device,
                                     self.arduino_bauds)

    def spawn_players(self):
        """Spawn players using the provided player create functions."""
        self.world.spawn_in_random(self.players, self.map.player_spawns)

    def spawn_agents(self):
        """Spawn agents using the provided player create functions."""
        self.world.spawn_in_random(self.agents, self.map.player_spawns)

    def spawn_zombies(self, count):
        """Spawn N zombies in the world."""
        zombies = [Zombie() for _ in range(count)]
        self.world.spawn_in_random(zombies,
                                   self.map.zombie_spawns,
                                   fail_if_cant=False)

    def spawn_zombies_to_maintain_minimum(self):
        # maintain the flow of zombies if necessary
        zombies = [thing for thing in self.world.things.values()
                    if isinstance(thing, Zombie)]
        if len(zombies) < self.minimum_zombies:
            self.spawn_zombies(self.minimum_zombies - len(zombies))

    def position_draw(self, position):
        """Get the string to draw for a given position of the world."""
        # decorations first, then things over them
        thing = (self.world.things.get(position) or
                 self.world.decoration.get(position))

        if thing is not None:
            if self.use_basic_icons:
                icon = thing.icon_basic
            else:
                icon = thing.icon
            return colored(icon, thing.color)
        else:
            return u' '

    def encode_position_as_channels(self, position):
        """Get the character to draw for a given position of the world."""
        # decorations first, then things over them
        thing = (self.world.things.get(position) or
                 self.world.decoration.get(position))

        if thing is not None:
            life = getattr(thing, 'life', 0)
            weapon = getattr(thing, 'weapon', None)
            weapon_name = weapon.name if weapon is not None else 'none'
            weapon_code = self.weapon_labels.get(weapon_name, 0)
            return [
                ord(thing.icon_basic),
                life,
                weapon_code
            ]
        else:
            return [0, 0, 0]
    
    def encode_position_simple(self, position):
        """Get the character to draw for a given position of the world."""
        # decorations first, then things over them
        thing = (self.world.things.get(position) or
                 self.world.decoration.get(position))

        if thing is not None:
            scaled_life = 16*getattr(thing, 'life', 0)//100
            thing_code = self.thing_labels.get(thing.icon_basic, 0)
            weapon = getattr(thing, 'weapon', None)
            weapon_name = weapon.name if weapon is not None else 'none'
            weapon_code = self.weapon_labels.get(weapon_name, 0)
            return 16*16*thing_code + 16*weapon_code + scaled_life
        else:
            return 0 
    
    def encode_world_simple(self):
        """Render the world as an array of characters."""
        return [
            [self.encode_position_simple((x, y)) for x in range(self.world.size[0])]
            for y in range(self.world.size[1])
        ]

    def play(self, frames_per_second=2.0):
        """Game main loop, ending in a game result with description."""
        while True:
            self.world.step()

            # maintain the flow of zombies if necessary
            zombies = [thing for thing in self.world.things.values()
                       if isinstance(thing, Zombie)]
            if len(zombies) < self.minimum_zombies:
                self.spawn_zombies(self.minimum_zombies - len(zombies))

            self.draw()

            if self.debug:
                if sys.version_info > (3,):
                    input()
                else:
                    raw_input()
            else:
                time.sleep(1.0 / frames_per_second)

            if self.rules.game_ended():
                won, description = self.rules.game_won()

                if self.use_arduino:
                    if won:
                        self.arduino('g', True)  # "gwin!!"
                    else:
                        self.arduino('l', True)  # lose

                print('')
                if won:
                    print(colored(u'WIN! ', 'green'))
                else:
                    print(colored(u'GAME OVER ', 'red'))
                print(description)

                return won, description

    def arduino(self, data, add_end_chars=False):
        """Send an order to the arduino screen."""
        if add_end_chars:
            data += chr(1) * 2
        self.arduino_serial.write(data)

    def draw_world(self):
        """Draw the world."""
        screen = ''

        # print the world
        screen += '\n'.join(u''.join(self.position_draw((x, y))
                                     for x in range(self.world.size[0]))
                            for y in range(self.world.size[1]))

        # game stats
        screen += '\nticks: %i deaths: %i' % (self.world.t, self.world.deaths)

        # print player stats
        players = sorted(self.agents, key=lambda x: x.agent_id) + sorted(self.players, key=lambda x: x.name)
        for player in players:
            try:
                weapon_name = player.weapon.name
            except:
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
                                  for t, thing, event in self.world.events
                                  if t == self.world.t])
        return screen # screen.encode('utf-8', errors='ignore') # TODO: cleanup

    def draw(self):
        # TODO: Call draw_world()
        """Draw the world."""
        screen = ''

        # print the world
        screen += '\n'.join(u''.join(self.position_draw((x, y))
                                     for x in range(self.world.size[0]))
                            for y in range(self.world.size[1]))

        # game stats
        screen += '\nticks: %i deaths: %i' % (self.world.t, self.world.deaths)

        # print player stats
        players = sorted(self.players, key=lambda x: x.name)
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
                                  for t, thing, event in self.world.events
                                  if t == self.world.t])
        os.system('clear')
        print(screen) # screen.encode('utf-8', errors='ignore') # TODO: cleanup

        # if using arduino screen, send data
        if self.use_arduino:
            for thing in self.world.things.values():
                if isinstance(thing, Player):
                    icon = 'p'
                else:
                    icon = thing.__class__.__name__[0].lower()

                self.arduino(
                    icon + chr(thing.position[0]) + chr(thing.position[1]))
            self.arduino('r', True)
