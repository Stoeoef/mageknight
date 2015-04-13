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

from mageknight import stack
from .core import Mana
from .enemies import BlockType, AttackType, AttackRange


@functools.total_ordering
class Effect:
    def add(self, other):
        return False
    
    def remove(self, other):
        if self == other:
            return None
        else: return False
        
    def __lt__(self, other):
        return type(self).__name__ < type(other).__name__ # just some ordering that always stays the same
    
    def __eq__(self, other):
        return other is self # should be implemented in subclasses


class UniqueEffect(Effect):
    def add(self, other):
        if type(other) == type(self):
            return self
        else: return False
        
    def remove(self, other):
        if type(other) == type(self):
            return None
        else: return False
        
    def __eq__(self, other):
        return type(other) == type(self)


class PointsEffect(Effect):
    def __init__(self, points):
        assert points != 0
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

    
class BlockPoints(PointsEffect):
    def __init__(self, points, type=BlockType.physical):
        super().__init__(points)
        assert isinstance(type, BlockType)
        self.type = type
        
    def __eq__(self, other):
        return type(other) is type(self) and other.points == self.points and other.type == self.type
    
    @property
    def name(self):
        return 'Block points ({})'.format(self.type.name) # TODO: translate type


class AttackPoints(PointsEffect):
    def __init__(self, points, type=AttackType.physical, range=AttackRange.normal):
        super().__init__(points)
        assert isinstance(type, AttackType)
        self.type = type
        self.range = range
        
    def __eq__(self, other):
        return type(other) is type(self) and other.points == self.points \
                    and other.type == self.type and other.range == self.range
    
    @property
    def name(self):
        return 'Attack points ({}, {})'.format(self.type.name, self.range.name) # TODO: translate
    

class ManaTokens(Effect):
    def __init__(self, tokens=None):
        self._tokens = {color: 0 for color in Mana}
        if isinstance(tokens, dict):
            self._tokens.update(tokens)
        elif isinstance(tokens, Mana):
            self._tokens[tokens] = 1
        else:
            assert tokens is None
    
    def _change(self, tokens):
        newTokens = {color: self._tokens[color]+tokens[color] for color in Mana}
        if any(v < 0 for v in newTokens.values()):
            return False
        if all(v == 0 for v in newTokens.values()):
            return None
        else: return ManaTokens(newTokens)
        
    def add(self, other):
        if isinstance(other, ManaTokens):
            return self._change(other._tokens)
        return False
    
    def remove(self, other):
        if isinstance(other, ManaTokens):
            return self._change({color: -v for color, v in other._tokens.items()})
        return False
        
    def __str__(self):
        strings = ['{}x {}'.format(self._tokens[color], color.name)
                   for color in Mana if self._tokens[color] > 0] 
        return translate('Effects', 'Mana: ') + ', '.join(strings)
    
    def __contains__(self, color):
        return color in self._tokens and self._tokens[color] > 0
    
    def __getitem__(self, color):
        return self._tokens[color]


class Concentration(Effect):
    """This effect is used for the cards Concentration and Will Power. While it is active all PointsEffects
    will be increased by *extra* (2 for Concentration, 3 for Will Power."""
    def __init__(self, extra):
        self.extra = extra
    
    
class EffectList(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    
    def __init__(self, match):
        super().__init__()
        self.match = match
        self._list = []
    
    def add(self, effect):
        if isinstance(effect, PointsEffect) and self.find(Concentration) is not None:
            # if several Concentration effects are active, only the last one counts
            effect.points += self.find(Concentration, reverse=True).extra
        self.match.stack.push(stack.Call(self._add, effect),
                              stack.Call(self._remove, effect))
        
    def remove(self, effect):
        self.match.stack.push(stack.Call(self._remove, effect),
                              stack.Call(self._add, effect))
        
    def _add(self, effect):
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
        
    def _remove(self, effect):
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
    
    def find(self, effectType, reverse=False):
        theList = self._list if not reverse else reversed(self._list)
        for e in theList:
            if isinstance(e, effectType):
                return e
        else: return None
        
    @property
    def movePoints(self):
        return sum(e.points for e in self._list if isinstance(e, MovePoints))
                   
    @property
    def influencePoints(self):
        return sum(e.points for e in self._list if isinstance(e, InfluencePoints))
