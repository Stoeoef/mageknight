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

from mageknight import stack
from mageknight.hexcoords import HexCoords
from mageknight.data import * # @UnusedWildImport
from . import player
    
    
class Map(QtCore.QObject):
    """Model for the map of a Mage Knight match.
    Public (read-only) attributes are:
        
        - shape: the MapShape specified in the constructor.
        - tiles: dict mapping HexCoords to Tiles. The coordinates always refer to the center hex of the tile.
        - shieldTokens: dict mapping HexCoords to a Player whose shield token is at this positionj
        - enemies: dict mapping HexCoords to a list of enemies at this position.
        - persons: dict mapping Persons to HexCoords (the mapping direction is swapped, because persons
                   typically move on the map) 
    
    """
    tileAdded = QtCore.pyqtSignal(HexCoords)
    shieldTokenAdded = QtCore.pyqtSignal(HexCoords)
    enemiesChanged = QtCore.pyqtSignal(HexCoords)
    personChanged = QtCore.pyqtSignal(player.Player)
    
    def __init__(self, match, shape):
        super().__init__()
        self.match = match
        assert isinstance(shape, MapShape)
        self.shape = shape
        self.tiles = {}
        self.shieldTokens = {}
        self.enemies = {}
        self.persons = {}

    def addTile(self, tile, coords):
        """Add a tile at the given hex coordinates. *coords* must point to an empty center hex
        (see isTileCenter).
        """
        assert isTileCenter(coords)
        assert coords not in self.tiles
        self.tiles[coords] = tile
        self.tileAdded.emit(coords)
        
    def tileAt(self, coords):
        """Return the tile at the given hex (contrary to self.tiles[coords] this works even if *coords* does
        not point to the center of the tile)."""
        return self.tiles.get(tileCenter(coords))
        
    def terrainAt(self, coords):
        """Return the terrain of the given hex. Returns None if there is no tile at this position."""
        tile = self.tileAt(coords)
        if tile is not None:
            return tile.terrainAt(coords-tileCenter(coords))
        else: return None
        
    def siteAt(self, coords):
        """Return the site on the given hex. Returns None if there is no tile at this position."""
        tile = self.tileAt(coords)
        if tile is not None:
            return tile.siteAt(coords-tileCenter(coords))
        else: return None
        
    def _addShieldToken(self, player, coords):
        """Add a shield token of the given player to the specified hex. The hex must be empty."""
        assert coords not in self.shieldTokens
        self.shieldTokens[coords] = player
        self.shieldTokenAdded.emit(coords)
        
    def _addEnemy(self, enemy, coords):
        """Add an enemy to the specified hex field. Each hex can contain arbitrary many enemies."""
        if coords not in self.enemies:
            self.enemies[coords] = []
        self.enemies[coords].append(enemy)
        self.enemiesChanged.emit(coords)
        
    def _removeEnemy(self, enemy, coords):
        """Remove the given enemy from the specified hex."""
        try:
            self.enemies[coords].remove(enemy)
        except (KeyError, ValueError):
            raise ValueError("There is no enemy {} at {}.".format(enemy, coords))
        self.enemiesChanged.emit(coords)
    
    def addPerson(self, person, coords):
        assert person not in self.persons
        self.match.stack.push(stack.Call(self._addPerson, person, coords),
                              stack.Call(self._removePerson, person))
        
    def removePerson(self, person):
        assert person in self.persons
        self.match.stack.push(stack.Call(self._removePerson, person),
                              stack.Call(self._addPerson, person, self.persons[person]))
        
    def _addPerson(self, person, coords):
        """Add the given person to the specified hex."""
        assert person not in self.persons
        self.persons[person] = coords
        self.personChanged.emit(person)
    
    def _removePerson(self, person):
        """Remove the given person from the map."""
        del self.persons[person]
        self.personChanged.emit(person)
    
    def movePerson(self, person, coords):
        assert person in self.persons
        self.match.stack.push(stack.Call(self._movePerson, person, coords),
                              stack.Call(self._movePerson, person, self.persons[person]))
        
    def _movePerson(self, person, coords):
        """Move the given person to the specified hex."""
        self.persons[person] = coords
        self.personChanged.emit(person)


def isTileCenter(coords):
    """Return whether *coords* are the coordinates of the center hex of a tile."""
    # tile centers are coordinates of the form n * (2,-1) + m * (1,3) with n,m ∈ ℕ
    # a little calculation leads to these conditions
    return (3*coords.x - coords.y) % 7 == 0 and (coords.x + 2*coords.y) % 7 == 0


def tileCenter(coords):
    """Get the coordinates of the center of the tile at the given coordinates."""
    if isTileCenter(coords):
        return coords
    else:
        for n in coords.neighbors():
            if isTileCenter(n):
                return n
    assert False
    