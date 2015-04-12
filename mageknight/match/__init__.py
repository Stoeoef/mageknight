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

import enum

from PyQt5 import QtCore

from mageknight import stack, hexcoords
from mageknight.match import player, map, enemies
from mageknight.match.data import RoundType, Round, Mana, InvalidAction
from mageknight.match.adapter import MatchAdapter


class State(enum.Enum):
    # TODO: more states are necessary for e.g. pillaging, resting, level-up...
    init = 1
    movement = 2
    action = 3


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
        self.map = map.Map(map.MapShape.wedge)
        for player in self.players:
            self.map.addPerson(player, hexcoords.HexCoords(0, 0))
    
    def movePlayer(self, player, coords):
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
        self.map.movePerson(player, coords)
        
    def terrainIsPassable(self, terrain):
        """Return whether the given terrain is currently passable for the current player. This might change
        as an effect of e.g. spells."""
        assert isinstance(terrain, map.Terrain)
        return terrain not in (map.Terrain.lake, map.Terrain.mountain)
        
        
class ManaSource(QtCore.QObject):
    """The mana source contains the mana dice available to all players. It behaves like a read-only list, so 
    e.g. 'len(source)' and 'source[2]' work as expected. The additional attribute 'count' stores the initial
    number of dice in the source (typically number of players + 2). The number returned by len(source) can
    be lower due to e.g. Mana Steal.
    """ 
    changed = QtCore.pyqtSignal()
    
    def __init__(self, count):
        super().__init__()
        self.count = count
        self._dice = None
        self.shuffle()
    
    # Methods required for a read-only list
    def __len__(self, index):
        return len(self._dice)
    
    def __getitem__(self, index):
        return self._dice(index)
    
    def __contains__(self, object):
        return object in self._dice
    
    def __iter__(self):
        return iter(self._dice)
    
    def isValidAtRoundStart(self):
        """Return whether at least half of the dice show a basic colors (as required by the rules at round
        start)."""
        return sum(1 if die.basic else 0 for die in self._dice) >= self.count / 2
        
    def shuffle(self):
        """Shuffle all dice in the source according to the rules."""
        while True:
            self._dice = [Mana.random() for _ in range(self.count)]
            if self.isValidAtRoundStart():
                break
        self.changed.emit()