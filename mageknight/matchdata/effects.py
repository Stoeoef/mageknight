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

from .core import Mana, InvalidAction


@functools.total_ordering
class Effect:
    def add(self, other):
        return False
    
    def remove(self, other):
        return False
        
    def __lt__(self, other):
        return type(self).__name__ < type(other).__name__ # just some ordering that always stays the same
    
    def __eq__(self, other):
        return other is self # should be implemented in subclasses


class PointsEffect(Effect):
    def __init__(self, points):
        self.points = points
    
    def _changed(self, amount):
        newPoints = self.points + amount
        if newPoints == 0:
            return None
        elif newPoints < min(0, self.points): # allow negative numbers if bigger than current number 
            return False # cannot pay
        else: return type(self)(newPoints)
        
    def add(self, other):
        if type(self) is type(other):
            return self._changed(other.points)
        else: return False
    
    def remove(self, other):
        if type(self) is type(other):
            return self._changed(-other.points)
        else: return False
        
    def __str__(self):
        return '{}: {}'.format(self.name, self.points)
    
    def __eq__(self, other):
        return type(other) is type(self) and other.points == self.points
    
    
class MovePoints(PointsEffect):
    name = translate("Effects", "Move points")
    
    def __init__(self, points):
        super().__init__(points)
        if points < 0:
            raise ValueError("Move points must not be negative.")
        
        
class InfluencePoints(PointsEffect):
    name = translate("Effects", "Influence points")
    # note: influence points can be negative due to reputation


class ManaTokens(Effect):
    def __init__(self, tokens=None):
        self._tokens = {} # mapping color->number
        if isinstance(tokens, dict):
            self._tokens.update(tokens)
        elif isinstance(tokens, Mana):
            self._tokens[tokens] = 1
        else:
            assert tokens is None
             
    def add(self, other):
        if isinstance(other, ManaTokens):
            _tokens = {}
            for color in Mana:
                count = self._tokens.get(color, 0) + other._tokens.get(color, 0)
                if count > 0:
                    _tokens[color] = count
            effect = ManaTokens()
            effect._tokens = _tokens
            return effect
        return False
    
    def remove(self, other):
        if isinstance(other, ManaTokens):
            _tokens = {}
            for color in Mana:
                count = self._tokens.get(color, 0) - other._tokens.get(color, 0)
                if count > 0:
                    _tokens[color] = count
                elif count < 0:
                    return False # cannot pay this mana
            if len(_tokens) > 0:
                effect = ManaTokens()
                effect._tokens = _tokens
                return effect
            else: return None # nothing remaining
        return False
        
    def __str__(self):
        strings = ['{}: {}'.format(color.name, self._tokens[color])
                   for color in Mana if color in self._tokens] 
        return ', '.join(strings)
    
    def __contains__(self, key):
        return key in self._tokens
    
    def __getitem__(self, key):
        return self._tokens[key]
    
    
class EffectList(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._list = []
        
    def add(self, effect):
        # first try to combine the effect with an existing one:
        for i, e in enumerate(self._list):
            new = e.add(effect)
            if new is False:
                continue
            elif new is not None:
                self._list[i] = new
            else: del self._list[i]
            self.changed.emit()
            return
        else:
            # insert at the right position
            i = 0
            while i < len(self._list) and self._list[i] < effect:
                i += 1
            self._list.insert(i, effect)
            self.changed.emit()
        
    def remove(self, effect):
        for i, e in enumerate(self._list):
            new = e.remove(effect)
            if new is False:
                continue
            elif new is not None:
                self._list[i] = new
            else: del self._list[i]
            self.changed.emit()
            return True
        else: False
        
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
