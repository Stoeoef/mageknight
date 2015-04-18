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

from mageknight.data import Mana, InvalidAction
from . import basesource


class ManaSource(basesource.ManaSource):
    def __init__(self, match, count):
        super().__init__(match, count)
        self.reset()
        
    def shuffle(self):
        """Shuffle all dice in the source."""
        self.match.revealNewInformation()
        self._dice = [Mana.random() for _ in range(self.count)]
        self.changed.emit()
    
    def reset(self):
        self.shuffle()
        # Rules: Source must be reshuffled if less than half of the dice show a basic color
        while sum(1 if die.isBasic else 0 for die in self._dice) < self.count / 2:
            self.shuffle()
        self.limit = 1        

    def take(self, colorOrIndex):
        """Take a die from the source to pay a mana for the current player. The argument is either the
        index of the die or a color.
        """ 
        if isinstance(colorOrIndex, int):
            color = self._dice[colorOrIndex] 
        else: color = colorOrIndex
        
        if self.limit == 0:
            raise InvalidAction("You cannot take another die in this turn")
        if color == Mana.black and not self.match.nightRulesApply():
            raise InvalidAction("You must not use black mana during day.")
        if color == Mana.gold and self.match.nightRulesApply():
            raise InvalidAction("You must not use gold mana during night.")
        self.changeLimit(-1)
        self.remove(color)
        