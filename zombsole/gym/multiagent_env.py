#!/usr/bin/env python
from os import path
from gym.core import Env
from gym.spaces import Text, Box, Dict, Sequence
from gym.spaces.discrete import Discrete
from zombsole.gym.observation import build_surroundings_observation
from zombsole.gym.reward import MultiAgentRewards
from zombsole.game import Game, Map
from zombsole.renderer import build_renderer
import time
import numpy as np


# NOTE: When we update from nixos-23.05, we will need to make sure this properly conforms with PettingZoo's ParallelEnv.
class MultiagentZombsoleEnv(object):
    """The main class for multiagent play.
    """
    # See the supported modes in the render method
    metadata = {
        'render.modes': ['human']
    }
    # reward_range doesn't appear to be mentioned in the ParallelEnv API, but we keep it anyway
    reward_range = (-float('inf'), float('inf'))
    
    def __init__(self, rules_name, player_names, map_name, agent_ids, initial_zombies=0,
                 minimum_zombies=0, render_mode=None,
                 observation_surroundings_width=21,
                 observation_position_encoding_style="channels",
                 agent_weapons="rifle",
                 debug=False):
        self.position_encoding_style = observation_position_encoding_style
        self.surroundings_width = observation_surroundings_width
        self.single_agent_observation = build_surroundings_observation(self.surroundings_width, self.position_encoding_style)

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

        if render_mode is not None and (render_mode not in self.metadata['render.modes']):
            raise ValueError("render_mode={} is not supported".format(render_mode))
        renderer = self.__build_renderer(render_mode, map_.size, len(player_names), len(agent_ids))

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
        )
        
        self.frames_per_second=None

    def __build_renderer(self, render_mode, map_size, num_players, num_agents):
        renderer = None
        if render_mode == "human":
            renderer = build_renderer(
                "opencv", False, map_size, num_players + num_agents
            )
        return renderer

    def get_observation(self):
        ret = {}
        for agent in self.game.agents:
            if agent.agent_id in self.agents: # This indicates the agent was alive before the step
                ret[agent.agent_id] = self.single_agent_observation.get_observation_at_position(
                    self.game, 
                    agent.position
                )
        # return the observation and info
        return ret

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
        """
        Receives a dictionary of actions keyed by the agent name.

        Returns the observation dictionary, reward dictionary, terminated dictionary, truncated dictionary and info dictionary,
        where each dictionary is keyed by the agent.

        Args:
            actions (dict): A dictionary of actions with agent IDs as keys

        Returns:
            observation (dict): observations of the current environment for each agent ID
            reward (dict[AgentID, float]) : amount of reward returned after previous action for each agent ID
            done (dict[AgentID, bool]): whether the episode has ended for each agent ID, in which case subsequent steps() calls might not return info for such an agent
            truncated (dict[AgentID, bool]): whether the episode has expired without a clear outcome for each agent ID, in which case further step() calls will return undefined results for that agent ID
            info (dict[AgentID, dict]): contains auxiliary diagnostic information (helpful for debugging, and sometimes learning) for each agent ID
        """
        agent_actions = self._process_action(action)
        for agent in self.game.agents:
            agent_action = agent_actions.get(agent.agent_id, {"action_type": "heal", "parameter": [0, 0]})
            agent.set_action(agent_action)

        self.game.world.step()
        
        rewardslist = self.reward_tracker.update(self.game.agents, self.game.world)

        # maintain the flow of zombies if necessary
        self.game.spawn_zombies_to_maintain_minimum()

        if self.frames_per_second is not None:
            time.sleep(1.0 / self.frames_per_second)

        doneflag = False
        truncatedflag = False
        end_reward = 0.0
        if self.game.rules.game_ended():
            won, description = self.game.rules.game_won()
            doneflag = True
            end_reward = self.reward_tracker.get_game_end_reward(won)
        elif not self.game.rules.agents_alive():
            # Using truncated to indicate the agents are no longer alive
            truncatedflag = True
            end_reward = self.reward_tracker.get_game_end_reward(False)
        
        # form returns
        rewards = {}
        for agent, reward in zip(self.game.agents, rewardslist):
            if agent.agent_id in self.agents:
                if agent.life > 0:
                    rewards[agent.agent_id] = reward + end_reward
                else:
                    rewards[agent.agent_id] = reward
        observations = self.get_observation()
        info = {}
        done = { agent_id: doneflag for agent_id in self.agents }
        truncated = { agent_id: truncatedflag for agent_id in self.agents }

        # Update the active list of agents
        self.agents = [agent.agent_id for agent in self.game.agents if agent.life > 0]

        return observations, rewards, done, truncated, info

    def reset(self, seed=None, options=None):
        """Resets the environment to an initial state and returns an initial
        observation.

        Returns:
            dictionary of observations (dict[AgentID, ObsType]): the initial observations
            dictionary of info (dict[AgentID, dict]): additional information for each agent
        """
        self.agents = self.possible_agents
        self.game.__initialize_world__()
        self.reward_tracker.reset(self.game.agents, self.game.world)
        return self.get_observation(), {}

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

# Note: At this time, we don't specify a base class
class MultiAgentWrapper(object):
    """Wraps the environment to allow a modular transformation.

    This class is the base class for all wrappers. The subclass could override
    some methods to change the behavior of the original environment without touching the
    original code.

    .. note::

        Don't forget to call ``super().__init__(env)`` if the subclass overrides :meth:`__init__`.

    """
    def __init__(self, env):
        self.env = env
        self.action_spaces = self.env.action_spaces
        self.observation_spaces = self.env.observation_spaces
        self.reward_range = self.env.reward_range
        self.metadata = self.env.metadata

    @classmethod
    def class_name(cls):
        return cls.__name__

    def step(self, action):
        return self.env.step(action)

    def reset(self, seed=None, options=None):
        return self.env.reset(seed=seed, options=options)

    def render(self, mode='human'):
        return self.env.render(mode)

    def close(self):
        self.env.close()

    def __str__(self):
        return '<{}{}>'.format(type(self).__name__, self.env)

class MultiagentZombsoleEnvDiscreteAction(MultiAgentWrapper):
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
        },
        {
            'action_type': 'heal_closest'
        }
    ]

    def __init__(self, rules_name, player_names, map_name, agent_ids, 
                 initial_zombies=0, minimum_zombies=0, 
                 render_mode=None,
                 observation_surroundings_width=21,
                 agent_weapons="rifle",
                 debug=False):
        env = MultiagentZombsoleEnv(
            rules_name, player_names, map_name, agent_ids, 
            initial_zombies=initial_zombies, minimum_zombies=minimum_zombies,
            render_mode=render_mode,
            observation_surroundings_width=observation_surroundings_width,
            agent_weapons=agent_weapons,
            debug=debug
        )
        super().__init__(env)
        # We override the action_space here
        self.action_spaces = {
            agent_id: Discrete(len(MultiagentZombsoleEnvDiscreteAction.game_actions))
            for agent_id in self.env.possible_agents
        }

    def step(self, actions):
        return super().step(self.actions(actions))

    def actions(self, actions):
        return {
            agent_id: self.game_actions[action] for agent_id, action in actions.items()
        }

    def reverse_actions(self, actions):
        return {
            agent_id: self.game_actions.index(action) for agent_id, action in actions.items()
        }

