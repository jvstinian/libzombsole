#!/usr/bin/env python
# coding: utf-8
from os import path, system
from abc import ABC, abstractmethod
from typing import Tuple
from gym.core import Env
from gym.spaces import Box
from gym.spaces.discrete import Discrete
from zombsole.game import Game, Map
from zombsole.renderer import NoRender
from zombsole.players.agent import Agent
from zombsole.things import Wall
import time
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
            scaled_life = 16*getattr(thing, 'life', 0)//100
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
        """Render the surroundings using channels."""
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
        # observation = np.array(game.encode_world_simple())
        observation = np.array(SinglePlayerObservation.encode_world_simple(game.world))
        return observation.reshape( (1,) + observation.shape )

    def get_observation_space(self):
        return Box(low=0, high=8*16*16, shape=(1, self.map_size[1], self.map_size[0]), dtype=np.int32)


class WorldChannelsObservation(SinglePlayerObservation):
    def __init__(self, map_size: Tuple[int, int]):
        self.map_size = map_size

    def get_observation(self, game: Game):
        return np.array(SinglePlayerObservation.encode_world_with_channels(game.world)).transpose((2, 0, 1))
        # return np.array(game.encode_world_with_channels())

    def get_observation_space(self):
        return Box(low=0, high=128, shape=(3, self.map_size[1], self.map_size[0]), dtype=np.int32)


class SurroundingsSimpleObservation(SinglePlayerObservation):
    def __init__(self, surroundings_width: int):
        self.width = surroundings_width
        self.half_width = surroundings_width // 2

    def get_observation(self, game: Game):
        agent = game.agents[0]
        observation = np.array(SinglePlayerObservation.encode_surroundings_simple(game.world, agent.position, self.half_width))
        # observation = np.array(game.encode_surroundings_simple(agent.position, self.half_width))
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
        # return np.array(game.encode_surroundings_with_channels(agent.position, self.half_width))

    def get_observation_space(self):
        return Box(low=0, high=128, shape=(self.width, self.width, 3), dtype=np.int32)


def build_observation(scope: str, position_encoding_style: str, map_size: Tuple[int, int]):
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


