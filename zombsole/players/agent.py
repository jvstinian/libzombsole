# coding: utf-8
from __future__ import print_function
import sys

from zombsole.things import Player, Zombie, Wall, Box
from zombsole.utils import closest


class Agent(Player):
    ICON = u'\u2A51'
    ICON_BASIC = u'A'

    def __init__(self, agent_id, color, position=None, 
                 weapon=None, rules=None, objectives=None
    ):
        # We override the players icon and icon_basic fields
        super(Agent, self).__init__('agent', color, position=position, weapon=weapon, rules=rules,
                                    objectives=objectives, icon=Agent.ICON, icon_basic=Agent.ICON_BASIC)
        self.thing_type = 'agent'
        self.agent_id = agent_id

    def set_action(self, action): 
        self.action = action
        self.action_type = action.get('action_type', None)
        self.action_parameter = action.get('parameter', None)

    """An interactive agent, with the next action determined by a separate process."""
    def next_step(self, things, t):
        target = None
        if not self.action_type:
            self.status = 'sitting idle'
            self.action_type = None
        elif self.action_type == 'move':
            # Throw if self.action_parameter not of length 2
            self.status = u'walking'
            target = (self.position[0] + self.action_parameter[0],
                      self.position[1] + self.action_parameter[1])
        elif self.action_type == 'attack_closest':
            zombies = [thing for thing in things.values()
                       if isinstance(thing, Zombie)]

            if zombies:
                self.status = u'shooting closest zombie'
                self.action_type = 'attack'
                target = closest(self, zombies)
            else:
                self.status = u'killing flies, because no zombies left'
                self.action_type = None
        elif self.action_type == 'attack':
            self.status = u'shooting at {}'.format(self.action_parameter)
            targetpos = (self.position[0] + self.action_parameter[0],
                         self.position[1] + self.action_parameter[1])
            target = things.get(targetpos, None)
            if target is None:
                # Reset the action type and target
                self.action_type = None
                target = None
                self.status = u'No target at position {} to attack'.format(self.action_parameter)
        elif self.action_type == 'heal':
            # Heal a target specified by the relative coordinates in self.action_parameter
            if (not self.action_parameter) or (tuple(self.action_parameter) == (0, 0)):
                self.status = u'healing self'
                target=self 
            else:
                self.status = u'healing thing at {}'.format(self.action_parameter)
                targetpos = (self.position[0] + self.action_parameter[0],
                             self.position[1] + self.action_parameter[1])
                target = things.get(targetpos, None)
                # For amusement, we allow boxes and walls to be healed in addition 
                # to players if it is explicitly specified as the target
                if not isinstance(target, (Player, Box, Wall)):
                    # Reset the action type and target
                    self.action_type = None
                    target = None
                    self.status = u'unable to heal thing at {}'.format(self.action_parameter)
        elif self.action_type == 'heal_closest':
            # Heal the closest player, or self if no other players 
            players = [thing for thing in things.values()
                       if isinstance(thing, Player) and thing is not self]

            if players:
                self.status = u'healing closest friend'
                self.action_type = 'heal'
                target = closest(self, players)
            else:
                self.status = u'healing self, because no other players are left'
                self.action_type = 'heal'
                target = self
        else:
            self.action_type = None
            self.status = u'confused'

        if self.action_type:
            return self.action_type, target
        else:
            return None

def create(agent_id, weapon, rules, objectives=None):
    return Agent(agent_id, "blue", weapon=weapon, rules=rules, objectives=objectives)
