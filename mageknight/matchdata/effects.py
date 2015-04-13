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

import functools

from PyQt5 import QtCore
translate = QtCore.QCoreApplication.translate

from .core import Mana


@functools.total_ordering
class Effect:
    def combine(self, other):
        return False
    
    def __lt__(self, other):
        return type(self).__name__ < type(other).__name__ # just some ordering that always stays the same
    
    def __eq__(self, other):
        return other is self # should be implemented in subclasses


class PointsEffect(Effect):
    def __init__(self, points):
        self.points = points
        
    def combine(self, other):
        if type(self) is type(other):
            self.points += other.points
            return True
        else: return False
        
    def __str__(self):
        return '{}: {}'.format(self.name, self.points)
    
    def __eq__(self, other):
        return type(other) is type(self) and other.points == self.points
    
    
class MovePoints(PointsEffect):
    name = translate("Effects", "Move points")
        
class InfluencePoints(PointsEffect):
    name = translate("Effects", "Influence points")


class ManaToken(Effect):
    def __init__(self, tokens):
        self.tokens = tokens # mapping color->number
        
    def combine(self, other):
        if isinstance(other, ManaToken):
            for color, number in other.tokens.items():
                if color in self.tokens:
                    self.tokens[color] += number
                else: self.tokens[color] = number
            return True
        else: return False
        
    def __str__(self):
        return ['{}: {}'.format(color.name, self.tokens[color]) for color in Mana].join(', ')
    
    
class EffectList(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._list = []
        
    def add(self, effect):
        # first try to combine the effect with an existing one:
        if any(e.combine(effect) for e in self._list):
            self.changed.emit()
        else:
            # insert at the right position
            i = 0
            while i < len(self._list) and self._list[i] < effect:
                i += 1
            self._list.insert(i, effect)
            self.changed.emit()
        
    def remove(self, effect):
        self._list.remove(effect)
        self.changed.emit()
        
    def __iter__(self):
        return iter(self._list)
    
    def __len__(self):
        return len(self._list)
    
    def __contains__(self, item):
        return item in self._list
    
    def __getitem__(self, index):
        return self._list[index]
    
    def findEffect(self, effectType):
        for e in self._list:
            if isinstance(e, effectType):
                return e
        else: return None
        
    @property
    def movePoints(self):
        return sum(e.points for e in self._list if isinstance(e, MovePoints))
                   
    @property
    def influencePoints(self):
        return sum(e.points for e in self._list if isinstance(e, InfluencePoints))
            
    def changeMovePoints(self, points):
        newPoints = self.movePoints + points
        if newPoints > 0:
            effect = self.findEffect(MovePoints)
            effect.points = newPoints
            self.changed.emit()
        elif newPoints == 0:
            effect = self.findEffect(MovePoints)
            if effect is not None:
                self.remove(effect)
        else: # newPoints < 0:
            raise ValueError("Move points must not be less than 0.")
