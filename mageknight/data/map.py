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

from mageknight import hexcoords, utils
from .core import Mana

__all__ = ['MapShape', 'Terrain', 'Site', 'Tile']


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
    
    # Map tile id to list of sites (or 0). List begins in the center, then top right, then clockwise.
    # Each entry can be either 0, or a Site, or a tuple (Site, data, ...).
    # The dict will be processed below, never use it directly.
    # Use siteAt and siteDataAt instead.
    _sites = {
          'A':  [Site.portal, 0, 0, 0, 0, 0, 0],
          'B':  [Site.portal, 0, 0, 0, 0, 0, 0],
          '1':  [Site.magicalGlade, 0, Site.village, 0, 0, 0, Site.maraudingOrcs],
          '2':  [0, Site.magicalGlade, Site.village, 0, (Site.crystalMines, Mana.green), 0, Site.maraudingOrcs],
          '3':  [0, Site.keep, 0, (Site.crystalMines, Mana.white), Site.village, 0, 0, 0],
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
    _siteData = {key: [] for key in _sites.keys()}
    
    # Process _sites, _siteData:
    # store data part of tuples in _siteData (or None)
    _siteData = {key: [site[1:] if isinstance(site, tuple) else None for site in sites]
                  for key, sites in _sites.items()}
    # remove second part of tuples from _sites
    _sites = {key: [site[0] if isinstance(site, tuple) else site for site in sites]
              for key, sites in _sites.items()}
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
        else: return 1 + hexcoords.HexCoords(0, 0).neighbors().index(coords)
    
    def terrainAt(self, coords):
        """Return the terrain at the given coords, assuming this tile sits at (0,0)."""
        terrains = self._terrains[self.id]
        return terrains[self._fieldIndex(coords)]
    
    def siteAt(self, coords):
        """Return the site at the given coords, assuming this tile sits at (0,0)."""
        sites = self._sites[self.id]
        return sites[self._fieldIndex(coords)]
    
    def siteDataAt(self, coords):
        """Return site data (e.g. crystal mine color) at the given coords, assuming this tile sits at (0,0).
        """
        siteData = self._siteData[self.id]
        return siteData[self._fieldIndex(coords)]
    
    def allSites(self):
        """Return a list of tuples (coords, site) for all sites on this tile."""
        sites = []
        for coords in hexcoords.HexCoords(0, 0).neighbors():
            site = self.siteAt(coords)
            if site is not Site.none:
                sites.append((coords, site, self.siteDataAt(coords)))
        return sites
        