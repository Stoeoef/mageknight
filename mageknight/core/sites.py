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
translate = QtCore.QCoreApplication.translate

from mageknight.data import * # @UnusedWildImport
from mageknight.core import effects 


def create(siteType, match, coords):
    for cls in ALL_SITES:
        if cls.type is siteType:
            return cls(match, coords)
    else: return None # TODO: raise an error instead when all sites are implemented
    
    
class SiteOnMap:
    def __init__(self, coords):
        self.coords = coords
        self.isActive = True
        self.enemies = []
        self.owner = None
        
    def __getattr__(self, attr):
        return getattr(self.type, attr)
    
    def onEnter(self, match, player): pass
    def onAdjacent(self, match, player): pass
    def onCombatEnd(self, match, player): pass
    

class FortifiedSite(SiteOnMap):
    def onEnter(self, match, player):
        if self.owner is None:
            player.addReputation(-1)
            match.map.revealEnemies(self)
            match.combat.begin(self.enemies)
        else:
            match.startInteraction() # TODO: conquer keeps of other players
            
    def onAdjacent(self, match, player):
        if self.owner is None and match.round.type is RoundType.day:
            match.map.revealEnemies(self)
            
    def onCombatEnd(self, match, player):
        match.map.setOwner(self, player)
        match.map.setEnemies(self, [])
    
    
class Keep(FortifiedSite):
    type = Site.keep
    
    def __init__(self, match, coords):
        super().__init__(coords)
        self.enemies = [UnknownEnemy(EnemyCategory.keep)]
    

class MaraudingOrcs(FortifiedSite):
    type = Site.maraudingOrcs
    
    def __init__(self, match, coords):
        super().__init__(coords)
        self.enemies = [match.chooseEnemy(EnemyCategory.maraudingOrcs)]
        
    def onEnter(self, match, player):
        if self.isActive:
            raise InvalidAction("Cannot enter a space occupied by marauding orcs.")
        
    
        
    
class Village(SiteOnMap):
    type = Site.village
    
    def __init__(self, match, coords):
        super().__init__(coords)
        self.plundered = False
    
    def onEnter(self, match, player):
        if match.state == State.movement: # should always be the case
            match.actions.add('interact', translate('sites', "Interact"), self.interact)
        
    def interact(self, match, player):
        match.startInteraction()
        match.actions.add('heal', translate('sites', "Buy healing"), self.heal)
        
    def heal(self, match, player):
        match.payInfluencePoints(3)
        match.effects.add(effects.HealPoints(1))
        

ALL_SITES = (Keep, MaraudingOrcs, Village)
    