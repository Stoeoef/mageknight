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

from mageknight import stack


class ManaSource(QtCore.QObject):
    """The mana source contains the mana dice available to all players. It behaves like a read-only list, so 
    e.g. 'len(source)' and 'source[2]' work as expected. The additional attribute 'count' stores the initial
    number of dice in the source (typically number of players + 2). The number returned by len(source) can
    be lower due to e.g. Mana Steal.
    """ 
    changed = QtCore.pyqtSignal()
    
    def __init__(self, match, count):
        super().__init__()
        self.match = match
        self.count = count
        self.limit = 1
        self._dice = None
    
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
    
    def remove(self, color):
        """Undoably remove a die of the given color from the source."""
        index = self._dice.index(color)
        self.match.stack.push(stack.Call(self._remove, index),
                              stack.Call(self._insert, index, color))
        
    def _insert(self, index, color):
        """Insert a die of the given color at the specified index."""
        self._dice.insert(index, color)
        self.changed.emit()
        
    def _remove(self, index):
        """Remove the die at the given index from the source."""
        self._dice.pop(index)
        self.changed.emit()

    def changeLimit(self, amount):
        self.match.stack.push(stack.Call(self._changeLimit, amount),
                              stack.Call(self._changeLimit, -amount))
        
    def _changeLimit(self, amount):
        self.limit += amount
