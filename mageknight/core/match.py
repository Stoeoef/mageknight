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

import random

from PyQt5 import QtCore

from mageknight import stack, hexcoords
from mageknight.data import *  # @UnusedWildImport
from mageknight.core import effects, cards, units
from mageknight.core import source, player, map, effectlist, shop, combat, actions  # @Reimport
from mageknight.gui import dialogs
from .decorators import action


class Match(QtCore.QObject):
    """This is the central object managing a match."""
    stateChanged = QtCore.pyqtSignal(State)
    roundChanged = QtCore.pyqtSignal(Round)
    terrainCostsChanged = QtCore.pyqtSignal()
    
    def __init__(self, players):
        super().__init__()
        self.stack = stack.UndoStack()
        
        self.round = Round(1, RoundType.day)
        self.state = State.movement
        self.players = players
        self.source = source.ManaSource(self, len(self.players)+2)
        self.map = map.Map(self, MapShape.wedge)
        self.effects = effectlist.EffectList(self)
        self.shop = shop.Shop(self)
        self.shop.refreshUnits()
        self.resetTerrainCosts()
        self.combat = combat.Combat(self)
        self.actions = actions.ActionList(self)
        
        for player in self.players:
            player.match = self
            self.map.addPerson(player, hexcoords.HexCoords(0, 0))
            player.initDeedDeck()
            player.drawCards()
        self.currentPlayer = self.players[0]    
    
    def setState(self, state):
        print("SET STATE", state)
        assert isinstance(state, State)
        if state != self.state:
            self.stack.push(stack.Call(self._setState, state),
                            stack.Call(self._setState, self.state))
    
    def _setState(self, state):
        if state != self.state:
            self.state = state
            self.stateChanged.emit(state)
                
    def revealNewInformation(self):
        """Call this whenever new information is revealed. It will clear the undo stack."""
        if self.stack.isComposing():
            self.stack.endMacro()
            self.stack.clear()
            self.stack.beginMacro()
        else:
            self.stack.clear()
    
    def checkEffectPlayable(self, effect=None, type=EffectType.unknown):
        """Check whether the given effect is playable in the current state and raise an InvalidAction error
        if not. Instead of specifying an effect it is possible to specify only an EffectType, or give no
        information at all (in this case the method will only check whether it is allowed to play any
        effects).
        """
        if self.state.inCombat:
            self.combat.checkEffectPlayable(effect, type)
        else:
            if effect is not None:
                type = effect.type
                
            if type == EffectType.movement and self.state is not State.movement:
                raise InvalidAction("Cannot play movement effects now.")
            elif type == EffectType.influence and self.state is not State.interaction:
                raise InvalidAction("Cannot play influence effects now.")
            elif type == EffectType.combat:
                raise InvalidAction("Cannot play combat effects now.")
        
    def nightRulesApply(self):
        """Return whether night rules hold currently. This is true during nights, in dungeons, etc."""
        return self.round.type == RoundType.night
        
    def isTerrainPassable(self, terrain):
        """Return whether the given terrain is currently passable for the current player. This might change
        as an effect of e.g. spells."""
        assert isinstance(terrain, Terrain)
        return terrain in self.terrainCosts
    
    def resetTerrainCosts(self):
        self.terrainCosts = {
            Terrain.plains: 2,
            Terrain.hills: 3,
            Terrain.forest: 3 if self.round.type == RoundType.day else 5,
            Terrain.wasteland: 4,
            Terrain.desert: 5 if self.round.type == RoundType.day else 3,
            Terrain.swamp: 5,
            Terrain.city: 2,
        }
        
    def reduceTerrainCost(self, terrain, amount, minimum):
        if terrain in self.terrainCosts: # should always be the case
            self.setTerrainCost(terrain, max(minimum, self.terrainCosts[terrain] - amount))
        
    def setTerrainCost(self, terrain, cost):
        """Set the movement cost of the given terrain to *cost*. If *cost* is None, the terrain will not
        be passable."""
        self.stack.push(stack.Call(self._setTerrainCost, terrain, cost),
                        stack.Call(self._setTerrainCost, terrain, self.terrainCosts.get(terrain)))
        
    def _setTerrainCost(self, terrain, cost):
        if cost is not None:
            self.terrainCosts[terrain] = cost
        elif terrain in self.terrainCosts:
            del self.terrainCosts[terrain]
        self.terrainCostsChanged.emit()
    
    def _manaOptions(self, player, color):
        colors = [color] # during day we might add Mana.gold, skills might add even more
        
        if not self.nightRulesApply():
            if color is Mana.black:
                return []
            elif color is not Mana.gold:
                colors.append(Mana.gold)
        else:
            if color is Mana.gold:
                return []
        
        options = []
        
        if player == self.currentPlayer:
            # Check available tokens
            effect = self.effects.find(effects.ManaTokens)
            if effect is not None:
                for color in colors:
                    if effect[color] > 0:
                        options.append(('token', color, '{} token'.format(color.name)))
        
            # Check source
            if self.source.limit > 0:
                for color in colors:
                    if color in self.source:
                        options.append(('die', color, '{} die'.format(color.name)))
        
        # Check crystals
        for color in colors:
            if color.isBasic and player.crystals[color] > 0:
                options.append(('crystal', color, '{} crystal'.format(color.name)))
                
        return options
                
    def hasMana(self, color):
        """Return whether the player can pay a mana of the given color."""
        return len(self._manaOptions(self.currentPlayer, color)) > 0
        
    def payMana(self, color):
        """Pay a mana in the given color."""
        options = self._manaOptions(self.currentPlayer, color)
        if len(options) == 0:
            if self.source.limit == 0:
                raise InvalidAction("You don't have mana (cannot use another die).")
            else: raise InvalidAction("You don't have mana.")
        
        if len(options) == 1 and options[0][0] != 'crystal': # always ask before using crystals
            type, color, _ = options[0]
        else:            
            type, color, _ = dialogs.choose(options, label=lambda t: t[2], title=self.tr("Pay mana"))
        if type == 'token':
            self.effects.remove(effects.ManaTokens(color))
        elif type == 'die':
            self.source.take(color)
        else:
            self.currentPlayer.removeCrystal(color)
    
    def payMovePoints(self, cost):
        if self.effects.movePoints < cost:
            raise InvalidAction("Not enough move points")
        if cost > 0:
            self.effects.remove(effects.MovePoints(cost))
     
    def payInfluencePoints(self, cost):
        if self.effects.influencePoints < cost:
            raise InvalidAction("Not enough influence points")
        if cost > 0:
            self.effects.remove(effects.InfluencePoints(cost))

    def chooseEnemy(self, category):
        enemies = []
        for enemy in category.all():
            enemies.extend([enemy] * enemy.count)
        return random.choice(enemies)
        
    @action
    def playCard(self, player, card, effectIndex=0):
        """Play the given card. For cards with several actions, *effectIndex* determines which action
        to play (e.g. 0 for basic effect and 1 for strong effect of action cards).
        """
        self.checkEffectPlayable(type=card.effectType)
        if isinstance(card, cards.ActionCard):
            if effectIndex == 0:
                #player.discard(card) # TODO: disabled to make debugging life easier
                card.basicEffect(self, player)
            elif effectIndex == 1:
                self.payMana(card.color)
                #player.discard(card) # TODO: see above
                card.strongEffect(self, player)
            else: raise ValueError("Invalid effect number for card '{}': {}".format(card.name, effectIndex))
        
    def sidewaysEffects(self):
        """Return all effects that can be achieved by playing a card sideways (might change due to skills).
        """
        options = [effects.MovePoints(1),
                   effects.InfluencePoints(1),
                   effects.AttackPoints(1),
                   effects.BlockPoints(1)
                   ]
        return options
    
    @action
    def playSideways(self, player, card, effectIndex):
        """Play the given card sideways. *effectIndex* is the index of the desired effect from
        self.sidewaysEffects()."""
        # No need to call checkEffectPlayable, because it will be called by effects.add.
        effect = self.sidewaysEffects()[effectIndex]
        #player.discard(card) # TODO: disabled to make debugging life easier
        self.effects.add(effect)
        
    @action(State.movement)
    def movePlayer(self, player, coords):
        """Move the given player to the specified hex. Use this method only for standard moves in the
        movement phase, not for Flight, Underground Travel and similar special effects. The player's
        move points will be reduced appropriately.
        """
        pos = self.map.persons[player]
        if pos == coords:
            return
        if not coords.isNeighborOf(pos):
            raise InvalidAction("Can only move to adjacent fields.")
        terrain = self.map.terrainAt(coords)
        if terrain is None or not self.isTerrainPassable(terrain):
            raise InvalidAction("This field is not passable")
        site = self.map.siteAt(coords) # returns only active sites
        if site is not None:
            if site.type in [Site.maraudingOrcs, Site.draconum]:
                raise InvalidAction("Cannot enter a field occupied by a marauding enemy.")
        
        self.payMovePoints(self.terrainCosts[terrain])
        self.map.movePerson(player, coords)
        oldEnemies = set(self.map.getAdjacentMaraudingEnemies(pos))
        newEnemies = set(self.map.getAdjacentMaraudingEnemies(coords))
        if len(oldEnemies.intersection(newEnemies)) > 0:
            enemies = []
            for site in oldEnemies.intersection(newEnemies):
                enemies.extend(site.enemies)
            self.combat.begin(enemies)
        elif len(self.map.getAdjacentMaraudingEnemies(coords)) > 0:
            self.actions.add('marauding', self.tr("Fight marauding enemies"))
        else: self.actions.remove('marauding') 
        
    @action
    def activateUnit(self, player, unit, action):
        assert isinstance(unit, units.Unit)
        assert action in unit.actions
        self.checkEffectPlayable() # TODO action type
        if not unit.isReady:
            raise InvalidAction("This unit is spent.")
        if unit.isWounded:
            raise InvalidAction("This unit is wounded.")
        if action.cost is not None:
            self.payMana(action.cost)
        unit.activate(action, self, player)
        player.spendUnit(unit)
        
    @action(State.interaction)
    def recruitUnit(self, player, unit):
        # TODO: check for interaction
        if not self.map.siteAtPlayer(player) in unit.sites:
            raise InvalidAction("Cannot recruit unit at this place.")
        if player.unitLimit <= player.unitCount:
            unitToDisband = dialogs.choose(player.units,
                                           label=self.tr("All slots occupied. Choose a unit to disband."))
            player.removeUnit(unitToDisband)
        self.payInfluencePoints(unit.cost)
        self.shop.takeUnit(unit)
        player.addUnit(unit)
        
    @action(State.combatStates())
    def setEnemySelected(self, player, enemy, selected):
        self.combat.setEnemySelected(enemy, selected)
    
    @action(State.combatStates())
    def combatNext(self, player):
        self.combat.next()
        
    @action(State.combatStates())
    def combatSkip(self, player):
        self.combat.skip()
    
    @action(State.assignDamage)
    def assignDamageToUnit(self, player, unit):
        self.combat.assignDamageToUnit(unit)
        
    @action
    def activateAction(self, player, actionId):
        print(actionId)
        
