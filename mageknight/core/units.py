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
# 

import functools

from PyQt5 import QtCore
translate = QtCore.QCoreApplication.translate

from mageknight import utils
from mageknight.gui import dialogs
from mageknight.data import * # @UnusedWildImport
from . import effects


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
    owner = None        # player which recruited this unit
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


class Foresters(RegularUnit):
    name = 'foresters'
    title = translate('units', "Foresters")
    count = 2
    cost = 5
    level = 1
    sites = (Site.village, )
    armor = 4
    
    @ability(None)
    def ability1(self, match, player):
        match.effects.add(effects.MovePoints(2))
        for terrain in Terrain.forest, Terrain.hills, Terrain.swamp:
            match.map.reduceTerrainCost(terrain, 1, 0)
        
    @ability(417)
    def ability2(self, match, player):
        match.effects.add(effects.BlockPoints(3))

    
class GuardianGolems(RegularUnit):
    name = 'guardian_golems'
    title = translate('units', "Guardian Golems")
    count = 2
    cost = 7
    level = 2
    sites = (Site.mageTower, Site.keep)
    armor = 3
    resistances = (Element.physical, )
    
    @ability(None)
    def ability1(self, match, player):
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
        
    @ability(356, Mana.red)
    def ability2(self, match, player):
        match.effects.add(effects.BlockPoints(4, element=Element.fire))
        
    @ability(420, Mana.blue)
    def ability3(self, match, player):
        match.effects.add(effects.BlockPoints(4, element=Element.ice))
    
        
class Herbalists(RegularUnit):
    name = 'herbalists'
    title = translate('units', "Herbalists")
    count = 2
    cost = 3
    level = 1
    sites = (Site.monastery, Site.village)
    armor = 2
    
    @ability(None, Mana.green)
    def ability1(self, match, player):
        match.effects.add(effects.HealPoints(2))
        
    @ability(356)
    def ability2(self, match, player):
        # TODO: Ready a level I or II Unit
        pass
        
    @ability(418)
    def ability3(self, match, player):
        match.effects.add(effects.ManaTokens(Mana.green))
    
    
class Illusionists(RegularUnit):
    name = 'illusionists'
    title = translate('units', "Illusionists")
    count = 2
    cost = 7
    level = 2
    sites = (Site.mageTower, Site.monastery)
    armor = 2
    resistances = (Element.physical, )
    
    @ability(None)
    def ability1(self, match, player):
        match.effects.add(effects.InfluencePoints(4))
        
    @ability(353, Mana.white)
    def ability2(self, match, player):
        #TODO: Target unfortified enemy does not attack this combat
        pass
    
    @ability(458)
    def ability3(self, match, player):
        player.addCrystal(Mana.white)


class NorthernMonks(RegularUnit):
    name = 'northern_monks'
    title = translate('units', "Northern Monks")
    count = 1
    cost = 7
    level = 2
    sites = (Site.monastery, )
    armor = 4
    
    @ability(None)
    def ability1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    @ability(387, Mana.blue)
    def ability2(self, match, player):
        options = [effects.AttackPoints(4, element=Element.ice),
                   effects.BlockPoints(4, element=Element.ice)]
        match.effects.add(dialogs.choose(options))
        
        
class Peasants(RegularUnit):
    name = 'peasants'
    title = translate('units', "Peasants")
    count = 3
    cost = 4
    level = 1
    sites = (Site.village, )
    armor = 3
    
    @ability(None)
    def ability1(self, match, player):
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
        
    @ability(356)
    def ability2(self, match, player):
        match.effects.add(effects.InfluencePoints(2))
        
    @ability(420)
    def ability3(self, match, player):
        match.effects.add(effects.MovePoints(2))
        

class RedCapeMonks(RegularUnit):
    name = 'red_cape_monks'
    title = translate('units', "Red Cape Monks")
    count = 1
    cost = 7
    level = 2
    sites = (Site.monastery, )
    armor = 4

    
    @ability(None)
    def ability1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    @ability(390, Mana.red)
    def ability2(self, match, player):
        options = [effects.AttackPoints(4, element=Element.fire),
                   effects.BlockPoints(4, element=Element.fire)]
        match.effects.add(dialogs.choose(options))
    
    
class SavageMonks(RegularUnit):
    name = 'savage_monks'
    title = translate('units', "Savage Monks")
    count = 1
    cost = 7
    level = 2
    sites = (Site.monastery, )
    armor = 4
    
    @ability(None)
    def ability1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    @ability(386, Mana.green)
    def ability2(self, match, player):
        match.effects.add(effects.AttackPoints(4, range=AttackRange.siege))
        
    
class UtemCrossbowmen(RegularUnit):
    name = 'utem_crossbowmen'
    title = translate('units', "Utem Crossbowmen")
    count = 2
    cost = 6
    level = 2
    sites = (Site.keep, Site.village, )
    armor = 4
    
    @ability(None)
    def ability1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    @ability(387)
    def ability2(self, match, player):
        match.effects.add(effects.AttackPoints(2, range=AttackRange.range))
        
    
class UtemGuardsmen(RegularUnit):
    name = 'utem_guardsmen'
    title = translate('units', "Utem Guardsmen")
    count = 2
    cost = 5
    level = 2
    sites = (Site.keep, Site.village, )
    armor = 5
    
    @ability(None)
    def ability1(self, match, player):
        match.effects.add(effects.AttackPoints(2))
        
    @ability(367)
    def ability2(self, match, player):
        match.effects.add(effects.BlockPoints(4))
        #TODO: lose Swiftness
    
    
class UtemSwordsmen(RegularUnit):
    name = 'utem_swordsmen'
    title = translate('units', "Utem Swordsmen")
    count = 2
    cost = 6
    level = 2
    sites = (Site.keep, )
    armor = 4
    
    @ability(None)
    def ability1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    @ability(368)
    def ability2(self, match, player):
        options = [effects.AttackPoints(6), effects.BlockPoints(6)]
        match.effects.add(dialogs.choose(options))
        player.woundUnit(self)
