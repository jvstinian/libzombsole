# coding: utf-8
from __future__ import print_function

import os
from os import path
import sys
import time
from termcolor import colored
from itertools import cycle, islice
from zombsole.rules.factory import RulesFactory
from zombsole.core import World
from zombsole.things import Box, Wall, Zombie, ObjectiveLocation, Player
from zombsole.renderer import TerminalRenderer, OpencvRenderer
from zombsole.weapons import WeaponFactory


def get_creator(module_name):
    """Get the create() function from a module."""
    module = __import__(module_name, fromlist=['create', ])
    create_function = getattr(module, 'create')

    return create_function

# More or less following the approach for player and rules
def create_agent(agent_id, weapon_name, rules_name, objectives):
    weapon = WeaponFactory.create_player_weapon(weapon_name)
    creator = get_creator('zombsole.players.agent')
    return creator(agent_id, weapon, rules_name, objectives)

def create_player(name, rules_name, objectives):
    creator = get_creator('zombsole.players.' + name)
    return creator(rules_name, objectives)

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
            # There might be a trailing newline and so the last "line" might be length 0.
            # We only process the line if it has positive length
            if line:
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

        # At this point max_row and max_col indicate the maximum index value, so we add 1 
        # to indicate the total number of rows and columns.
        max_row += 1
        max_col += 1

        return Map((max_col, max_row),
                   things,
                   player_spawns,
                   zombie_spawns,
                   objectives)

    @classmethod
    def from_map_name(cls, map_name):
        map_file = path.join(path.dirname(__file__), 'maps', map_name)
        return cls.from_file(map_file)
    
    @classmethod
    def get_map_file_location(cls, map_name):
        return path.join(path.dirname(__file__), 'maps', map_name)


class Game(object):
    """An instance of game controls the flow of the game.

       This includes player and zombies spawning, game main loop, deciding when
       to stop, importing map data, drawing each update, etc.
    """
    def __init__(self, rules_name, player_names, map_, initial_zombies=0,
                 minimum_zombies=0, debug=False,
                 use_basic_icons=False,
                 renderer=TerminalRenderer(False, debug=False),
                 agent_ids = [],
                 agent_weapons = "rifle"):
        self.players = []

        self.rules_name = rules_name
        self.rules = RulesFactory.create_rules(rules_name, self)
        self.map = map_
        self.initial_zombies = initial_zombies
        self.minimum_zombies = minimum_zombies
        self.debug = debug
        self.use_basic_icons = use_basic_icons

        self.player_names = player_names
        self.agent_ids = agent_ids
        # The following processes the provided weapon names into a list of weapon names 
        # with length matching the length of agent_ids
        self.__process_weapon_name_inputs__(agent_weapons)
        
        # Initialize world, players, agents
        self.__initialize_world__()

        self.renderer = renderer

    def __process_weapon_name_inputs__(self, agent_weapons):
        agent_count = len(self.agent_ids) if self.agent_ids else 0
        if isinstance(agent_weapons, (str,)):
            self.agent_weapons = [agent_weapons] * agent_count
        elif isinstance(agent_weapons, (list,)):
            self.agent_weapons = list(islice(cycle(agent_weapons), agent_count))
        else:
            raise ValueError(f"{agent_weapons} is not a valid value for argument agent_weapons.  Value must be the weapon name as a string or a list of weapon names.")

    def __initialize_world__(self):
        self.world = World(self.map.size, debug=self.debug)

        for thing in self.map.things:
            self.world.spawn_thing(thing)

        self.players = [create_player(name, self.rules_name,
                                      self.map.objectives)
                        for name in self.player_names]

        if self.agent_ids:
            self.agents = [create_agent(agent_id, weapon_name, self.rules_name, self.map.objectives)
                           for agent_id, weapon_name in zip(self.agent_ids, self.agent_weapons)]
        else:
            self.agents = []

        self.spawn_players()
        self.spawn_agents()
        self.spawn_zombies(self.initial_zombies)

    # Return both players and agents
    def get_all_players(self):
        return (self.players + self.agents)

    def get_agents_health(self):
        return sum([thing.life for thing in self.agents])

    def get_players_health(self):
        return sum([thing.life for thing in self.players])

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

                print('')
                if won:
                    print(colored(u'WIN! ', 'green'))
                else:
                    print(colored(u'GAME OVER ', 'red'))
                print(description)

                return won, description

    def draw(self):
        allplayers = sorted(self.agents, key=lambda x: x.agent_id) + sorted(self.players, key=lambda x: x.name)
        self.renderer.render(self.world, allplayers)

