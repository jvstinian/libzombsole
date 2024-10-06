# tests/players/agent.py
import pytest
from zombsole.players.agent import create
from zombsole.weapons import Rifle

def test_agent_icon_basic():
    agent = create("0", Rifle, None, objectives=None)
    assert agent.agent_id == "0"
    assert agent.icon_basic == "A"