class ZombsoleGymEnv(object):
    """The main OpenAI Gym class. It encapsulates an environment with
    arbitrary behind-the-scenes dynamics. An environment can be
    partially or fully observed.

    The main API methods that users of this class need to know are:

        step
        reset
        render
        close
        seed

    And set the following attributes:

        action_space: The Space object corresponding to valid actions
        observation_space: The Space object corresponding to valid observations
        reward_range: A tuple corresponding to the min and max possible rewards

    The methods are accessed publicly as "step", "reset", etc...
    """
    # See the supported modes in the render method
    metadata = {
        'render.modes': ['human']
    }
    reward_range = (-float('inf'), float('inf'))
    game_actions = [
        { 
            'action_type': 'move',
            'parameter': [0, 1]
        },
        { 
            'action_type': 'move',
            'parameter': [-1, 0]
        },
        { 
            'action_type': 'move',
            'parameter': [0, -1]
        },
        { 
            'action_type': 'move',
            'parameter': [1, 0]
        },
        {
            'action_type': 'attack_closest'
        },
        {
            'action_type': 'heal'
        }
    ]
    # Set these in ALL subclasses
    action_space = Discrete(len(game_actions))
    # setting observation_space in the constructor

    def __init__(self, rules_name, player_names, map_name, agent_id, initial_zombies=0,
                 minimum_zombies=0, renderer=NoRender(), 
                 observation_scope="world", observation_position_encoding="simple", 
                 debug=False):
        fdir = path.dirname(path.abspath(__file__))
        map_file = path.join(fdir, 'maps', map_name)
        map_ = Map.from_file(map_file)

        self.game = Game(
            rules_name, player_names, map_,
            initial_zombies=initial_zombies, minimum_zombies=minimum_zombies,
            use_basic_icons=True,
            agent_ids=[agent_id],
            renderer=renderer,
            debug=debug,
        )

        self.observation_handler = build_observation(
                observation_scope, observation_position_encoding, map_.size
        )
        # self.observation_handler = WorldSimpleObservation(map_.size)

        # self.observation_space = Box(low=0, high=8*16*16, shape=(1, self.game.world.size[1], self.game.world.size[0]), dtype=np.int32)
        self.observation_space = self.observation_handler.get_observation_space()

    def get_observation(self):
        return self.observation_handler.get_observation(self.game)
        # observation = np.array(self.game.encode_world_simple())
        # return observation.reshape( (1,) + observation.shape )
    
    def get_frame_size(self):
        return tuple(reversed(self.game.map.size))

    def step(self, action):
        """Run one timestep of the environment's dynamics. When end of
        episode is reached, you are responsible for calling `reset()`
        to reset this environment's state.

        Accepts an action and returns a tuple (observation, reward, done, info).

        Args:
            action (object): an action provided by the agent

        Returns:
            observation (object): agent's observation of the current environment
            reward (float) : amount of reward returned after previous action
            done (bool): whether the episode has ended, in which case further step() calls will return undefined results
            info (dict): contains auxiliary diagnostic information (helpful for debugging, and sometimes learning)
        """
        game_action = self.game_actions[action]
        self.game.agents[0].set_action(game_action)

        frames_per_second=None

        zombie_deaths_0 = self.game.world.zombie_deaths 
        # player_deaths_0 = self.game.world.player_deaths 
        # agent_deaths_0 = self.game.world.agent_deaths
        agents_health_0 = self.game.get_agents_health()
        players_health_0 = self.game.get_players_health()

        self.game.world.step()
        
        zombie_deaths_1 = self.game.world.zombie_deaths 
        # player_deaths_1 = self.game.world.player_deaths 
        # agent_deaths_1 = self.game.world.agent_deaths
        agents_health_1 = self.game.get_agents_health()
        players_health_1 = self.game.get_players_health()

        # maintain the flow of zombies if necessary
        self.game.spawn_zombies_to_maintain_minimum()

        observation = self.get_observation()
        if frames_per_second is not None:
            time.sleep(1.0 / frames_per_second)
        reward = (zombie_deaths_1 - zombie_deaths_0) # \
        #          + 1.0*(min(players_health_1 - players_health_0, 0.0))/100.0 \
        #          - (agents_health_1 - agents_health_0)/100.0

        done = False
        if self.game.rules.game_ended():
            won, description = self.game.rules.game_won()
            done = True
        
        info = {}

        # A new output is needed in newer versions of gym
        truncated = False
            
        return observation, reward, done, truncated, info


    def reset(self):
        """Resets the environment to an initial state and returns an initial
        observation.

        Note that this function should not reset the environment's random
        number generator(s); random variables in the environment's state should
        be sampled independently between multiple calls to `reset()`. In other
        words, each call of `reset()` should yield an environment suitable for
        a new episode, independent of previous episodes.

        Returns:
            observation (object): the initial observation.
        """
        self.game.__initialize_world__()
        return self.get_observation()

    def render(self, mode='human'):
        """Renders the environment.

        The set of supported modes varies per environment. (And some
        environments do not support rendering at all.) By convention,
        if mode is:

        - human: render to the current display or terminal and
          return nothing. Usually for human consumption.
        - rgb_array: Return an numpy.ndarray with shape (x, y, 3),
          representing RGB values for an x-by-y pixel image, suitable
          for turning into a video.
        - ansi: Return a string (str) or StringIO.StringIO containing a
          terminal-style text representation. The text can include newlines
          and ANSI escape sequences (e.g. for colors).

        Note:
            Make sure that your class's metadata 'render.modes' key includes
              the list of supported modes. It's recommended to call super()
              in implementations to use the functionality of this method.

        Args:
            mode (str): the mode to render with

        Example:

        class MyEnv(Env):
            metadata = {'render.modes': ['human', 'rgb_array']}

            def render(self, mode='human'):
                if mode == 'rgb_array':
                    return np.array(...) # return RGB frame suitable for video
                elif mode == 'human':
                    ... # pop up a window and render
                else:
                    super(MyEnv, self).render(mode=mode) # just raise an exception
        """
        # if mode == 'ansi':
        #     return self.draw_world()
        if mode == 'human':
            self.game.draw()
            return None
        else:
            raise ValueError("mode={} is not supported".format(mode))

    def close(self):
        """Override close in your subclass to perform any necessary cleanup.

        Environments will automatically close() themselves when
        garbage collected or when the program exits.
        """
        pass

    def seed(self, seed=None):
        """Sets the seed for this env's random number generator(s).

        Note:
            Some environments use multiple pseudorandom number generators.
            We want to capture all such seeds used in order to ensure that
            there aren't accidental correlations between multiple generators.

        Returns:
            list<bigint>: Returns the list of seeds used in this env's random
              number generators. The first value in the list should be the
              "main" seed, or the value which a reproducer should pass to
              'seed'. Often, the main seed equals the provided 'seed', but
              this won't be true if seed=None, for example.
        """
        # NOTE: Not currently capturing the seed information used in zombsole
        return

    @property
    def unwrapped(self):
        """Completely unwrap this env.

        Returns:
            gym.Env: The base non-wrapped gym.Env instance
        """
        return self

    def __str__(self):
        if self.spec is None:
            return '<{} instance>'.format(type(self).__name__)
        else:
            return '<{}<{}>>'.format(type(self).__name__, self.spec.id)

    def __enter__(self):
        """Support with-statement for the environment. """
        return self

    def __exit__(self, *args):
        """Support with-statement for the environment. """
        self.close()
        # propagate exception
        return False

