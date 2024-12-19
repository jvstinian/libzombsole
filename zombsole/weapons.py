# coding: utf-8
import random
from zombsole.core import Weapon


def _new_weapon_class(name, max_range, damage_range):
    """Create new weapon class."""
    class NewWeapon(Weapon):
        def __init__(self):
            super(NewWeapon, self).__init__(name,
                                            max_range,
                                            damage_range)

    NewWeapon.__name__ = name
    return NewWeapon


ZombieClaws = _new_weapon_class('ZombieClaws', 1.5, (5, 10))

Knife = _new_weapon_class('Knife', 1.5, (5, 10))
Axe = _new_weapon_class('Axe', 1.5, (75, 100))

Gun = _new_weapon_class('Gun', 6, (10, 50))
Rifle = _new_weapon_class('Rifle', 10, (25, 75))
Shotgun = _new_weapon_class('Shotgun', 3, (75, 100))


class WeaponFactory(object):
    @staticmethod
    def create_player_weapon(weapon_name):
        lc_weapon_name = weapon_name.lower()
        if lc_weapon_name == "knife":
            return Knife()
        elif lc_weapon_name == "axe":
            return Axe()
        elif lc_weapon_name == "gun":
            return Gun()
        elif lc_weapon_name == "rifle":
            return Rifle()
        elif lc_weapon_name == "shotgun":
            return Shotgun()
        elif lc_weapon_name == "random":
            return random.choice([Knife(), Axe(), Gun(), Rifle(), Shotgun()])
        else:
            raise ValueError(f"{weapon_name} is not a valid player weapon name.  Valid options are knife, axe, gun, rifle, shotgun, and random.")

