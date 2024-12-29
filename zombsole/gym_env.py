#!/usr/bin/env python
# coding: utf-8
from os import path, system
from gym.core import Env
from gym.spaces import Text, Box, Dict
from gym.spaces.discrete import Discrete
from gym.envs.registration import register
from zombsole.gym.observation import build_observation
from zombsole.gym.reward import AgentRewards
from zombsole.game import Game, Map
from zombsole.renderer import NoRender
import time
import numpy as np


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
    # Set these in ALL subclasses
    reward_range = (-float('inf'), float('inf'))
    action_space = Dict({
        "action_type": Text(15), 
        "parameter": Box(low=-10, high=10, shape=(2,), dtype=np.int32)
    })
    # setting observation_space in the constructor

    def __init__(self, rules_name, player_names, map_name, agent_id, initial_zombies=0,
                 minimum_zombies=0, renderer=NoRender(), 
                 observation_scope="world", observation_position_encoding="simple", 
                 agent_weapon="rifle",
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
            agent_weapons=[agent_weapon],
            debug=debug,
        )

        self.observation_handler = build_observation(
                observation_scope, observation_position_encoding, map_.size
        )
        self.observation_space = self.observation_handler.get_observation_space()

        self.reward_tracker = AgentRewards(
            self.game.agents,
            self.game.world,
            10.0,
            include_life_in_reward=True
        )

    def get_observation(self):
        return self.observation_handler.get_observation(self.game)
    
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
        self.game.agents[0].set_action(action)

        frames_per_second=None

        self.game.world.step()
        
        reward = self.reward_tracker.update(self.game.agents, self.game.world)

        # maintain the flow of zombies if necessary
        self.game.spawn_zombies_to_maintain_minimum()

        observation = self.get_observation()
        if frames_per_second is not None:
            time.sleep(1.0 / frames_per_second)

        done = False
        truncated = False
        if self.game.rules.game_ended():
            won, description = self.game.rules.game_won()
            done = True
            end_reward = self.reward_tracker.get_game_end_reward(won)
            reward += end_reward
        elif not self.game.rules.agents_alive():
            # Using truncated to indicate the agents are no longer alive
            truncated = True
            end_reward = self.reward_tracker.get_game_end_reward(False)
            reward += end_reward
        
        info = {}

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
        self.reward_tracker.reset(self.game.agents, self.game.world)
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


class Wrapper(Env):
    """Wraps the environment to allow a modular transformation.

    This class is the base class for all wrappers. The subclass could override
    some methods to change the behavior of the original environment without touching the
    original code.

    .. note::

        Don't forget to call ``super().__init__(env)`` if the subclass overrides :meth:`__init__`.

    """
    def __init__(self, env):
        self.env = env
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space
        self.reward_range = self.env.reward_range
        self.metadata = self.env.metadata

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError("attempted to get missing private attribute '{}'".format(name))
        return getattr(self.env, name)

    @property
    def spec(self):
        return self.env.spec

    @classmethod
    def class_name(cls):
        return cls.__name__

    def step(self, action):
        return self.env.step(action)

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)

    def render(self, mode='human', **kwargs):
        return self.env.render(mode, **kwargs)

    def close(self):
        return self.env.close()

    def seed(self, seed=None):
        return self.env.seed(seed)

    # def compute_reward(self, achieved_goal, desired_goal, info):
    #     return self.env.compute_reward(achieved_goal, desired_goal, info)

    def __str__(self):
        return '<{}{}>'.format(type(self).__name__, self.env)

    def __repr__(self):
        return str(self)

    @property
    def unwrapped(self):
        return self.env.unwrapped


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


class ZombsoleGymEnvDiscreteAction(Wrapper):
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
    
    def __init__(self, rules_name, player_names, map_name, agent_id, 
                 initial_zombies=0, minimum_zombies=0, 
                 renderer=NoRender(), 
                 observation_scope="world", observation_position_encoding="simple", 
                 debug=False):
        env = ZombsoleGymEnv(
            rules_name, player_names, map_name, agent_id, 
            initial_zombies=initial_zombies, minimum_zombies=minimum_zombies,
            renderer=renderer,
            observation_scope=observation_scope, observation_position_encoding=observation_position_encoding,
            debug=debug
        )
        super().__init__(env)
        # We override the action_space here
        self.action_space = Discrete(len(ZombsoleGymEnvDiscreteAction.game_actions))

    def reset(self, **kwargs):
        return super().reset(**kwargs)

    def step(self, action):
        return super().step(self.action(action))

    def action(self, action):
        return self.game_actions[action]

    def reverse_action(self, action):
        return self.game_actions.index(action)


register(
    id='jvstinian/Zombsole-v0', 
    entry_point='zombsole.gym_env:ZombsoleGymEnvDiscreteAction', 
    max_episode_steps=1000,
    kwargs={
        'rules_name': 'extermination',
        'player_names': [],
        'map_name': 'bridge',
        'agent_id': 0,
        'initial_zombies': 10,
        'minimum_zombies': 0,
        'debug': False
    }
)

register(
    id='jvstinian/Zombsole-SurroundingsView-v0', 
    entry_point='zombsole.gym_env:ZombsoleGymEnvDiscreteAction', 
    max_episode_steps=1000,
    kwargs={
        'rules_name': 'extermination',
        'player_names': [],
        'map_name': 'bridge',
        'agent_id': 0,
        'initial_zombies': 10,
        'minimum_zombies': 0,
        'observation_scope': 'surroundings:21',
        'observation_position_encoding': 'simple',
        'debug': False
    }
)

