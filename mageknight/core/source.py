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

from PyQt5 import QtCore

from mageknight.attributes import * # @UnusedWildImport
from mageknight.data import Mana, InvalidAction


class ManaSource(AttributeObject):
    """The mana source contains the mana dice available to all players. It behaves like a read-only list, so 
    e.g. 'len(source)' and 'source[2]' work as expected. The additional attribute 'count' stores the initial
    number of dice in the source (typically number of players + 2).
    """ 
    changed = QtCore.pyqtSignal()
    _dice = ListAttribute(Mana, signal='changed')
    limit = IntAttribute(default=1)
        
    def __init__(self, match, count):
        super().__init__(match.stack)
        self.match = match
        self.count = count
        
    def shuffle(self):
        """Shuffle all dice in the source."""
        self._dice = [Mana.random() for _ in range(self.count)]
        self.match.newInformationRevealed()
    
    def reset(self):
        """Reset the source at the beginning of a new round."""
        self.shuffle()
        # Rules: Source must be reshuffled if less than half of the dice show a basic color
        while sum(1 if die.isBasic else 0 for die in self._dice) < self.count / 2:
            self.shuffle()
        self.limit = 1        

    def remove(self, color):
        """Remove a die from the source."""
        self._dice.remove(color)
        
    def take(self, color):
        """Take a die from the source to pay a mana for the current player. Contrary to 'remove' this
        includes some checks and decreases source.limit.
        """ 
        if self.limit == 0:
            raise InvalidAction("You cannot take another die in this turn")
        if color == Mana.black and not self.match.nightRulesApply():
            raise InvalidAction("You must not use black mana during day.")
        if color == Mana.gold and self.match.nightRulesApply():
            raise InvalidAction("You must not use gold mana during night.")
        self.limit -= 1
        self._dice.remove(color)
        
    # Methods required for a read-only list
    def __len__(self):
        return len(self._dice)
    
    def __getitem__(self, index):
        return self._dice[index]
    
    def __contains__(self, object):
        return object in self._dice
    
    def __iter__(self):
        return iter(self._dice)
    
    def __str__(self):
        return '[{}]'.format(', '.join(color.name for color in self._dice))
    