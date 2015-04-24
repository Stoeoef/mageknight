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

from mageknight import hexcoords
from mageknight.data import *  # @UnusedWildImport
from . import basemap


class SiteOnMap:
    def __init__(self, site, coords):
        self.type = site
        self.coords = coords
        self.isActive = True
        self.enemies = []
        self.owner = None
        
    def __getattr__(self, attr):
        return getattr(self.site, attr)
    

class Map(basemap.Map):
    def __init__(self, match, shape):
        super().__init__(match, shape)
        
        self.addTile(Tile('A'), hexcoords.HexCoords(0,0))
        self.addTile(Tile('1'), hexcoords.HexCoords(1,3))
        self.addTile(Tile('2'), hexcoords.HexCoords(3,2))
        
    def addTile(self, tile, coords):
        """Add the tile and put enemy tokens on top of it."""
        super().addTile(tile, coords)
        for c, site in tile.allSites():
            site = SiteOnMap(site, coords + c)
            if site.type is Site.maraudingOrcs:
                enemy = self.match.chooseEnemy(EnemyCategory.maraudingOrcs)
                site.enemies.append(enemy)
            
            self.addSite(site)

    def getAdjacentMaraudingEnemies(self, coords):
        return [site for site in self.adjacentSites(coords)
                if site.type in [Site.maraudingOrcs, Site.draconum]]
        