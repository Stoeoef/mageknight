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

from mageknight.gui import dialogs
from mageknight.data import * # @UnusedWildImport
from mageknight.core import effects
from mageknight.core.assets import RegularUnit, ability


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
