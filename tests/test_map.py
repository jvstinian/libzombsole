# tests/test_map.py
import pytest
from zombsole.game import Map
from zombsole.things import Wall, ObjectiveLocation

@pytest.mark.parametrize("map_name,exp_map_size,exp_walls_count,exp_objs_count", [
    ("bridge", (111, 12), 182, 28),
    ("boxed", (15, 8), 14, 0),
    ("fort", (73, 21), 210, 0),
])
def test_map_read(map_name, exp_map_size, exp_walls_count, exp_objs_count):
    lmap = Map.from_map_name(map_name)
    assert lmap.size == exp_map_size

    objectives_count = 0
    walls_count = 0
    for thing in lmap.things:
        if isinstance(thing, (Wall,)):
            walls_count += 1
        elif isinstance(thing, (ObjectiveLocation,)):
            objectives_count += 1

    assert walls_count == exp_walls_count
    assert objectives_count == exp_objs_count

