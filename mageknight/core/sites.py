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

import random

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
        self.enemies = []
        self.owner = None
        
    def __getattr__(self, attr):
        return getattr(self.type, attr)
    
    def onEnter(self, match, player): pass
    def onAdjacent(self, match, player): pass
    def onCombatEnd(self, match, player): pass
    def onBeginOfTurn(self, match, player): pass
    def onEndOfTurn(self, match, player): pass
    def updateActions(self, match, player): pass
    
    def onEnemyKilled(self, match, player, enemy):
        match.map.removeEnemy(self, enemy)
        player.fame += enemy.fame
        

class FortifiedSite(SiteOnMap):
    def onEnter(self, match, player):
        if self.owner is None:
            player.reputation -= 1
            match.map.revealEnemies(self)
            match.combat.init(self) # use init instead of start, so that marauding enemies may be added
        # TODO: conquer keeps of other players
    
    def updateActions(self, match, player):
        if match.state == State.movement:
            match.actions.add('interact', translate('sites', "Interact"), match.startInteraction)
            
    def onAdjacent(self, match, player):
        if self.owner is None and match.round.type is RoundType.day:
            match.map.revealEnemies(self)
            
    def onCombatEnd(self, match, player):
        if len(self.enemies) == 0:
            match.map.setOwner(self, player)
    
    
class AdventureSite(SiteOnMap):
    def updateActions(self, match, player):
        if self.owner is None or self.canReenter:
            match.actions.add('enter', translate('sites', "Enter"), self.enter)
            
    def onCombatEnd(self, match, player):
        if self.owner is None and len(self.enemies) == 0:
            # entered for the first time
            match.map.setOwner(self, player)
            self.addReward(match) # defined in subclasses
        else:
            # reentered
            # remove enemies so that new enemies are chosen at the next fight
            match.map.setEnemies(self, [])
            
    def addReward(self):
        """Implemented in subclasses to add the reward. This is not called when the site is re-entered."""
        pass


class CrystalMines(SiteOnMap):
    type = Site.crystalMines
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.color = data[0]
        
    def onEndOfTurn(self, match, player):
        player.addCrystal(self.color)
        

class Draconum(SiteOnMap):
    type = Site.draconum
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.enemies = match.chooseEnemies([EnemyCategory.draconum])
        
    def onEnter(self, match, player):
        if (self.enemies):
            raise InvalidAction("Cannot enter a space occupied by a draconum.")
    
    def onEnemyKilled(self, match, player, enemy):
        super().onEnemyKilled(match, player, enemy)
        player.reputation += 2


class Dungeon(AdventureSite):
    type = Site.dungeon
    canReenter = True
    
    def enter(self, match, player):
        match.map.setEnemies(self, match.chooseEnemies([EnemyCategory.dungeon]))
        match.combat.start(self, unitsAllowed=False, nightRules=True)
        
    def addReward(self, match):
        if random.randint(1,3) == 1:
            match.combat.addReward(CombatReward(CombatRewardType.spell))
        else: match.combat.addReward(CombatReward(CombatRewardType.artifact))
        match.revealNewInformation()


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
        
    def onCombatEnd(self, match, player):
        super().onCombatEnd(match, player)
        if len(self.enemies) == 0:
            match.combat.addReward(CombatReward(CombatRewardType.spell))


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
        
    
class MaraudingOrcs(SiteOnMap):
    type = Site.maraudingOrcs
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.enemies = match.chooseEnemies([EnemyCategory.maraudingOrcs])
        
    def onEnter(self, match, player):
        if self.enemies:
            raise InvalidAction("Cannot enter a space occupied by marauding orcs.")
    
    def onEnemyKilled(self, match, player, enemy):
        super().onEnemyKilled(match, player, enemy)
        player.reputation += 1


class Monastery(SiteOnMap):
    type = Site.monastery
    
    def updateActions(self, match, player):
        # No actions if monastery has an owner (it was burned)
        if self.owner is None and match.state == State.movement:
            match.actions.add('interact', translate('sites', "Interact"), self.interact)
            match.actions.add('burn', translate('sites', "Burn monastery"), self.burn)
        
    def interact(self, match, player):
        match.startInteraction()
        match.actions.add('heal', translate('sites', "Buy healing"), self.heal)
        
    def heal(self, match, player):
        match.payInfluencePoints(2)
        match.effects.add(effects.HealPoints(1))
        
    def burn(self, match, player):
        player.reputation -= 3
        match.map.setEnemies(self, match.chooseEnemies([EnemyCategory.mageTower]))
        match.combat.start(self, unitsAllowed=False)
        match.revealNewInformation()
        
    def onCombatEnd(self, match, player):
        if len(self.enemies) == 0:
            match.map.setOwner(self, player)
            match.combat.addReward(CombatReward(CombatRewardType.artifact))
        else:
            # remove enemies so that new enemies are chosen at the next fight
            match.map.setEnemies(self, [])
    

class MonsterDen(AdventureSite):
    type = Site.monsterDen
    canReenter = False
            
    def enter(self, match, player):
        match.map.setEnemies(self, match.chooseEnemies([EnemyCategory.dungeon]))
        match.combat.start(self)
        
    def addReward(self, match):
        match.combat.addReward(CombatReward(CombatRewardType.crystal, 2))


class SpawningGrounds(AdventureSite):
    type = Site.spawningGrounds
    canReenter = False
            
    def enter(self, match, player):
        match.map.setEnemies(self, match.chooseEnemies([EnemyCategory.dungeon, EnemyCategory.dungeon]))
        match.combat.start(self)
        
    def addReward(self, match):
        match.combat.addReward(CombatReward(CombatRewardType.crystal, 3))
        match.combat.addReward(CombatReward(CombatRewardType.artifact))
        

class Tomb(AdventureSite):
    type = Site.tomb
    canReenter = True
    
    def enter(self, match, player):
        match.map.setEnemies(self, match.chooseEnemies([EnemyCategory.draconum]))
        match.combat.start(self, unitsAllowed=False, nightRules=True)   
         
    def addReward(self, match):
        match.combat.addReward(CombatReward(CombatRewardType.spell))
        match.combat.addReward(CombatReward(CombatRewardType.artifact))


class Village(SiteOnMap):
    type = Site.village
    
    def __init__(self, match, coords, data):
        super().__init__(match, coords, data)
        self.plundered = False
    
    def onBeginOfTurn(self, match, player):
        if dialogs.ask(translate('sites', "Do you wish to plunder the village?")):
            player.drawCards(2)
            player.reputation -= 1
        
    def updateActions(self, match, player):
        match.actions.add('interact', translate('sites', "Interact"), self.interact)
        
    def interact(self, match, player):
        match.startInteraction()
        match.actions.add('heal', translate('sites', "Buy healing"), self.heal)
        
    def heal(self, match, player):
        match.payInfluencePoints(3)
        match.effects.add(effects.HealPoints(1))
        

ALL_SITES = (CrystalMines, Draconum, Dungeon, Keep, MageTower, MagicalGlade, MaraudingOrcs,
             Monastery, MonsterDen, SpawningGrounds, Tomb, Village)
    
