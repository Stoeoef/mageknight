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

from mageknight.data import * # @UnusedWildImport


@functools.total_ordering
class Effect:
    type = EffectType.unknown
    
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
    
    def __str__(self):
        return self.title


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
    
    def _changed(self, amount, **kwargs):
        newPoints = self.points + amount
        if newPoints == 0:
            return None
        elif newPoints < min(0, self.points): # allow negative numbers if bigger than current number 
            return False # cannot pay
        else: return type(self)(newPoints, **kwargs)
        
    def _sameType(self, other):
        # if this returns true, effects can be combined. Must be reimplemented for Attack/Block types. 
        return type(self) is type(other)
        
    def add(self, other):
        if self._sameType(other):
            return self._changed(other.points)
        else: return False
    
    def remove(self, other):
        if self._sameType(other):
            return self._changed(-other.points)
        else: return False
        
    def __str__(self):
        return '{} {}'.format(self.title, self.points)
    
    def __eq__(self, other):
        return self._sameType(other) and self.points == other.points
    
    
class MovePoints(PointsEffect):
    title = translate("Effects", "Move")
    type = EffectType.movement
    
    def __init__(self, points):
        super().__init__(points)
        if points < 0:
            raise ValueError("Move points must not be negative.")
        
        
        
class InfluencePoints(PointsEffect):
    title = translate("Effects", "Influence")
    type = EffectType.influence
    # note: influence points can be negative due to reputation

    
class BlockPoints(PointsEffect):
    type = EffectType.combat
    def __init__(self, points, element=Element.physical):
        super().__init__(points)
        assert isinstance(element, Element)
        self.element = element
    
    def _changed(self, amount):
        return super()._changed(amount, element=self.element)
    
    def _sameType(self, other):
        return type(other) is type(self) and other.element == self.element
    
    @property
    def title(self):
        if self.element == Element.physical:
            return 'Block'
        else: return '{} Block'.format(self.element.title)


class AttackPoints(PointsEffect):
    type = EffectType.combat
    def __init__(self, points, element=Element.physical, range=AttackRange.normal):
        super().__init__(points)
        assert isinstance(element, Element)
        self.element = element
        self.range = range
        
    def _changed(self, amount):
        return super()._changed(amount, element=self.element, range=self.range)
    
    def _sameType(self, other):
        return type(other) is type(self) and other.element == self.element and other.range == self.range
    
    @property
    def title(self):
        if self.range != AttackRange.normal:
            title = self.range.title + ' '
        else: title = ''
        if self.element != Element.physical:
            title += self.element.title + ' '
        title += 'Attack'
        return title
    

class HealPoints(PointsEffect):
    title = translate("Effects", "Heal")
    
    def __init__(self, points):
        super().__init__(points)
        if points < 0:
            raise ValueError("Heal points must not be negative.")
    

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


class LosesResistance(Effect):
    title = translate("Effects", "Loses resistances")


class ArmorReduction(Effect):
    def __init__(self, amount):
        self.amount = amount
        
    @property
    def title(self):
        return translate("Effects", "Armor -{}".format(self.amount))


class Concentration(Effect):
    """This effect is used for the cards Concentration and Will Power. While it is active all PointsEffects
    will be increased by *extra* (2 for Concentration, 3 for Will Power."""
    def __init__(self, extra):
        self.extra = extra
    