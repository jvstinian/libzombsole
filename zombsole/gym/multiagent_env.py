#!/usr/bin/env python
# coding: utf-8
from os import path
from gym.core import Env
from gym.spaces import Text, Box, Dict, Sequence
from gym.spaces.discrete import Discrete
from zombsole.gym.observation import SurroundingsChannelsObservation
from zombsole.gym.reward import MultiAgentRewards # , AgentRewards
from zombsole.game import Game, Map
from zombsole.renderer import NoRender
import time
import numpy as np


class MultiagentZombsoleEnv(object):
    """The main class for multiagent play.
    """
    # See the supported modes in the render method
    metadata = {
        'render.modes': ['human']
    }
    reward_range = (-float('inf'), float('inf'))
    
    # action_space = Sequence( # alternate approach; this might be the way to go
    #     Dict({
    #         "agent_id": Discrete(64), # TODO
    #         "action_type": Text(15), 
    #         "parameter": Box(low=-10, high=10, shape=(2,), dtype=np.int32)
    #     })
    # )

    # # setting observation_space in the constructor with the help of the following
    # def _get_observation_space(self, width):
    #     return Sequence(
    #         Dict({
    #             "agent_id": Discrete(64), # TODO
    #             "observation": Box(low=0, high=128, shape=(3, width, width), dtype=np.int32)
    #         })
    #     )


    def __init__(self, rules_name, player_names, map_name, agent_ids, initial_zombies=0,
                 minimum_zombies=0, renderer=NoRender(), 
                 observation_surroundings_width=21,
                 agent_weapons="rifle",
                 debug=False):
        self.surroundings_width = observation_surroundings_width
        self.single_agent_observation = SurroundingsChannelsObservation(self.surroundings_width)

        self.agents = agent_ids
        self.possible_agents = agent_ids
        # self.num_agents = len(self.agents) # Is this needed by PettingZoo?
        # self.max_num_agents = len(self.possible_agents) # Is this needed by PettingZoo?
        self.action_spaces = { 
            agent_id: Dict({
                "action_type": Text(15), 
                "parameter": Box(low=-10, high=10, shape=(2,), dtype=np.int32)
            })
            for agent_id in self.possible_agents 
        }
        self.observation_spaces = {
            agent_id: self.single_agent_observation.get_observation_space()
            for agent_id in self.possible_agents 
        }

        # map
        fdir = path.dirname(path.abspath(__file__))
        map_file = path.join(fdir, '..', 'maps', map_name)
        map_ = Map.from_file(map_file)

        # game
        self.game = Game(
            rules_name, player_names, map_,
            initial_zombies=initial_zombies, minimum_zombies=minimum_zombies,
            use_basic_icons=True,
            agent_ids=agent_ids,
            renderer=renderer,
            agent_weapons=agent_weapons,
            debug=debug,
        )

        self.reward_tracker = MultiAgentRewards(
            self.game.agents,
            self.game.world,
            10.0,
            # include_life_in_reward=True
        )

    def get_observation(self):
        ret = {}
        for agent in self.game.agents:
            if agent.agent_id in self.agents: # This indicates the agent was alive before the step
                ret[agent.agent_id] = self.single_agent_observation.get_observation_at_position(
                    self.game, 
                    agent.position
                )
        # return the observation and info
        return ret, {}

    def _process_single_agent_action(self, sp_action):
        coords = sp_action.get("parameter", [0, 0])
        return { 
            "action_type": sp_action["action_type"], 
            "parameter": coords
        }

    def _process_action(self, actions):
        return {
            agent_id: self._process_single_agent_action(v) for agent_id, v in actions.items()
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

        frames_per_second=None # TODO: Move to constructor

        self.game.world.step()
        
        # TODO: What should be done with the following?
        rewardslist = self.reward_tracker.update(self.game.agents, self.game.world)

        # maintain the flow of zombies if necessary
        self.game.spawn_zombies_to_maintain_minimum()

        if frames_per_second is not None:
            time.sleep(1.0 / frames_per_second)

        doneflag = False
        truncatedflag = False
        end_reward = 0.0
        if self.game.rules.game_ended():
            won, description = self.game.rules.game_won()
            doneflag = True
            end_reward = self.reward_tracker.get_game_end_reward(won)
            # reward += end_reward
        elif not self.game.rules.agents_alive():
            # Using truncated to indicate the agents are no longer alive
            truncatedflag = True
            end_reward = self.reward_tracker.get_game_end_reward(False)
            # reward += end_reward
        
        # form returns
        rewards = {}
        for agent, reward in zip(self.game.agents, rewardslist):
            if agent.agent_id in self.agents:
                if agent.life > 0:
                    rewards[agent.agent_id] = reward + end_reward
                else:
                    rewards[agent.agent_id] = reward
        observations, info = self.get_observation()
        done = { agent_id: doneflag for agent_id in self.agents }
        truncated = { agent_id: truncatedflag for agent_id in self.agents }

        # Update the active list of agents
        self.agents = [agent.agent_id for agent in self.game.agents if agent.life > 0]

        return observations, rewards, done, truncated, info


    def reset(self, seed=None, options=None):
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
        self.agents = self.possible_agents
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

    # def seed(self, seed=None):
    #     """Sets the seed for this env's random number generator(s).

    #     Note:
    #         Some environments use multiple pseudorandom number generators.
    #         We want to capture all such seeds used in order to ensure that
    #         there aren't accidental correlations between multiple generators.

    #     Returns:
    #         list<bigint>: Returns the list of seeds used in this env's random
    #           number generators. The first value in the list should be the
    #           "main" seed, or the value which a reproducer should pass to
    #           'seed'. Often, the main seed equals the provided 'seed', but
    #           this won't be true if seed=None, for example.
    #     """
    #     # NOTE: Not currently capturing the seed information used in zombsole
    #     return

    @property
    def unwrapped(self):
        """Completely unwrap this env.

        Returns:
            gym.Env: The base non-wrapped gym.Env instance
        """
        return self

    def __str__(self):
        return '<{} instance>'.format(type(self).__name__)

    def __enter__(self):
        """Support with-statement for the environment. """
        return self

    def __exit__(self, *args):
        """Support with-statement for the environment. """
        self.close()
        # propagate exception
        return False

