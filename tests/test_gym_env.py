# tests/test_gym_env.py
import pytest
import gymnasium
from zombsole.gym_env import ZombsoleGymEnv


def test_gym_env_registry():
    assert "jvstinian/Zombsole-v0" in gymnasium.envs.registry.keys()
    assert "jvstinian/Zombsole-SurroundingsView-v0" in gymnasium.envs.registry.keys()

@pytest.mark.parametrize("scope,position_encoding", [("world", "simple"), ("world", "channels")])
def test_observations_world(scope, position_encoding):
    gym_env = ZombsoleGymEnv(
        "extermination",
        ["terminator"],
        "bridge",
        "0", # agent_id
        initial_zombies=1,
        minimum_zombies=0, 
        render_mode=None,
        observation_scope=scope,
        observation_position_encoding=position_encoding,
        debug=False
    )
    observation = gym_env.get_observation()
    map_size = gym_env.game.world.size
    channels = 3 if position_encoding == "channels" else 1
    assert observation.shape == (channels,map_size[1], map_size[0])

@pytest.mark.parametrize("scope,position_encoding", [("surroundings:11", "simple"), ("surroundings:11", "channels")])
def test_observations_surroundings(scope, position_encoding):
    gym_env = ZombsoleGymEnv(
        "extermination",
        ["terminator"],
        "bridge",
        "0", # agent_id
        initial_zombies=1,
        minimum_zombies=0, 
        render_mode=None,
        observation_scope=scope,
        observation_position_encoding=position_encoding,
        debug=False
    )
    surroundings_width = int(scope[len("surroundings:"):])
    observation = gym_env.get_observation()
    channels = 3 if position_encoding == "channels" else 1
    assert observation.shape == (channels, surroundings_width, surroundings_width)

