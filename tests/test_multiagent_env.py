# tests/test_multiagent_env.py
import pytest
from zombsole.gym.multiagent_env import MultiagentZombsoleEnv
from zombsole.renderer import NoRender


@pytest.fixture(scope="function", name="env1p")
def env1p_fixture():
    env = MultiagentZombsoleEnv(
        "extermination",
        [],
        "boxed",
        [0], # agent_ids
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
         observation_surroundings_width=21, 
        debug=True
    )
    return env


@pytest.fixture(scope="function", name="env2p")
def env2p_fixture():
    env = MultiagentZombsoleEnv(
        "extermination",
        [],
        "boxed",
        [0, 1], # agent_ids
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
         observation_surroundings_width=21, 
        debug=True
    )
    return env


@pytest.fixture(scope="function", name="env32p")
def env32p_fixture():
    env = MultiagentZombsoleEnv(
        "extermination",
        [],
        "fort",
        list(range(0, 32)), # agent_ids
        initial_zombies=100,
        minimum_zombies=0, 
        renderer=NoRender(), 
         observation_surroundings_width=21, 
        debug=True
    )
    return env


def test_multiagent_env_shape():
    env = MultiagentZombsoleEnv(
        "extermination",
        ["terminator"],
        "boxed",
        [0], # agent_ids
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
         observation_surroundings_width=21, 
        debug=True
    )
    observation = env.get_observation()
    map_size = env.game.world.size
    channels = 3
    expected_observation_shape = (channels, max(map_size[1], 21), max(map_size[0], 21))
    for spobs in observation:
        assert spobs.get("observation").shape == expected_observation_shape


def test_multiagent_1pgame(env1p):
    stepcount = 0
    while True:
        observation, reward, done, truncated, _ = env1p.step([
            {
                "agent_id": 0,
                "action_type": "attack_closest",
                "parameter": [0, 0]
            }
        ])

        if done or truncated or (stepcount >=10):
            break

        stepcount += 1

    assert stepcount < 10

def test_multiagent_targeted_heal(env2p):
    env2p.game.agents[1].life = 25
    agent1pos = env2p.game.agents[1].position
    agent0pos = env2p.game.agents[0].position
    relativepos = (agent1pos[0] - agent0pos[0], agent1pos[1] - agent0pos[1])

    _ = env2p.step([
        {
            "agent_id": 0,
            "action_type": "heal",
            "parameter": relativepos
        }
    ])

    assert env2p.game.agents[1].agent_id == 1
    assert env2p.game.agents[1].life > 25

def test_multiagent_large_game(env32p):
    stepcount = 0
    while True:
        _, _, done, truncated, _ = env32p.step([
            {
                "agent_id": idx,
                "action_type": "attack_closest",
                "parameter": [0, 0]
            } for idx in range(0, 32)
        ])

        if done or truncated or (stepcount >=200):
            break

        stepcount += 1

    assert True

