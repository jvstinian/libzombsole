#!/usr/bin/env python
# coding: utf-8
from os import path
from gym.core import Env
from gym.spaces import Text, Box, Dict, Sequence
from gym.spaces.discrete import Discrete
from zombsole.gym.observation import SurroundingsChannelsObservation
from zombsole.gym.reward import AgentRewards # MultiAgentRewards
from zombsole.game import Game, Map
from zombsole.renderer import NoRender
import time
import numpy as np


class MultiagentZombsoleEnv(object):
    """The main Gym class for multiagent play.
    """
    # See the supported modes in the render method
    metadata = {
        'render.modes': ['human']
    }
    reward_range = (-float('inf'), float('inf'))
    
    action_space = Sequence( # alternate approach; this might be the way to go
        Dict({
            "agent_id": Discrete(64),
            "action_type": Text(15), 
            "parameter": Box(low=-10, high=10, shape=(2,), dtype=np.int32)
        })
    )

    # setting observation_space in the constructor with the help of the following
    # TODO: Why is half_width used in the following?
    def _get_observation_space(self, half_width):
        return Sequence(
            Dict({
                "agent_id": Discrete(64),
                "observation": Box(low=0, high=128, shape=(3, half_width, half_width), dtype=np.int32)
            })
        )


    def __init__(self, rules_name, player_names, map_name, agent_ids, initial_zombies=0,
                 minimum_zombies=0, renderer=NoRender(), 
                 observation_surroundings_width=21, 
                 debug=False):
        fdir = path.dirname(path.abspath(__file__))
        map_file = path.join(fdir, '..', 'maps', map_name)
        map_ = Map.from_file(map_file)

        self.game = Game(
            rules_name, player_names, map_,
            initial_zombies=initial_zombies, minimum_zombies=minimum_zombies,
            use_basic_icons=True,
            agent_ids=agent_ids,
            renderer=renderer,
            debug=debug,
        )

        self.surroundings_width = observation_surroundings_width
        self.surroundings_half_width = observation_surroundings_width // 2
        self.single_agent_observation = SurroundingsChannelsObservation(self.surroundings_width)
        self.observation_space = self._get_observation_space(self.surroundings_half_width)

        self.reward_tracker = AgentRewards(
            self.game.agents,
            self.game.world,
            10.0,
            include_life_in_reward=True
        )

    def get_observation(self):
        return [
            {
                "agent_id": agent.agent_id,
                "observation": self.single_agent_observation.get_observation_at_position(self.game, agent.position)
            } for agent in self.game.agents
        ]

    def _process_single_agent_action(self, sp_action):
        coords = sp_action.get("parameter", [0, 0])
        return { 
            "action_type": sp_action["action_type"], 
            "parameter": coords
        }

    def _process_action(self, action):
        return {
            v["agent_id"]: self._process_single_agent_action(v) for v in action
        }

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
        agent_actions = self._process_action(action)
        for agent in self.game.agents:
            agent_action = agent_actions.get(agent.agent_id, {"action_type": "heal", "parameter": [0, 0]})
            agent.set_action(agent_action)

        frames_per_second=None

        # zombie_deaths_0 = self.game.world.zombie_deaths 
        # # player_deaths_0 = self.game.world.player_deaths 
        # # agent_deaths_0 = self.game.world.agent_deaths
        # agents_health_0 = self.game.get_agents_health()
        # players_health_0 = self.game.get_players_health()

        self.game.world.step()
        
        # zombie_deaths_1 = self.game.world.zombie_deaths 
        # # player_deaths_1 = self.game.world.player_deaths 
        # # agent_deaths_1 = self.game.world.agent_deaths
        # agents_health_1 = self.game.get_agents_health()
        # players_health_1 = self.game.get_players_health()

        reward = self.reward_tracker.update(self.game.agents, self.game.world)

        # maintain the flow of zombies if necessary
        self.game.spawn_zombies_to_maintain_minimum()

        observation = self.get_observation()
        if frames_per_second is not None:
            time.sleep(1.0 / frames_per_second)
        # reward = (zombie_deaths_1 - zombie_deaths_0) # \
        # #          + 1.0*(min(players_health_1 - players_health_0, 0.0))/100.0 \
        # #          - (agents_health_1 - agents_health_0)/100.0

        done = False
        truncated = False
        if self.game.rules.game_ended():
            won, description = self.game.rules.game_won()
            done = True
            end_reward = self.reward_tracker.get_game_end_reward(won)
            # reward = list(map(lambda rs: rs[0] + rs[1], zip(reward, end_reward)))
            reward += end_reward
        elif not self.game.rules.agents_alive():
            # Using truncated to indicate the agents are no longer alive
            truncated = True
            end_reward = self.reward_tracker.get_game_end_reward(False)
            # reward = list(map(lambda rs: rs[0] + rs[1], zip(reward, end_reward)))
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
        """Renders the environment.  Only 'human' is supported in this implementation.
        Args:
            mode (str): the mode to render with
        """
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

