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

import random

from mageknight import hexcoords
from mageknight.data import *  # @UnusedWildImport
from . import basemap, sites
from .effects import TerrainCostsOverwrite


class Map(basemap.Map):
    """Model for the map of a Mage Knight match.
    Public (read-only) attributes are:
        
        - shape: the MapShape specified in the constructor.
        - tiles: dict mapping HexCoords to Tiles. The coordinates always refer to the center hex of the tile.
        - shieldTokens: dict mapping HexCoords to a Player whose shield token is at this positionj
        - enemies: dict mapping HexCoords to a list of enemies at this position.
        - persons: dict mapping Persons to HexCoords (the mapping direction is swapped, because persons
                   typically move on the map) 
    
    """
    def __init__(self, match, shape):
        super().__init__(match, shape)
        self.tilePile = []
    
    @staticmethod
    def create(match, shape):
        map = Map(match, shape)
        map.tilePile = TilePile(7, 2, 2)
        if shape is MapShape.wedge:
            map.addTile(Tile('A'), hexcoords.HexCoords(0,0))

            map.addTile(map.tilePile.pop(), hexcoords.HexCoords(1,3))
            map.addTile(map.tilePile.pop(), hexcoords.HexCoords(3,2))
            # map.addTile(Tile('7'), hexcoords.HexCoords(1,3))
            # map.addTile(Tile('6'), hexcoords.HexCoords(3,2))

        else:
            raise NotImplementedError()
        return map
        
    def addTile(self, tile, coords):
        """Add the tile and put enemy tokens on top of it."""
        super().addTile(tile, coords)
        for c, site, data in tile.allSites():
            site = sites.create(site, self.match, coords + c, data)
            if site is not None: # TODO: remove debugging code
                self._addSite(site)
    
    def modifiedTerrainCosts(self, terrain):
        overwrite = self.match.effects.find(TerrainCostsOverwrite)
        if overwrite != None:
            return overwrite.terrainCosts(terrain, self.baseTerrainCosts(terrain))
        return self.baseTerrainCosts(terrain)

    def baseTerrainCosts(self, terrain):
        return {
            Terrain.plains: 2,
            Terrain.hills: 3,
            Terrain.forest: 3 if self.match.round.type == RoundType.day else 5,
            Terrain.wasteland: 4,
            Terrain.desert: 5 if self.match.round.type == RoundType.day else 3,
            Terrain.swamp: 5,
            Terrain.city: 2,
        }.get(terrain)

      
    def isTerrainPassable(self, terrain):
        """Return whether the given terrain is currently passable for the current player. This might change
        as an effect of e.g. spells."""
        assert isinstance(terrain, Terrain)
        return self.modifiedTerrainCosts(terrain) != None
    
    def isSafeSpace(self, coords, player):
        """Return whether a space is considered to be a "safe space". Players must end their turn on a
        safe space."""
        terrain = self.terrainAt(coords)
        print("terrain: ", terrain)
        if terrain in [Terrain.lake, Terrain.mountain]:
            return False
        site = self.siteAt(coords)
        if site is not None:
            if isinstance(site, sites.FortifiedSite):
                print("owner: ", site.owner)
                if site.owner is None or (isinstance(site, Keep) and site.owner != player):
                    return False
        for otherPlayer in self.match.players:
            if otherPlayer != player and self.persons[otherPlayer] == coords:
                if site not in [Site.portal, Site.city]:
                    return False
        return True

    def reduceTerrainCost(self, terrain, amount, minimum):
        """Reduce cost of *terrain* by *amount*, to a minimum of *minimum*."""
        self.match.effects.add(TerrainCostsOverwrite.reduceCosts(terrain, amount, minimum))

    def overwriteTerrainCost(self, terrain, value):
        self.match.effects.add(TerrainCostsOverwrite.overwriteBaseCosts(terrain, value))

    def revealEnemies(self, site):
        self.match.revealNewInformation()
        # note: one of the following two lists should be empty. Thus no problems with changing the order
        enemies = [e for e in site.enemies if not isinstance(e, UnknownEnemy)]
        unknownEnemies = [e.category for e in site.enemies if isinstance(e, UnknownEnemy)]
        enemies.extend(self.match.chooseEnemies(unknownEnemies))
        self._setEnemies(site, enemies)
        
    def adjacentMarauderSites(self, coords):
        return [site for site in self.adjacentSites(coords)
                if site.type in [Site.maraudingOrcs, Site.draconum]]
    
    def getTileNeighbors(self, coords):
        neighbors = []
        for t in [(3, 2), (2, -1), (-1, -3), (-3, -2), (-2, 1), (1, 3)]:
            nCoords = coords + hexcoords.HexCoords(*t)
            if self.terrainAt(nCoords) is not None:
                neighbors.append(nCoords)
        return neighbors    
        
    def isTileInWedge(self, coords):
        """Return whether the given hex, which must be a tile center, is within the "wedge" shape of a map.
        """
        # The tile centers at the coast have coordinates of the form m*(1,3) and n*(3,2) with m,n ∈ ℕ.
        # All tiles in between are positive linear combinations.
        # See also basemap.isTileCenter
        m = (3*coords.y - 2*coords.x) // 7 
        n = (coords.x-m) // 3
        return m >= 0 and n >= 0
        
    def getExplorableTiles(self, coords):
        if self.tilePile.state is TilePileState.empty:
            return []
        emptyNeighbors = [n for n in coords.neighbors() if self.terrainAt(n) is None]
        tiles = list(set([basemap.tileCenter(n) for n in emptyNeighbors]))
        if self.shape is MapShape.wedge:
            tiles = [t for t in  tiles if self.isTileInWedge(t)]
        else: raise NotImplementedError()
        
        for tile in list(tiles):
            neighbors = self.getTileNeighbors(tile)
            assert len(neighbors) >= 1
            if self.tilePile.state is TilePileState.countrySide:
                # Rules: countryside tiles must be placed adjacent to two tiles or to a tile that is
                # adjacent to two tiles.
                if len(neighbors) == 1 and len(self.getTileNeighbors(neighbors[0])) <= 1:
                    tiles.remove(tile)
                    
            elif self.tilePile.state is TilePileState.core:
                # Rules: core tiles must be placed adjacent to two tiles
                if len(neighbors) == 1:
                    tiles.remove(tile)
                    
            else:
                # Rules: rest tiles must be placed adjacent to three tiles
                if len(neighbors) <= 2:
                    tiles.remove(tile)
            
        return tiles
        
    def canExplore(self, coords):
        return len(self.getExplorableTiles(coords)) > 0
    
    def explore(self, coords):
        coords = basemap.tileCenter(coords)
        if coords not in self.getExplorableTiles(self.persons[self.match.currentPlayer]):
            raise InvalidAction("Cannot explore")
        tile = self.tilePile.pop()
        self.addTile(tile, coords)
        
        
