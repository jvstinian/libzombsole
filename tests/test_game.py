# tests/test_game.py
import pytest
from zombsole.gym_env import ZombsoleGymEnv, ZombsoleGymEnvDiscreteAction
from zombsole.renderer import NoRender
from zombsole.things import Zombie


# We use the Gymnasium environment here so we can control an agents actions.
def test_game_targeted_attack():
    gym_env = ZombsoleGymEnv(
        "extermination",
        [], # no players
        "boxed",
        0, # agent_id
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
        observation_scope="world",
        observation_position_encoding="simple",
        debug=True
    )

    zombies = [thing for thing in gym_env.game.world.things.values() if isinstance(thing, Zombie)]
    assert len(zombies) > 0
   
    zombie = zombies[0]
    initial_zombie_life = zombie.life
    zombiepos = zombie.position
    agentpos = gym_env.game.agents[0].position
    relativepos = (zombiepos[0] - agentpos[0], zombiepos[1] - agentpos[1])
    
    # Step and inspect the life remaining of the zombie
    gym_env.step({
        "action_type": "attack",
        "parameter": relativepos
    })
    new_zombie_life = zombie.life
    assert new_zombie_life < initial_zombie_life


def test_game_targeted_heal():
    gym_env = ZombsoleGymEnv(
        "extermination",
        ["terminator"], # no players
        "boxed",
        0, # agent_id
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
        observation_scope="world",
        observation_position_encoding="simple",
        debug=True
    )

    gym_env.game.players[0].life = 25
   
    playerpos = gym_env.game.players[0].position
    agentpos = gym_env.game.agents[0].position
    relativepos = (playerpos[0] - agentpos[0], playerpos[1] - agentpos[1])

    # Step and check the remaining life of the player has increased
    gym_env.step({
        "action_type": "heal",
        "parameter": relativepos
    })
    assert gym_env.game.players[0].life > 25

def test_game_heal_closest():
    gym_env = ZombsoleGymEnv(
        "extermination",
        ["terminator"], # no players
        "boxed",
        0, # agent_id
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
        observation_scope="world",
        observation_position_encoding="simple",
        debug=True
    )

    gym_env.game.players[0].life = 25
   
    # Step and check the remaining life of the player has increased
    gym_env.step({
        "action_type": "heal_closest",
        "parameter": [0, 0]
    })
    assert gym_env.game.players[0].life > 25

def test_game_heal_self():
    gym_env = ZombsoleGymEnv(
        "extermination",
        [], # no players
        "boxed",
        0, # agent_id
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
        observation_scope="world",
        observation_position_encoding="simple",
        debug=True
    )

    gym_env.game.agents[0].life = 25

    # Step and check the agent has healed itself
    gym_env.step({
        "action_type": "heal",
        "parameter": [0, 0]
    })
    assert gym_env.game.agents[0].life > 25

def test_discrete_game_closest_attack():
    gym_env = ZombsoleGymEnvDiscreteAction(
        "extermination",
        [], # no players
        "boxed",
        0, # agent_id
        initial_zombies=1,
        minimum_zombies=0, 
        renderer=NoRender(), 
        observation_scope="world",
        observation_position_encoding="simple",
        debug=True
    )

    zombies = [thing for thing in gym_env.game.world.things.values() if isinstance(thing, Zombie)]
    assert len(zombies) > 0
   
    zombie = zombies[0]
    initial_zombie_life = zombie.life

    action_id = gym_env.reverse_action({
        "action_type": "attack_closest"
    })
    assert action_id == 4

    gym_env.step(action_id)
    new_zombie_life = zombie.life
    assert new_zombie_life < initial_zombie_life

    # Check that we can reset
    gym_env.reset()
    assert True

