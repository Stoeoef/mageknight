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
from mageknight.gui import dialogs


def create(siteType, match, coords, data):
    for cls in ALL_SITES:
        if cls.type is siteType:
            return cls(match, coords, data)
    else: return None # TODO: raise an error instead when all sites are implemented
    
    
class SiteOnMap:
    def __init__(self, match, coords, data):
        self.coords = coords
        self.isActive = True
        self.enemies = []
        self.owner = None
        
    def __getattr__(self, attr):
        return getattr(self.type, attr)
    
    def onEnter(self, match, player): pass
    def onAdjacent(self, match, player): pass
    def onCombatEnd(self, match, player): pass
    def onBeginOfTurn(self, match, player): pass
    def onEndOfTurn(self, match, player): pass
    

class FortifiedSite(SiteOnMap):
    def onEnter(self, match, player):
        if self.owner is None:
            player.addReputation(-1)
            match.map.revealEnemies(self)
            match.combat.begin(self.enemies)
        else:
            if not isinstance(self, Keep) or self.owner is player: # TODO: conquer keeps of other players
                if match.state == State.movement: # should always be the case
                    match.actions.add('interact', translate('sites', "Interact"), match.startInteraction)
            
    def onAdjacent(self, match, player):
        if self.owner is None and match.round.type is RoundType.day:
            match.map.revealEnemies(self)
            
    def onCombatEnd(self, match, player):
        # Rules: additional marauding enemies must not be considered here
        remainingEnemies = [enemy for enemy in match.combat.remainingEnemies() if enemy in self.enemies]
        if len(remainingEnemies) == 0:
            match.map.setOwner(self, player)
        # TODO: redrawal 
        match.map.setEnemies(self, remainingEnemies)
    
    
class AdventureSite(SiteOnMap):
    def onEnter(self, match, player):
        if self.owner is None or self.canReenter:
            match.actions.add('enter', translate('sites', "Enter"), self.enter)
            
    def onCombatEnd(self, match, player):
        # note: owner does not change when a dungeon/tomb is reentered
        if len(match.combat.remainingEnemies()) == 0 and self.owner is None:
            match.map.setOwner(self, player)
            # TODO: gain reward
        match.map.setEnemies(self, [])


class CrystalMines(SiteOnMap):
    type = Site.crystalMines
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.color = data[0]
        
    def onEndOfTurn(self, match, player):
        player.addCrystal(self.color)
        
    
class Dungeon(AdventureSite):
    type = Site.dungeon
    canReenter = True
    
    def enter(self, match, player):
        # TODO: night rules, no units, reenter
        enemies = match.chooseEnemies([EnemyCategory.draconum])
        match.combat.begin(enemies)
        

class Keep(FortifiedSite):
    type = Site.keep
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.enemies = [UnknownEnemy(EnemyCategory.keep)]
        
        
class MageTower(FortifiedSite):
    type = Site.mageTower
    
    # TODO: allow to buy spells, gain a spell
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.enemies = [UnknownEnemy(EnemyCategory.mageTower)]


class MagicalGlade(SiteOnMap):
    type = Site.magicalGlade
    
    def onBeginOfTurn(self, match, player):
        color = Mana.gold if match.round.type is RoundType.day else Mana.black
        match.effects.add(effects.ManaTokens(color))
        
    def onEndOfTurn(self, match, player):
        options = []
        if any(card.isWound for card in player.handCards):
            options.append(('hand', translate('sites', "Yes, from hand")))
        if any(card.isWound for card in player.discardPile):
            options.append(('discardPile', translate('sites', "Yes, from discard pile")))
        
        if len(options) > 0:
            options.append(('no', translate('sites', "No")))
            option = dialogs.choose(
                            options,
                            labelFunc = lambda t: t[1],
                            text = translate('sites', "Magical glade: Do you wish to discard a wound?"),
                            default = options[-1])
            
            if option[0] == 'hand':
                player.heal()
            elif option[0] == 'discardPile':
                player.heal(fromDiscardPile=True)
        
    
class MaraudingOrcs(FortifiedSite):
    type = Site.maraudingOrcs
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.enemies = match.chooseEnemies([EnemyCategory.maraudingOrcs])
        
    def onEnter(self, match, player):
        if self.isActive:
            raise InvalidAction("Cannot enter a space occupied by marauding orcs.")
        
        
class Monastery(SiteOnMap):
    type = Site.monastery
    
    def onEnter(self, match, player):
        if self.owner is None and match.state == State.movement: # should always be the case
            match.actions.add('interact', translate('sites', "Interact"), self.interact)
            match.actions.add('burn', translate('sites', "Burn monastery"), self.burn)
        
    def interact(self, match, player):
        match.startInteraction()
        match.actions.add('heal', translate('sites', "Buy healing"), self.heal)
        
    def heal(self, match, player):
        match.payInfluencePoints(2)
        match.effects.add(effects.HealPoints(1))
        
    def burn(self, match, player):
        player.addReputation(-3)
        enemies = match.chooseEnemies([EnemyCategory.mageTower])
        match.map.setEnemies(self, enemies)
        match.combat.begin(self.enemies) # TODO: no units
        match.revealNewInformation()
        
    def onCombatEnd(self, match, player):
        if len(match.combat.remainingEnemies()) == 0:
            match.map.setOwner(self, player)
            # TODO: gain an artifact
        match.map.setEnemies(self, [])
    

class MonsterDen(AdventureSite):
    type = Site.monsterDen
    canReenter = False
            
    def enter(self, match, player):
        enemies = match.chooseEnemies([EnemyCategory.dungeon])
        match.combat.begin(enemies)
        

class SpawningGrounds(AdventureSite):
    type = Site.spawningGrounds
    canReenter = False
            
    def enter(self, match, player):
        enemies = match.chooseEnemies([EnemyCategory.dungeon, EnemyCategory.dungeon])
        match.combat.begin(enemies)
        

class Tomb(AdventureSite):
    type = Site.tomb
    canReenter = True
    
    def enter(self, match, player):
        # TODO: night rules, no units, reenter
        enemies = match.chooseEnemies([EnemyCategory.draconum])
        match.combat.begin(enemies)    


class Village(SiteOnMap):
    type = Site.village
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.plundered = False
    
    def onBeginOfTurn(self, match, player):
        if dialogs.ask(translate('sites', "Do you wish to plunder the village?")):
            player.drawCards(2)
            player.addReputation(-1)
        
    def onEnter(self, match, player):
        match.actions.add('interact', translate('sites', "Interact"), self.interact)
        
    def interact(self, match, player):
        match.startInteraction()
        match.actions.add('heal', translate('sites', "Buy healing"), self.heal)
        
    def heal(self, match, player):
        match.payInfluencePoints(3)
        match.effects.add(effects.HealPoints(1))
        

ALL_SITES = (CrystalMines, Dungeon, Keep, MageTower, MagicalGlade, MaraudingOrcs,
             Monastery, MonsterDen, SpawningGrounds, Tomb, Village)
    