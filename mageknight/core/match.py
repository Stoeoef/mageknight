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

import random, functools

from PyQt5 import QtCore

from mageknight import stack, hexcoords
from mageknight.data import *  # @UnusedWildImport
from mageknight.core import effects, cards
from mageknight.core import source, player, map, effectlist, shop, combat, actions, assets  # @Reimport
from mageknight.gui import dialogs
from .decorators import action

DISCARD_CARDS = True # TODO: remove this debugging option


class PlayerData:
    def __init__(self, name, hero):
        self.name = name
        self.hero = hero
        
        
class Match(QtCore.QObject):
    """This is the central object managing a match."""
    stateChanged = QtCore.pyqtSignal(State)
    roundChanged = QtCore.pyqtSignal(Round)
    
    def __init__(self, players):
        super().__init__()
        self.stack = stack.UndoStack()
        
        self.round = Round(1, RoundType.day)
        self.state = None
        self.players = [player.Player(self, data.name, data.hero) for data in players]
        self.source = source.ManaSource(self, len(self.players)+2)
        self.map = map.Map.create(self, MapShape.wedge)
        self.effects = effectlist.EffectList(self)
        self.shop = shop.Shop.create(self)
        self.combat = combat.Combat(self)
        self.actions = actions.ActionList(self)
        
        self.currentPlayer = self.players[0]
        for pl in self.players:
            pl.match = self
            self.map.addPerson(pl, hexcoords.HexCoords(0, 0))

        self.beginRound()
    
    def beginRound(self):
        self.source.reset()
        self.shop.refreshUnits()
        
        for player in self.players:
            player.initCards()
            player.drawCards()
            
        # TODO: tactic selection
        self.beginTurn()
                    
    def beginTurn(self):
        self.setState(State.movement)
        self.playerPath = [self.map.persons[self.currentPlayer]]
        site = self.map.siteAtPlayer(self.currentPlayer)
        if site is not None:
            site.onBeginOfTurn(self, self.currentPlayer)
            site.onEnter(self, self.currentPlayer)
        self.revealNewInformation() # clear stack
        
    def endTurn(self):
        if self.state is not State.endOfTurn:

            # Start end of turn sequence
            self.doForcedWithdrawal()
            site = self.map.siteAtPlayer(self.currentPlayer)
            if site is not None:
                site.onEndOfTurn(self, self.currentPlayer)

        

            # TODO: combat reward, level-up, etc.
            self.effects.clear()
            
            if len(self.combat.rewards) > 0:
                self.setState(State.combatRewards)
            else:
                self.setState(State.endOfTurn)
        else:
            # Really end turn
            self.currentPlayer.drawCards()
            self.beginTurn()

    def doForcedWithdrawal(self):
        while not self.map.isSafeSpace(self.map.persons[self.currentPlayer],
                                       self.currentPlayer):
            self.withdrawCurrentPlayer()
            self.currentPlayer.addWounds(1)

        
    def withdrawCurrentPlayer(self):
        self.playerPath.pop()
        self.map.movePerson(self.currentPlayer, self.playerPath[-1])


    def setState(self, state):
        assert isinstance(state, State)
        if state != self.state:
            self.stack.push(stack.Call(self._setState, state),
                            stack.Call(self._setState, self.state))
            self.updateActions()
    
    def _setState(self, state):
        if state != self.state:
            print("SET STATE", state)
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
    
    def newInformationRevealed(self):
        if self.stack.isComposing():
            self.stack.endMacro()
            self.stack.clear()
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
            type, color, _ = dialogs.choose(options, labelFunc=lambda t: t[2], title=self.tr("Pay mana"))
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
            
    def payHealPoints(self, cost):
        if self.effects.healPoints < cost:
            raise InvalidAction("Not enough heal points")
        if cost > 0:
            self.effects.remove(effects.HealPoints(cost))

    def chooseEnemies(self, categories):
        all = {}
        for category in categories:
            if category not in all:
                all[category] = category.all()
                    
        # draw enemies
        enemies = []
        for category in categories:
            if len(all[category]) > 0:
                index = random.randint(0, len(all[category])-1)
                enemies.append(all[category].pop(index))
            else:
                # more enemies requested as exist, should not happen
                enemies.extend(self.chooseEnemies([category])) # use default distribution
        return enemies
        
    @action
    def playCard(self, player, card, effectIndex=0):
        """Play the given card. For cards with several actions, *effectIndex* determines which action
        to play (e.g. 0 for basic effect and 1 for strong effect of action cards).
        """
        if isinstance(card, cards.ActionCard):
            self.checkEffectPlayable(type=card.effectType)
            if effectIndex == 0:
                if DISCARD_CARDS:
                    player.discard(card)
                card.basicEffect(self, player)
            elif effectIndex == 1:
                self.payMana(card.color)
                if DISCARD_CARDS:
                    player.discard(card)
                card.strongEffect(self, player)
            else: raise ValueError("Invalid effect number for card '{}': {}".format(card.name, effectIndex))
        
        elif card.isWound:
            self.payHealPoints(1)
            self.currentPlayer.removeCard(card)
            
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
        if not card.isWound:
            effect = self.sidewaysEffects()[effectIndex]
            player.discard(card)
            self.effects.add(effect)
        else:
            raise InvalidAction("Cannot play wounds sideways.")
        
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
        if terrain is None or not self.map.isTerrainPassable(terrain):
            raise InvalidAction("This field is not passable")
        
        self.payMovePoints(self.map.modifiedTerrainCosts(terrain))
        self.map.movePerson(player, coords)
        self.stack.push(stack.Call(self.playerPath.append, coords),
                        stack.Call(self.playerPath.pop))

        # Site
        site = self.map.siteAt(coords) # returns only active sites
        if site is not None:
            site.onEnter(self, self.currentPlayer)
        self.updateActions()
        for site in self.map.adjacentSites(coords):
            site.onAdjacent(self, self.currentPlayer)

        # Marauding enemies
        oldMarauderSites = set(self.map.adjacentMarauderSites(pos))
        newMarauderSites = set(self.map.adjacentMarauderSites(coords))
        provokedMarauderSites = newMarauderSites.intersection(oldMarauderSites)
        provokableMarauderSites = newMarauderSites - provokedMarauderSites
                    
        if len(provokedMarauderSites) > 0:
            enemyCount = 0
            for site in provokedMarauderSites:
                enemyCount += len(site.enemies)

            if enemyCount:
                if not self.state.inCombat:
                    self.combat.init()
                for site in provokedMarauderSites:
                    # these enemies are not provokable, they must be fought
                    self.combat.addEnemies(site)
                    
        provokableEnemies = 0
        for site in provokableMarauderSites:
            provokableEnemies += len(site.enemies)
        if provokableEnemies:
            if not self.state.inCombat:
                self.actions.add('marauding', self.tr("Fight marauding enemies"), self.fightMaraudingEnemies)
            else:
                for site in provokableMarauderSites:
                    self.combat.addEnemies(site, provokable=True)
            
        if self.state is State.initCombat:
            self.combat.start()

    def fightMaraudingEnemies(self):
        coords = self.map.persons[self.currentPlayer]
        marauders = self.map.adjacentMarauderSites(coords)
        self.combat.init()
        for site in marauders:
            self.combat.addEnemies(site, provokable=True)
        self.combat.start()
    
    def updateActions(self):
        self.actions.clear()
        site = self.map.siteAt(self.map.persons[self.currentPlayer]) # TODO: improve this
        if site is not None:
            site.updateActions(self, self.currentPlayer)
        if self.state in [State.movement, State.interaction, State.combatEnd,
                          State.endOfTurn, State.combatRewards]:
            self.actions.add('endturn', self.tr("End turn"), self.endTurn)
        # Explore
        coords = self.map.persons[self.currentPlayer]
        if self.state is State.movement and self.map.canExplore(coords):
            self.actions.add('explore', self.tr("Explore"),
                             functools.partial(self.setState, State.explore))
    
            
    
    def startInteraction(self):
        if self.state is not State.movement:
            raise InvalidAction("Cannot start interaction now.")
        modifier = self.currentPlayer.reputationModifier
        if modifier is REPUTATION_NONE:
            raise InvalidAction("Nobody wants to interact with you!")
        self.setState(State.interaction)
        if modifier != 0:
            self.effects.add(effects.InfluencePoints(modifier))
        
    @action
    def activateUnit(self, player, unit, ability):
        assert isinstance(unit, assets.Unit)
        if not unit.isWounded:
            assert ability in unit.abilities
            self.checkEffectPlayable() # TODO action type
            if not unit.isReady:
                raise InvalidAction("This unit is spent.")
            if ability.cost is not None:
                self.payMana(ability.cost)
            ability.activate(unit, self, player)
            player.units.setIsReady(unit, False)
        else:
            self.payHealPoints(unit.level)
            player.healUnit(unit)
            
    @action(State.interaction)
    def recruitUnit(self, player, unit):
        if self.state is not State.interaction:
            raise InvalidAction("Cannot recruit units outside of interaction.")
        site = self.map.siteAtPlayer(player)
        if site is None or not site.type in unit.sites:
            raise InvalidAction("Cannot recruit unit at this place.")
        self._getUnit(player, unit, reward=False)
        
    def _getUnit(self, player, unit, reward):
        # This helper function is used in recruitUnit (reward=False)
        # and when a player gets a unit as reward (reward=True)
        if player.unitLimit <= len(player.units): # TODO: special case (reward+level-up)
            unitToDisband = dialogs.choose(player.units,
                                           text=self.tr("All slots occupied. Choose a unit to disband."))
            player.units.remove(unitToDisband)
        if not reward:
            self.payInfluencePoints(unit.cost)
        self.shop.units.remove(unit)
        player.units.append(unit)
        
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
        self.actions.activate(self, player, actionId)
        
    @action(State.explore)
    def explore(self, player, coords):
        self.payMovePoints(2)
        self.map.explore(coords)
        self.setState(State.movement)
        
        # Some of the new sites might be adjacent to players (not necessarily to the current player)
        for site in self.map.adjacentSites(coords): # sites on outside fields of new tile
            for player in self.players:
                if site.coords.isNeighborOf(self.map.persons[player]):
                    site.onAdjacent(self, player)

    @action(State.combatRewards)
    def chooseRewardType(self, player, reward):
        self.combat.chooseRewardType(reward)
        
    @action(State.combatRewards)
    def chooseRewardItem(self, player, reward, item):
        self.combat.chooseRewardItem(reward, item)

        
