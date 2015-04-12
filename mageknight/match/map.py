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

from mageknight import utils
from mageknight.match import player 
from mageknight.hexcoords import HexCoords


class MapShape(enum.Enum):
    """The shape of the map as specified in the rule book.""" 
    wedge = 1
    columns3 = 2 # 3 columns
    columns4 = 3 # 4 columns, extending more to the right
    columns5 = 4 # called "Fully open" in rule book


class Terrain(enum.Enum):
    """The terrain of one hex field."""
    plains = 1
    hills = 2
    forest = 3
    wasteland = 4
    desert = 5
    swamp = 6
    lake = 7 # also used for the sea on the start tile
    mountain = 8
    city = 9
    
    @staticmethod
    def fromChar(char):
        """Return a terrain from its initial letter."""
        return Terrain(1 + 'phfwdslmc'.index(char))
    
    
class Site(enum.Enum):
    """The site on a hex field. Site.none indicates an empty hex."""
    none = 0
    portal = 1
    crystalMines = 2 # TODO: color?
    magicalGlade = 3
    maraudingOrcs = 4
    draconum = 5
    village = 6
    monastery = 7
    mageTower = 8
    keep = 9
    monsterDen = 10
    spawningGrounds = 11
    dungeon = 12
    tomb = 13
    ancientRuins = 14
    city = 15 # TODO: color?
    
    
class Tile:
    """One of the tiles shipped with Mage Knight. Tiles are identified by an id: 'A' or 'B' for the start
    tiles, '1' etc. for countryside tiles and 'c1' etc. for core tiles, including cities.
    """
    # terrains of the tiles. Start at the center, then list the neighbors beginning with top-right and
    # continuing in clockwise order.
    _terrains = {
         'A':  'pfplllp',
         'B':  'pfppllp',
         '1':  'flpppff', 
         '2':  'hfpphph',
         '3':  'fhhhppp',
         '4':  'ddmpphd',
         '5':  'lpphfff',
         '6':  'hfpfhhm',
         '7':  'sffpppl',
         '8':  'sfpssff',
         '9':  'mmwpwpw',
         '10': 'mfphhhh',
         '11': 'pllhlph',
         'c1': 'ddddhhm',
         'c2': 'lshssfl',
         'c3': 'wwhwhwm',
         'c4': 'mhwwwwh',
         'c5': 'csssflf',
         'c6': 'cpllhmf',
         'c7': 'cpfllww',
         'c8': 'chddwwd',
    }
    # Convert strings to list of Terrains
    _terrains = {key: [Terrain.fromChar(c) for c in string] for key, string in _terrains.items()}
    
    _sites = {
          'A':  [Site.portal, 0, 0, 0, 0, 0, 0],
          'B':  [Site.portal, 0, 0, 0, 0, 0, 0],
          '1':  [Site.magicalGlade, 0, Site.village, 0, 0, 0, Site.maraudingOrcs],
          '2':  [0, Site.magicalGlade, Site.village, 0, Site.crystalMines, 0, Site.maraudingOrcs],
          '3':  [0, Site.keep, 0, Site.crystalMines, Site.village, 0, 0, 0],
          '4':  [Site.mageTower, 0, 0, Site.village, 0, Site.maraudingOrcs, 0],
          '5':  [0, Site.monastery, Site.maraudingOrcs, Site.crystalMines, 0, Site.magicalGlade, 0],
          '6':  [Site.crystalMines, 0, 0, Site.maraudingOrcs, 0, Site.monsterDen, 0],
          '7':  [0, Site.maraudingOrcs, Site.magicalGlade, Site.dungeon, 0, Site.monastery, 0],
          '8':  [Site.maraudingOrcs, Site.ancientRuins, 0, Site.village, 0, 0, Site.magicalGlade],
          '9':  [0, 0, Site.keep, 0, Site.mageTower, 0, Site.dungeon],
          '10': [0, 0, 0, Site.ancientRuins, Site.keep, 0, Site.monsterDen],
          '11': [Site.mageTower, 0, 0, Site.maraudingOrcs, 0, Site.ancientRuins, 0],
          'c1': [Site.monastery, Site.tomb, 0, 0, 0, Site.spawningGrounds, 0],
          'c2': [0, Site.ancientRuins, Site.crystalMines, Site.draconum, Site.mageTower, 0, 0],
          'c3': [0, Site.ancientRuins, Site.mageTower, 0, Site.crystalMines, Site.tomb, 0],
          'c4': [Site.draconum, 0, Site.keep, 0, Site.ancientRuins, 0, Site.crystalMines],
          'c5': [Site.city, Site.village, Site.maraudingOrcs, 0, Site.maraudingOrcs, 0, Site.magicalGlade],
          'c6': [Site.city, Site.monastery, 0, 0, 0, Site.draconum, 0],
          'c7': [Site.city, 0, 0, Site.draconum, 0, Site.keep, Site.spawningGrounds],
          'c8': [Site.city, Site.crystalMines, 0, Site.draconum, 0, Site.draconum, Site.ancientRuins],
    }
    
    # Convert 0 to Site.none
    _sites = {key: [Site.none if s == 0 else s for s in values] for key, values in _sites.items()}
    
    def __init__(self, id, orientation=0):
        assert id in self._terrains
        self.id = id
        self.orientation = orientation # TODO: Implement rotated tiles
        
    def pixmap(self):
        """Return the pixmap of this tile."""
        return utils.getPixmap('mk/tiles/tile-{}.png'.format(self.id))
        
    def _fieldIndex(self, coords):
        """Return the position of the hex *coords* within its tile: 0 indicates the center, 1-6 are the 
        neighbors, starting with the top-right one and continuing in clockwise order."""
        if coords.x == 0 and coords.y == 0:
            return 0
        else: return 1 + HexCoords(0, 0).neighbors().index(coords)
    
    def terrainAt(self, coords):
        """Return the terrain at the given coords, assuming this tile sits at (0,0)."""
        terrains = self._terrains[self.id]
        return terrains[self._fieldIndex(coords)]
    
    def siteAt(self, coords):
        """Return the site at the given coords, assuming this tile sits at (0,0)."""
        sites = self._sites[self.id]
        return sites[self._fieldIndex(coords)]
        
        
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
    
    def __init__(self, shape):
        super().__init__()
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
        
    def addShieldToken(self, player, coords):
        """Add a shield token of the given player to the specifiey hex. The hex must be empty."""
        assert coords not in self.shieldTokens
        self.shieldTokens[coords] = player
        self.shieldTokenAdded.emit(coords)
        
    def addEnemy(self, enemy, coords):
        """Add an enemy to the specified hex field. Each hex can contain arbitrary many enemies."""
        if coords not in self.enemies:
            self.enemies[coords] = []
        self.enemies[coords].append(enemy)
        self.enemiesChanged.emit(coords)
        
    def removeEnemy(self, enemy, coords):
        """Remove the given enemy from the specified hex."""
        try:
            self.enemies[coords].remove(enemy)
        except (KeyError, ValueError):
            raise ValueError("There is no enemy {} at {}.".format(enemy, coords))
        self.enemiesChanged.emit(coords)
        
    def addPerson(self, person, coords):
        """Add the given person to the specified hex."""
        assert person not in self.persons
        self.persons[person] = coords
        self.personChanged.emit(person)
    
    def removePerson(self, person):
        """Remove the given person from the map."""
        del self.persons[person]
        self.personChanged.emit(person)
        
    def movePerson(self, person, coords):
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
    