# class Wrapper(Env):
#     """Wraps the environment to allow a modular transformation.

#     This class is the base class for all wrappers. The subclass could override
#     some methods to change the behavior of the original environment without touching the
#     original code.

#     .. note::

#         Don't forget to call ``super().__init__(env)`` if the subclass overrides :meth:`__init__`.

#     """
#     def __init__(self, env):
#         self.env = env
#         self.action_space = self.env.action_space
#         self.observation_space = self.env.observation_space
#         self.reward_range = self.env.reward_range
#         self.metadata = self.env.metadata

#     def __getattr__(self, name):
#         if name.startswith('_'):
#             raise AttributeError("attempted to get missing private attribute '{}'".format(name))
#         return getattr(self.env, name)

#     @property
#     def spec(self):
#         return self.env.spec

#     @classmethod
#     def class_name(cls):
#         return cls.__name__

#     def step(self, action):
#         return self.env.step(action)

#     def reset(self, **kwargs):
#         return self.env.reset(**kwargs)

#     def render(self, mode='human', **kwargs):
#         return self.env.render(mode, **kwargs)

#     def close(self):
#         return self.env.close()

#     def seed(self, seed=None):
#         return self.env.seed(seed)

#     def compute_reward(self, achieved_goal, desired_goal, info):
#         return self.env.compute_reward(achieved_goal, desired_goal, info)

#     def __str__(self):
#         return '<{}{}>'.format(type(self).__name__, self.env)

#     def __repr__(self):
#         return str(self)

#     @property
#     def unwrapped(self):
#         return self.env.unwrapped


# class ObservationWrapper(Wrapper):
#     def reset(self, **kwargs):
#         observation = self.env.reset(**kwargs)
#         return self.observation(observation)

#     def step(self, action):
#         observation, reward, done, info = self.env.step(action)
#         return self.observation(observation), reward, done, info

#     def observation(self, observation):
#         raise NotImplementedError


# class RewardWrapper(Wrapper):
#     def reset(self, **kwargs):
#         return self.env.reset(**kwargs)

#     def step(self, action):
#         observation, reward, done, info = self.env.step(action)
#         return observation, self.reward(reward), done, info

#     def reward(self, reward):
#         raise NotImplementedError


# class ActionWrapper(Wrapper):
#     def reset(self, **kwargs):
#         return self.env.reset(**kwargs)

#     def step(self, action):
#         return self.env.step(self.action(action))

#     def action(self, action):
#         raise NotImplementedError

#     def reverse_action(self, action):
#         raise NotImplementedError
