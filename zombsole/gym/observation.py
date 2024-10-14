from abc import ABC, abstractmethod
from typing import Tuple
from gym.spaces import Box
from zombsole.game import Game
from zombsole.things import Wall
import numpy as np


class SinglePlayerObservation(ABC):
    @abstractmethod
    def get_observation(self, game: Game):
        pass
    
    @abstractmethod
    def get_observation_space(self):
        pass
    
    thing_labels = {
        '@': 1,
        '=': 2,
        '*': 3,
        '#': 4,
        'x': 5,
        'P': 6,
        'A': 7,
    }
    weapon_labels = {
        'ZombieClaws': 1,
        'Knife': 10,
        'Axe': 11,
        'Gun': 12,
        'Rifle': 13,
        'Shotgun': 14
    }

    @staticmethod
    def encode_position_simple(world, position):
        """Get the character to draw for a given position of the world."""
        # decorations first, then things over them
        if world.within_bounds(position):
            thing = (world.things.get(position) or
                     world.decoration.get(position))
        else:
            thing = Wall(position) # Note the position is out of bounds here

        if thing is not None:
            adj_life = min(getattr(thing, 'life', 0), 100)
            scaled_life = 15*adj_life//100
            thing_code = SinglePlayerObservation.thing_labels.get(thing.icon_basic, 0)
            weapon = getattr(thing, 'weapon', None)
            weapon_name = weapon.name if weapon is not None else 'none'
            weapon_code = SinglePlayerObservation.weapon_labels.get(weapon_name, 0)
            return 16*16*thing_code + 16*weapon_code + scaled_life
        else:
            return 0 

    @staticmethod
    def encode_position_as_channels(world, position):
        """Get the character to draw for a given position of the world."""
        # decorations first, then things over them
        if world.within_bounds(position):
            thing = (world.things.get(position) or
                     world.decoration.get(position))
        else:
            thing = Wall(position) # Note the position is out of bounds here

        if thing is not None:
            life = getattr(thing, 'life', 0)
            weapon = getattr(thing, 'weapon', None)
            weapon_name = weapon.name if weapon is not None else 'none'
            weapon_code = SinglePlayerObservation.weapon_labels.get(weapon_name, 0)
            thing_code = SinglePlayerObservation.thing_labels.get(thing.icon_basic, 0)
            if thing_code == 7: # agent
                thing_code = 8 + int(thing.agent_id)
            return [
                thing_code,
                life,
                weapon_code
            ]
        else:
            return [0, 0, 0]
    
    @classmethod
    def encode_world_simple(cls, world):
        """Render the world as an array of characters."""
        return [
            [cls.encode_position_simple(world, (x, y)) for x in range(world.size[0])]
            for y in range(world.size[1])
        ]
    
    @classmethod
    def encode_world_with_channels(cls, world):
        """Render the world using channels."""
        return [
            [cls.encode_position_as_channels(world, (x, y)) for x in range(world.size[0])]
            for y in range(world.size[1])
        ]

    @classmethod
    def encode_surroundings_simple(cls, world, position: Tuple[int, int], surroundings_half_width: int):
        """Render the surroundings using characters."""
        xrange = range(position[0] - surroundings_half_width, position[0] + surroundings_half_width + 1)
        yrange = range(position[1] - surroundings_half_width, position[1] + surroundings_half_width + 1)

        return [
            [cls.encode_position_simple(world, (x, y)) for x in xrange]
            for y in yrange
        ]

    @classmethod
    def encode_surroundings_with_channels(cls, world, position: Tuple[int, int], surroundings_half_width: int):
        """Render the surroundings using channels."""
        xrange = range(position[0] - surroundings_half_width, position[0] + surroundings_half_width + 1)
        yrange = range(position[1] - surroundings_half_width, position[1] + surroundings_half_width + 1)

        return [
            [cls.encode_position_as_channels(world, (x, y)) for x in xrange]
            for y in yrange
        ]
    

class WorldSimpleObservation(SinglePlayerObservation):
    def __init__(self, map_size: Tuple[int, int]):
        self.map_size = map_size

    def get_observation(self, game: Game):
        observation = np.array(SinglePlayerObservation.encode_world_simple(game.world))
        return observation.reshape( (1,) + observation.shape )

    def get_observation_space(self):
        return Box(low=0, high=8*16*16, shape=(1, self.map_size[1], self.map_size[0]), dtype=np.int32)


class WorldChannelsObservation(SinglePlayerObservation):
    def __init__(self, map_size: Tuple[int, int]):
        self.map_size = map_size

    def get_observation(self, game: Game):
        return np.array(SinglePlayerObservation.encode_world_with_channels(game.world)).transpose((2, 0, 1))

    def get_observation_space(self):
        return Box(low=0, high=128, shape=(3, self.map_size[1], self.map_size[0]), dtype=np.int32)


class SurroundingsSimpleObservation(SinglePlayerObservation):
    def __init__(self, surroundings_width: int):
        self.width = surroundings_width
        self.half_width = surroundings_width // 2

    def get_observation(self, game: Game):
        agent = game.agents[0]
        observation = np.array(SinglePlayerObservation.encode_surroundings_simple(game.world, agent.position, self.half_width))
        return observation.reshape( (1,) + observation.shape )

    def get_observation_space(self):
        return Box(low=0, high=8*16*16, shape=(1, self.width, self.width), dtype=np.int32)


class SurroundingsChannelsObservation(SinglePlayerObservation):
    def __init__(self, surroundings_width: int):
        self.width = surroundings_width
        self.half_width = surroundings_width // 2

    def get_observation(self, game: Game):
        agent = game.agents[0]
        return np.array(SinglePlayerObservation.encode_surroundings_with_channels(game.world, agent.position, self.half_width)).transpose((2, 0, 1))

    def get_observation_space(self):
        return Box(low=0, high=128, shape=(3, self.width, self.width), dtype=np.int32)


def build_observation(scope: str, position_encoding_style: str, map_size: Tuple[int, int]) -> SinglePlayerObservation:
    lscope = scope.lower()
    is_world_scope = False
    surroundings_width = None
    if lscope in ["world", "map"]:
        is_world_scope = True
    elif lscope.startswith("surroundings"):
        is_world_scope = False
        surroundings_width = int(lscope[len("surroundings:"):])
        if (surroundings_width % 2 == 0) or (surroundings_width <= 1):
            raise ValueError("surroundings width must be an odd number greater than 1")
    else:
        raise ValueError(f"{scope} is not a valid observation scope, must be \"world\", \"map\", or of the form \"surroundings:i\" where i is an integer")
    
    lpes = position_encoding_style.lower()
    if not (lpes in ["simple", "channels"]):
        raise ValueError(f"{lpes} must be \"simple\" or \"channels\"")

    if is_world_scope:
        if lpes == "simple":
            return WorldSimpleObservation(map_size)
        else:
            return WorldChannelsObservation(map_size)
    else:
        if lpes == "simple":
            return SurroundingsSimpleObservation(surroundings_width)
        else:
            return SurroundingsChannelsObservation(surroundings_width)

