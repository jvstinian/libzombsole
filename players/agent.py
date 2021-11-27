# coding: utf-8
from __future__ import print_function
import sys

from things import Player, Zombie
from utils import closest


class Agent(Player):
    def __init__(self, agent_id, color, position=None, weapon=None, rules=None,
                 objectives=None, icon=None):
        super(Agent, self).__init__('agent', color, position=position, weapon=weapon, rules=rules,
                                    objectives=objectives, icon=icon)
        self.thing_type = 'agent'
        self.agent_id = agent_id
        self.ICON = u'\u2A51'
        self.ICON_BASIC = u'A'

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
        elif self.action_type == 'heal':
            if not self.action_parameter:
                self.status = u'healing self'
                target=self # TODO: This will likely be needed, DONE
            else:
                players = [thing for thing in things.values()
                           if isinstance(thing, Player) and thing is not self]

                if players:
                    self.status = u'healing closest friend'
                    target = closest(self, players)
                else:
                    self.status = u'healing flies, because no players left'
                    self.action_type = None
        else:
            self.action_type = None
            self.status = u'confused'

        if self.action_type:
            return self.action_type, target

def create(agent_id, weapon, rules, objectives=None):
    return Agent(agent_id, 'red', weapon=weapon, rules=rules, objectives=objectives)
