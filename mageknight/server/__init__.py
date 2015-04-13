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

from mageknight import stack, hexcoords
from mageknight.matchdata import *
from .objects import ManaSource, Player
from .map import Map


# use this to wrap player actions
# TODO: Check for current player
def action(f):
    def wrap(self, *args, **kwargs):
        self.stack.beginMacro()
        try:
            f(self, *args, **kwargs)
            self.stack.endMacro()
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
        self.source = ManaSource(len(self.players)+2)
        self.map = map.Map(MapShape.wedge)
        self.effects = effects.EffectList()
        
        for player in self.players:
            self.map.addPerson(player, hexcoords.HexCoords(0, 0))
            player.initDeedDeck()
            player.drawCards()
        self.currentPlayer = self.players[0]
        
    def terrainIsPassable(self, terrain):
        """Return whether the given terrain is currently passable for the current player. This might change
        as an effect of e.g. spells."""
        assert isinstance(terrain, map.Terrain)
        return terrain not in (map.Terrain.lake, map.Terrain.mountain)
    
    def getTerrainCost(self, terrain):
        """Return the current cost of the given terrain."""
        costs = {
            map.Terrain.plains: 2,
            map.Terrain.hills: 3,
            map.Terrain.forest: 3 if self.round.type == RoundType.day else 5,
            map.Terrain.wasteland: 4,
            map.Terrain.desert: 5 if self.round.type == RoundType.day else 3,
            map.Terrain.swamp: 5,
            map.Terrain.city: 2,
        }
        if terrain not in costs:
            raise ValueError("Terrain {} is not passable".format(terrain.name))
        return costs[terrain]
    
    def _payMana(self, color):
        """Pay a mana of the given color and return whether this was possible. First try mana tokens, then
        gold mana (only during days), finally try to use a crystal.
        """
        if self.effects.remove(effects.ManaTokens(color)):
            return True
        if color.isBasic and self.round.type == RoundType.day \
            and self.effects.remove(effects.ManaTokens(Mana.gold)):
            return True
        if self.currentPlayer.crystals[color] > 0:
            self.currentPlayer.removeCrystal(color)
            return True
        else:
            return False

    @action
    def playCard(self, player, card, effectNumber):
        if isinstance(card, cards.ActionCard):
            if effectNumber == 0:
                card.basicEffect(self, player)
            elif effectNumber == 1:
                if self._payMana(card.color):
                    card.strongEffect(self, player)
                else: raise InvalidAction("Cannot pay mana cost")
            else: raise ValueError("Invalid effect number for card '{}': {}".format(card.name, effectNumber))
            # TODO: remove card
        
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
        if not self.effects.remove(effects.MovePoints(self.getTerrainCost(terrain))):
            raise InvalidAction("Not enough move points")
        self.map.movePerson(player, coords)
            
    @action
    def chooseSourceDie(self, player, index):
        if len(self.source) < self.source.count:
            raise InvalidAction("You cannot take more than one die") # TODO: improve this check
        color = self.source[index]
        if self.round.type == RoundType.day and color == Mana.black:
            raise InvalidAction("You must not use black mana during day rounds.")
        if self.round.type == RoundType.night and color == Mana.gold:
            raise InvalidAction("You must not use gold mana during night rounds.")
        self.stack.push(stack.Call(self.source.remove, index),
                        stack.Call(self.source.insert, index, color))
        self.stack.push(stack.Call(self.effects.add, effects.ManaTokens(color)),
                        stack.Call(self.effects.remove, effects.ManaTokens(color)))
        