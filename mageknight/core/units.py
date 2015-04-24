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

from PyQt5 import QtCore
translate = QtCore.QCoreApplication.translate

from mageknight import utils
from mageknight.gui import dialogs
from mageknight.data import * # @UnusedWildImport
from . import effects


class UnitAction:
    def __init__(self, pos, cost, method):
        self.pos = pos
        self.cost = cost
        self.method = method
        
    def __repr__(self):
        return self.method
        
        
def _makeActions(cls):
    data = (294, ) + cls.actions # 294 is the y-coordinate of the top of the first action
    index = 0
    while 2*index < len(data):
        yield UnitAction(data[2*index], data[2*index+1], 'action{}'.format(index+1))
        index += 1


# to make life easier actions are specified in each concrete unit class as a tuple of
# (cost, y-coord of separator, cost, y-coord,...)
# (the separators are needed to map user clicks to actions)
# This meta class converts this into a tuple of UnitAction-instances
class UnitMetaClass(type):
    def __init__(cls, name, bases, nmspc):
        super(UnitMetaClass, cls).__init__(name, bases, nmspc)
        if cls.actions is not None:
            cls.actions = tuple(_makeActions(cls))


class Unit(metaclass=UnitMetaClass):
    """Abstract base class for units."""
    resistances = tuple()
    actions = None
    owner = None
    wounds = 0
    isReady = True
    isProtected = False # true if no damage can be assigned to this unit
    
    def __str__(self):
        return self.title
    
    def __repr__(self):
        return type(self).__name__
    
    def pixmap(self):
        return utils.getPixmap('mk/cards/{}/{}.jpg'
                               .format('elite_units' if self.isElite else 'regular_units', self.name))
        
    def activate(self, action, match, player):
        getattr(self, action.method)(match, player)
        
    @property
    def isWounded(self):
        return self.wounds > 0
        

def get(name):
    """Return the card of the given unit."""
    # action cards
    for subclass in RegularUnit.__subclasses__() + EliteUnit.__subclasses__():
        if subclass.name == name:
            return subclass()
    raise ValueError("There is no unit with name '{}'.".format(name))
    

class RegularUnit(Unit):
    isElite = False
    

class EliteUnit(Unit):
    isElite = True


class Foresters(RegularUnit):
    name = 'foresters'
    title = translate('units', "Foresters")
    count = 2
    cost = 5
    level = 1
    sites = (Site.village, )
    armor = 4
    actions = (None, 417, None) # see UnitMetaClass above
    
    def action1(self, match, player):
        match.effects.add(effects.MovePoints(2))
        # TODO: reduce terrain costs
        
    def action2(self, match, player):
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
    actions = (None, 356, Mana.red, 420, Mana.blue)
    
    def action1(self, match, player):
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
        
    def action2(self, match, player):
        match.effects.add(effects.BlockPoints(4, type=Element.fire))
        
    def action3(self, match, player):
        match.effects.add(effects.BlockPoints(4, type=Element.ice))
    
        
class Herbalists(RegularUnit):
    name = 'herbalists'
    title = translate('units', "Herbalists")
    count = 2
    cost = 3
    level = 1
    sites = (Site.monastery, Site.village)
    armor = 2
    actions = (Mana.green, 356, None, 418, None) 
    
    def action1(self, match, player):
        match.effects.add(effects.HealPoints(2))
        
    def action2(self, match, player):
        # TODO: Ready a level I or II Unit
        pass
        
    def action3(self, match, player):
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
    actions = (None, 353, Mana.white, 458, None)
    
    def action1(self, match, player):
        match.effects.add(effects.InfluencePoints(4))
        
    def action2(self, match, player):
        #TODO: Target unfortified enemy does not attack this combat
        pass
    
    def action3(self, match, player):
        player.addCrystal(Mana.white)


class NorthernMonks(RegularUnit):
    name = 'northern_monks'
    title = translate('units', "Northern Monks")
    count = 1
    cost = 7
    level = 2
    sites = (Site.monastery, )
    armor = 4
    actions = (None, 387, Mana.blue)
    
    def action1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    def action2(self, match, player):
        options = [effects.AttackPoints(4, type=Element.ice),
                   effects.BlockPoints(4, type=Element.ice)]
        match.effects.add(dialogs.choose(options))
        
        
class Peasants(RegularUnit):
    name = 'peasants'
    title = translate('units', "Peasants")
    count = 3
    cost = 4
    level = 1
    sites = (Site.village, )
    armor = 3
    actions = (None, 356, None, 420, None)
    
    def action1(self, match, player):
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
        
    def action2(self, match, player):
        match.effects.add(effects.InfluencePoints(2))
        
    def action3(self, match, player):
        match.effects.add(effects.MovePoints(2))
        

class RedCapeMonks(RegularUnit):
    name = 'red_cape_monks'
    title = translate('units', "Red Cape Monks")
    count = 1
    cost = 7
    level = 2
    sites = (Site.monastery, )
    armor = 4
    actions = (None, 390, Mana.red)
    
    def action1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    def action2(self, match, player):
        options = [effects.AttackPoints(4, type=Element.fire),
                   effects.BlockPoints(4, type=Element.fire)]
        match.effects.add(dialogs.choose(options))
    
    
class SavageMonks(RegularUnit):
    name = 'savage_monks'
    title = translate('units', "Savage Monks")
    count = 1
    cost = 7
    level = 2
    sites = (Site.monastery, )
    armor = 4
    actions = (None, 386, Mana.green)
    
    def action1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    def action2(self, match, player):
        match.effects.add(effects.AttackPoints(4, range=AttackRange.siege))
        
    
class UtemCrossbowmen(RegularUnit):
    name = 'utem_crossbowmen'
    title = translate('units', "Utem Crossbowmen")
    count = 2
    cost = 6
    level = 2
    sites = (Site.keep, Site.village, )
    armor = 4
    actions = (None, 387, None)
    
    def action1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    def action2(self, match, player):
        match.effects.add(effects.AttackPoints(2, range=AttackRange.range))
        
    
class UtemGuardsmen(RegularUnit):
    name = 'utem_guardsmen'
    title = translate('units', "Utem Guardsmen")
    count = 2
    cost = 5
    level = 2
    sites = (Site.keep, Site.village, )
    armor = 5
    actions = (None, 367, None)
    
    def action1(self, match, player):
        match.effects.add(effects.AttackPoints(2))
        
    def action2(self, match, player):
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
    actions = (None, 368, None)
    
    def action1(self, match, player):
        options = [effects.AttackPoints(3), effects.BlockPoints(3)]
        match.effects.add(dialogs.choose(options))
        
    def action2(self, match, player):
        options = [effects.AttackPoints(6), effects.BlockPoints(6)]
        match.effects.add(dialogs.choose(options))
        player.woundUnit(self)
