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
from mageknight.core import source, player, map, effectlist, effects, cards, units, shop, combat # @Reimport
from mageknight.gui import dialogs


# use this to wrap player actions
# TODO: Check for current player
def action(f):
    def wrap(self, *args, **kwargs):
        self.stack.beginMacro()
        try:
            f(self, *args, **kwargs)
            self.stack.endMacro(abortIfEmpty=True) # the macro is often empty, when new info was revealed
        except CancelAction: # action was aborted e.g. by canceling a dialog
            self.stack.abortMacro()
        except InvalidAction as e:
            print(e)
            self.stack.abortMacro()
    return wrap


class Match(QtCore.QObject):
    """This is the central object managing a match."""
    roundChanged = QtCore.pyqtSignal(Round)
    
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
        self.combat = combat.Combat(self)
        
        for player in self.players:
            player.match = self
            self.map.addPerson(player, hexcoords.HexCoords(0, 0))
            player.initDeedDeck()
            player.drawCards()
        self.currentPlayer = self.players[0]
                
    def revealNewInformation(self):
        """Call this whenever new information is revealed. It will clear the undo stack."""
        if self.stack.isComposing():
            self.stack.endMacro()
            self.stack.clear()
            self.stack.beginMacro()
        else:
            self.stack.clear()
        
    def nightRulesApply(self):
        """Return whether night rules hold currently. This is true during nights, in dungeons, etc."""
        return self.round.type == RoundType.night
        
    def terrainIsPassable(self, terrain):
        """Return whether the given terrain is currently passable for the current player. This might change
        as an effect of e.g. spells."""
        assert isinstance(terrain, Terrain)
        return terrain not in (Terrain.lake, Terrain.mountain)
    
    def getTerrainCost(self, terrain):
        """Return the current cost of the given terrain."""
        costs = {
            Terrain.plains: 2,
            Terrain.hills: 3,
            Terrain.forest: 3 if self.round.type == RoundType.day else 5,
            Terrain.wasteland: 4,
            Terrain.desert: 5 if self.round.type == RoundType.day else 3,
            Terrain.swamp: 5,
            Terrain.city: 2,
        }
        if terrain not in costs:
            raise ValueError("Terrain {} is not passable".format(terrain.name))
        return costs[terrain]
    
    def _manaOptions(self, player, colors):
        if isinstance(colors, Mana):
            colors = [colors]
        colors = [c for c in Mana if c in colors] # copy and sort
        if not self.nightRulesApply():
            assert Mana.black not in colors
            if Mana.gold not in colors:
                colors.append(Mana.gold)
        else:
            assert Mana.gold not in colors
        
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
        
    def payMana(self, colors):
        """Pay a mana in one of the given colors (*colors* may be a single color or a list of colors).
        Raise an InvalidAction if that is not possible. Return the chosen color.
        """
        options = self._manaOptions(self.currentPlayer, colors)
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
        return color
    
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
        self.combat.checkEffectPlayable()
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
        self.combat.checkEffectPlayable()
        effect = self.sidewaysEffects()[effectIndex]
        #player.discard(card) # TODO: disabled to make debugging life easier
        self.effects.add(effect)
        
    @action
    def movePlayer(self, player, coords):
        """Move the given player to the specified hex. Use this method only for standard moves in the
        movement phase, not for Flight, Underground Travel and similar special effects. The player's
        move points will be reduced appropriately.
        """
        if not self.state == State.movement:
            raise InvalidAction("Can only move during movement phase.")
        pos = self.map.persons[player]
        if pos == coords:
            return
        if not coords.isNeighborOf(pos):
            raise InvalidAction("Can only move to adjacent fields.")
        terrain = self.map.terrainAt(coords)
        if terrain is None or not self.terrainIsPassable(terrain):
            raise InvalidAction("This field is not passable")
        self.payMovePoints(self.getTerrainCost(terrain))
        self.map.movePerson(player, coords)
        
    @action
    def activateUnit(self, player, unit, action):
        assert isinstance(unit, units.Unit)
        assert action in unit.actions
        self.combat.checkEffectPlayable()
        if not unit.isReady:
            raise InvalidAction("This unit is spent.")
        if unit.isWounded:
            raise InvalidAction("This unit is wounded.")
        if action.cost is not None:
            self.payMana(action.cost)
        unit.activate(action, self, player)
        player.spendUnit(unit)
        
    @action
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
        
    @action
    def setEnemySelected(self, player, enemy, selected):
        self.combat.setEnemySelected(enemy, selected)
    
    @action
    def combatNext(self, player):
        self.combat.next()
        
    @action
    def combatSkip(self, player):
        self.combat.skip()
    
    @action
    def assignDamageToUnit(self, player, unit):
        self.combat.assignDamageToUnit(unit)
    
    
        
        