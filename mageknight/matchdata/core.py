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

__all__ = ['InvalidAction', 'State', 'RoundType', 'Round', 'Mana']


class InvalidAction(Exception):
    """Use this exception, when the user tries to perform an action that is not allowed by the rules."""
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return "Invalid action: "+self.message
    
    
class State(enum.Enum):
    # TODO: more states are necessary for e.g. pillaging, resting, level-up...
    init = 1
    movement = 2
    action = 3
    
    
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
    def basic(self):
        return self not in (Mana.gold, Mana.black)
    
    @staticmethod
    def basicColors():
        return (Mana.red, Mana.blue, Mana.green, Mana.white)
