# tests/test_map.py
import pytest
from zombsole.game import Map
from zombsole.things import Wall, ObjectiveLocation

def test_map_read():
    bridge = Map.from_map_name("bridge")
    assert bridge.size == (110, 12)

    objectives_count = 0
    walls_count = 0
    for thing in bridge.things:
        if isinstance(thing, (Wall,)):
            walls_count += 1
        elif isinstance(thing, (ObjectiveLocation,)):
            objectives_count += 1

    assert walls_count == 182
    assert objectives_count == 28

