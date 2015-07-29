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
from .effects import MovePoints, InfluencePoints, HealPoints


class EffectList(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    
    def __init__(self, match):
        super().__init__()
        self.match = match
        self._list = []
    
    def add(self, effect):
        self._modify(effect, "add")

    def remove(self, effect):
        self._modify(effect, "remove")

    def _modify(self, effect, func):
        # first try to combine the effect with an existing one:
        for i, e in enumerate(self._list):
            new = getattr(e, func)(effect)
            if new is False:
                continue
            elif new is not None:
                old = self._list[i]
                assert old != new
                self.match.stack.push(stack.Call(lambda: self._assignIth(i, new)),
                                      stack.Call(lambda: self._assignIth(i, old)))
            else:
                old = self._list[i]
                self.match.stack.push(stack.Call(lambda: self._popIth(i)),
                                      stack.Call(lambda: self._insertIth(i, old)))
            break
        else:
            # insert at the right position
            i = 0
            while i < len(self._list) and self._list[i] < effect:
                i += 1
            self.match.stack.push(stack.Call(lambda: self._insertIth(i, effect)),
                                  stack.Call(lambda: self._popIth(i)))        

    def _insertIth(self, i, value):
        self._list.insert(i, value)
        self.changed.emit()

    def _popIth(self, i):
        self._list.pop(i)
        self.changed.emit()

    def _assignIth(self, i, value):
        self._list[i] = value
        self.changed.emit()

    def clear(self):
        self._list = []
        self.changed.emit()
        
    def __iter__(self):
        return iter(self._list)
    
    def __len__(self):
        return len(self._list)
    
    def __contains__(self, item):
        return item in self._list
    
    def __getitem__(self, index):
        return self._list[index]
    
    def find(self, effectType, reverse=False):
        theList = self._list if not reverse else reversed(self._list)
        for e in theList:
            if isinstance(e, effectType):
                return e
        else: return None
        
    def findEffects(self, effectType):
        return [e for e in self._list if isinstance(e, effectType)]
        
    @property
    def movePoints(self):
        return sum(e.points for e in self._list if isinstance(e, MovePoints))
                   
    @property
    def influencePoints(self):
        return sum(e.points for e in self._list if isinstance(e, InfluencePoints))
    
    @property
    def healPoints(self):
        return sum(e.points for e in self._list if isinstance(e, HealPoints))
    
