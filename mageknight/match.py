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

from PyQt5 import QtCore

from mageknight import map, player

class RoundType(enum.Enum):
    day = 1
    night = 2
    
    
class Round:
    def __init__(self, number, type):
        self.number = number
        self.type = type


class Match(QtCore.QObject):
    roundChanged = QtCore.pyqtSignal(Round)
    
    def __init__(self):
        super().__init__()
        self.round = Round(1, RoundType.day)
        self.players = [player.Player('Arythea', player.Hero.Arythea),
                        player.Player('Goldyx', player.Hero.Goldyx),
                        player.Player('Norowas', player.Hero.Norowas),
                        player.Player('Tovak', player.Hero.Tovak)
                        ]
        self.source = ManaSource(len(self.players)+2)
        self.map = map.Map(map.MapShape.wedge)
    
        
class Mana(enum.Enum):
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
    
    
class ManaSource(QtCore.QObject):
    """The mana source contains the mana dice available to all players. It behaves like a read-only list, so 
    e.g. 'len(source)' and 'source[2]' work as expected. The additional attribute 'count' stores the initial
    number of dice in the source (typically number of players + 2). The number returned by len(source) can
    be lower due to e.g. Mana Steal.
    """ 
    changed = QtCore.pyqtSignal()
    
    def __init__(self, count):
        super().__init__()
        self.count = count
        self._dice = None
        self.shuffle()
    
    # Methods required for a read-only list
    def __len__(self, index):
        return len(self._dice)
    
    def __getitem__(self, index):
        return self._dice(index)
    
    def __contains__(self, object):
        return object in self._dice
    
    def __iter__(self):
        return iter(self._dice)
    
    def isValidAtRoundStart(self):
        """Return whether at least half of the dice show a basic colors (as required by the rules at round
        start)."""
        return sum(1 if die.basic else 0 for die in self._dice) >= self.count / 2
        
    def shuffle(self):
        """Shuffle all dice in the source according to the rules."""
        while True:
            self._dice = [Mana.random() for _ in range(self.count)]
            if self.isValidAtRoundStart():
                break
        self.changed.emit()
        
