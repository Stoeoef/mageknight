# -*- coding: utf-8 -*-
#
# This file is part of the Mage Knight implementation at
# https://github.com/MartinAltmayer/mageknight.
#
# Copyright 2015 Martin Altmayer, Stefan Altmayer
# The Mage Knight board game was created by Vlaada Chvátil.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import enum, random

__all__ = ['InvalidAction', 'CancelAction', 'State', 'RoundType', 'Round', 'Mana',
           'AttackRange', 'Element', 'EffectType', 'CombatReward', 'CombatRewardType']


class InvalidAction(Exception):
    """Use this exception, when the user tries to perform an action that is not allowed by the rules."""
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return "Invalid action: "+self.message


class CancelAction(Exception):
    pass


class State(enum.Enum):
    # TODO: more states are necessary for e.g. pillaging, resting, level-up...
    movement = 1     # movement phase
    interaction = 2  # 
    combatEnd = 3    # after a combat, before end of turn. User may play special effects and healing.
    explore = 4      # while choosing a new tile location
    
    # Combat states
    initCombat = 10 # technical state during which (marauding) enemies might be added
    provokeMarauders = 11 # if provokable enemies were added, let the user choose which enemies to fight
    rangeAttack = 12
    block = 13
    assignDamage = 14
    attack = 15
    combatRewards = 16
    
    endOfTurn = 20
    
    @staticmethod
    def combatStates():
        return (State.initCombat, State.provokeMarauders, State.rangeAttack, State.block,
                State.assignDamage, State.attack, State.combatRewards)
    
    @property
    def inCombat(self):
        return self in State.combatStates()
    
    
class RoundType(enum.Enum):
    """Each round is either day or night."""
    day = 1
    night = 2
    
    
class Round:
    """A match of Mage Knight consists of a fixed number of rounds, each being either one day or night."""
    def __init__(self, number, type):
        self.number = number
        self.type = type
    
        
class Mana(enum.Enum):
    """This class represents mana of a certain color. Depending on the context it might be a token, crystal,
    die, or something else."""
    red = 1
    blue = 2
    green = 3
    white = 4
    gold = 5
    black = 6
    
    @staticmethod
    def random():
        return Mana(random.randint(1, 6))
    
    @property
    def isBasic(self):
        return self not in (Mana.gold, Mana.black)
    
    @staticmethod
    def basicColors():
        return (Mana.red, Mana.blue, Mana.green, Mana.white)
 

class AttackRange(enum.Enum):
    """Range of a player attack."""
    normal = 1
    range = 2
    siege = 3
    
    @property
    def title(self):
        if self is AttackRange.normal:
            return 'Normal'
        elif self is AttackRange.range:
            return 'Ranged'
        else: return 'Siege'


class Element(enum.Enum):
    """The type of a block."""
    physical = 1
    fire = 2
    ice = 3
    coldFire = 4
    summoner = 5
    
    @property
    def title(self):
        if self is Element.physical:
            return 'Physical'
        elif self is Element.fire:
            return 'Fire'
        elif self is Element.ice:
            return 'Ice'
        elif self is Element.coldFire:
            return 'Cold Fire'
        else: return 'Summoner'
        
        
class EffectType(enum.Enum):
    """Each card,unit action, skill etc. has a type which determines when it can be played."""
    unknown = 0
    movement = 1
    influence = 2
    combat = 3
    healing = 4
    special = 5
    
    
class CombatRewardType(enum.Enum):
    """Type of reward after combat. Fame/reputation gains are not considered as combat rewards."""
    crystal = 1
    artifact = 2
    spell = 3
    advancedAction = 4
    unit = 5
    
    @property
    def title(self):
        if self is CombatRewardType.crystal:
            return "Crystal" # TODO: translate
        elif self is CombatRewardType.artifact:
            return "Artifact"
        elif self is CombatRewardType.spell:
            return "Spell"
        elif self is CombatRewardType.advancedAction:
            return "Advanced Action"
        elif self is CombatRewardType.unit:
            return "Unit"
                
class CombatReward:
    def __init__(self, type, count=1):
        self.type = type
        self.count = count
        self.items = tuple()
        
    