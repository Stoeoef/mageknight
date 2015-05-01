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

"""Abstract base classes and miscellaneous stuff around assets (i.e. cards and units)."""

import functools

from mageknight import utils


def get(name):
    """Return the card or unit of the given name."""
    classes = [BasicAction, AdvancedAction, Artifact, RegularUnit, EliteUnit]
    for cls in classes:
        for subclass in cls.__subclasses__():
            if subclass.name == name:
                return subclass()
    if name == 'wound':
        return Wound()
    raise ValueError("There is no asset with name '{}'.".format(name))


class Card:
    """Abstract base class for all cards. Note that two instances are always considered different."""
    def __str__(self):
        return self.title
    
    def __repr__(self):
        return type(self).__name__
    
    @property
    def isWound(self):
        return isinstance(self, Wound)
    
    @classmethod
    def all(cls):
        result = []
        for cardClass in cls.__subclasses__():
            result.append(cardClass())
        return result
    
    
class ActionCard(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/{}/{}.jpg'
                            .format('advanced_actions' if self.isAdvanced else 'basic_actions', self.name))

    
class BasicAction(ActionCard):
    isAdvanced = False


class AdvancedAction(ActionCard):
    isAdvanced = True


class Spell(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/spells/{}.jpg'.format(self.name))


class Artifact(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/artifacts/{}.jpg'.format(self.name))


class Wound(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/wound.jpg')


class UnitAbility:
    """This method represents a single ability of a unit. Besides the method that is invoked, when the
    ability is activated, it stores the position (y-coordinate) on the card (to map clicks to abilities)
    and the cost (None or a mana color).
    """
    def __init__(self, pos, cost, method):
        self.pos = pos
        self.cost = cost
        self.method = method
        
    def activate(self, unit, match, player):
        self.method(unit, match, player)
        
    def __repr__(self):
        return self.method
    

def ability(pos, cost=None):
    """Decorator to transform methods to UnitAbilities. *pos* is the y-coordinate of the ability on the 
    card (None for the first ability). *cost* is either None or a mana color.
    """
    if pos is None:
        pos = 294 # y-coordinate of the top of the first ability
    return functools.partial(UnitAbility, pos, cost)


class Unit:
    """Abstract base class for units. To create a new unit you must create a subclass of either
    RegularUnit or EliteUnit, specify the necessary attributes (in particular 'abilities' which specifies
    how many abilities the unit has) and implement the methods 'ability1', 'ability2' etc..
    """
    # Uncommented attributes are defined in subclasses
    # name: uniqe identifier, e.g. "guardian_golems",
    # title: user-readable name,
    # count: number of cards of this unit in the game (specifies unit card distribution),
    # cost: influence points necessary to recruit this unit
    # level: level of unit
    # armor: armor points
    # isElite: whether the unit is an elite unit
    # sites: List of Site-instances; determines where this unit can be recruited.
    resistances = tuple() # list of Elements against which this unit is resistant
    owner = None        # player which recruited this unit # TODO: make item attribute
    wounds = 0          # number of wounds ∈ {0,1,2},  see isWounded
    isReady = True      
    isProtected = False # true if no damage can be assigned to this unit
    
    def __str__(self):
        return self.title
    
    def __repr__(self):
        return type(self).__name__
    
    def pixmap(self):
        """Return the pixmap of this unit's card."""
        return utils.getPixmap('mk/cards/{}/{}.jpg'
                               .format('elite_units' if self.isElite else 'regular_units', self.name))
        
    @property
    def isWounded(self):
        return self.wounds > 0
    
    @property
    def abilities(self):
        """A sorted list of all abilities."""
        abilities = [x for x in type(self).__dict__.values() if isinstance(x, UnitAbility)]
        abilities.sort(key=lambda ability: ability.pos)
        return abilities
    
    @classmethod
    def all(cls):
        result = []
        for unitClass in cls.__subclasses__():
            for _ in range(unitClass.count):
                result.append(unitClass())
        return result
    
    @staticmethod
    def get(name):
        """Return a unit from its name."""
        for subclass in RegularUnit.__subclasses__() + EliteUnit.__subclasses__():
            if subclass.name == name:
                return subclass()
        raise ValueError("There is no unit with name '{}'.".format(name))
    

class RegularUnit(Unit):
    """Abstract base class for regular units."""
    isElite = False
    

class EliteUnit(Unit):
    """Abstract base class for elite units."""
    isElite = True