class TilePile(QtCore.QObject):
    tileCountChanged = QtCore.pyqtSignal(int, int, int)
    
    def __init__(self, countrySides, nonCities, cities):
        super().__init__()
        self._pile = []
        
        # Countryside tiles
        tiles = Tile.allTiles(TileType.countrySide)
        self._pile.extend(random.sample(tiles, countrySides))
        
        # Core tiles
        coreTiles = []
        tiles = Tile.allTiles(TileType.core)
        coreTiles.extend(random.sample(tiles, nonCities))
        tiles = Tile.allTiles(TileType.city)
        coreTiles.extend(random.sample(tiles, cities))
        random.shuffle(coreTiles)
        self._pile.extend(coreTiles)
        
        # Remaining countryside tiles
        restTiles = [t for t in Tile.allTiles(TileType.countrySide) if t not in self._pile]
        restTiles.extend(t for t in Tile.allTiles(TileType.core) if t not in self._pile)
        random.shuffle(restTiles)
        self._pile.extend(restTiles)
        
        self.counts = [countrySides, nonCities+cities, len(restTiles)]
        
    def pop(self):
        tile = self._pile.pop(0)
        self.tileCountChanged.emit(*self.counts)
        return tile
        
    @property
    def state(self):
        c = len(self._pile)
        if c == 0:
            return TilePileState.empty
        elif c <= self.counts[2]: # rest tiles
            return TilePileState.rest
        elif c <= self.counts[2] + self.counts[1]: # rest/core
            return TilePileState.core
        else:
            return TilePileState.countrySide
