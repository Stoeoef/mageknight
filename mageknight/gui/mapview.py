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

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from mageknight import hexcoords, utils
from mageknight.match import map, player


class MapView(QtWidgets.QGraphicsView):
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setScene(MapModel(parent, match))
        self.scale(0.5, 0.5)
        self.setBackgroundBrush(Qt.black)
        
    def zoomIn(self):
        self.scale(1.2, 1.2)
        
    def zoomOut(self):
        self.scale(1 / 1.2, 1 / 1.2)
        


class MapModel(QtWidgets.QGraphicsScene):
    def __init__(self, parent, match):
        super().__init__(parent) # parent is necessary or segfaults occur
        self.match = match
        self.map = match.map
        self._enemyItems = {}
        self._personItems = {}
        
        # initialize
        for coords in self.map.enemies.keys():
            self._enemiesChanged(coords)
        for person in self.map.persons.keys():
            self._personChanged(person)
        
        self.map.tileAdded.connect(self._tileAdded)
        self.map.shieldTokenAdded.connect(self._shieldTokenAdded)
        self.map.enemiesChanged.connect(self._enemiesChanged)
        self.map.personChanged.connect(self._personChanged)
        self._addAllTiles()
    
    def _addAllTiles(self):
        """Debug method: Create a map containing all tiles."""
        self.map.addTile(map.Tile('A'), hexcoords.HexCoords(0,0))
        self.map.addTile(map.Tile('1'), hexcoords.HexCoords(1,3))
        self.map.addTile(map.Tile('2'), hexcoords.HexCoords(3,2))
        self.map.addTile(map.Tile('3'), hexcoords.HexCoords(2,6))
        self.map.addTile(map.Tile('4'), hexcoords.HexCoords(4,5))
        self.map.addTile(map.Tile('5'), hexcoords.HexCoords(6,4))
        self.map.addTile(map.Tile('6'), hexcoords.HexCoords(3,9))
        self.map.addTile(map.Tile('7'), hexcoords.HexCoords(5,8))
        self.map.addTile(map.Tile('8'), hexcoords.HexCoords(7,7))
        self.map.addTile(map.Tile('9'), hexcoords.HexCoords(9,6))
        self.map.addTile(map.Tile('10'), hexcoords.HexCoords(4,12))
        self.map.addTile(map.Tile('11'), hexcoords.HexCoords(6,11))
        
        self.map.addTile(map.Tile('c1'), hexcoords.HexCoords(8,10))
        self.map.addTile(map.Tile('c2'), hexcoords.HexCoords(10,9))
        self.map.addTile(map.Tile('c3'), hexcoords.HexCoords(12,8))
        self.map.addTile(map.Tile('c4'), hexcoords.HexCoords(5,15))
        self.map.addTile(map.Tile('c5'), hexcoords.HexCoords(7,14))
        self.map.addTile(map.Tile('c6'), hexcoords.HexCoords(9,13))
        self.map.addTile(map.Tile('c7'), hexcoords.HexCoords(11,12))
        self.map.addTile(map.Tile('c8'), hexcoords.HexCoords(13,11))
        
    def _tileAdded(self, coords):
        tileItem = TileItem(self.map.tiles[coords], coords)
        self.addItem(tileItem)
        
    def _shieldTokenAdded(self, coords):
        player = self.map.shieldTokens[coords]
        pixmap = utils.getPixmap('mk/players/shield_{}.png'.format(player))
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        item.setPos(coords.center())
        # to make sure that the site below remains visible, we do not center the token vertically
        item.setOffset(-pixmap.width()/2, 0)
        self.addItem(item)
    
    def _shiftItemsAt(self, coords):
        """Shift all enemy tokens and persons at the specified hex slightly, so that the user can see that
        there are multiple items at this position.
        """
        items = []
        if coords in self._enemyItems:
            items.extend(self._enemyItems[coords])
        for item in self._personItems.values():
            if item.coords == coords:
                items.append(item)
                
        if len(items) == 1:
            items[0].setZValue(1)
            items[0].setPos(coords.center())
        elif len(items) > 1:
            for i, item in enumerate(items):
                offset = -20 + 40*i/(len(items)-1)
                item.setPos(coords.center() + QtCore.QPointF(offset, 0))
                item.setZValue(i+1)
        
    def _enemiesChanged(self, coords):
        if coords in self._enemyItems:
            for item in self._enemyItems[coords]:
                self.removeItem(item)
        self._enemyItems[coords] = [EnemyItem(enemy, coords) for enemy in self.map.enemies[coords]]
        for item in self._enemyItems[coords]:
            self.addItem(item)
        self._shiftItemsAt(coords)
    
    def _personChanged(self, person):
        if person not in self._personItems: # person added
            coords = self.map.persons[person]
            self._personItems[person] = PersonItem(person, coords)
            self.addItem(self._personItems[person])
            self._shiftItemsAt(coords)
        elif person not in self.map.persons: # person removed
            item = self._personsItem[person]
            self.removeItem(item)
            del self._personItems[person]
            self._shiftItemsAt(item.coords)
        else:
            # person moved
            item = self._personItems[person]
            oldCoords = item.coords
            newCoords = self.map.persons[person]
            item.move(newCoords)
            self._shiftItemsAt(oldCoords)
            self._shiftItemsAt(newCoords)
            
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        coords = hexcoords.HexCoords.fromPixel(event.scenePos())
        self.match.movePlayer(coords)


class TileItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem to display a Mage Knight tile."""
    def __init__(self, tile, coords):
        super().__init__()
        self.tile = tile
        self.coords = coords
        self.setOffset(-3*hexcoords.ALTITUDE, -2.5*hexcoords.SIDE) # position of top left corner
        self.setPixmap(tile.pixmap())
        self.setPos(coords.center())

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        

class EnemyItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem that displays an enemy token. *enemy* may also be an EnemyType in which case the 
    back side of an (unknown) enemy token is displayed."""
    def __init__(self, enemy, coords):
        super().__init__()
        self.enemy = enemy
        pixmap = enemy.pixmap()
        pixmap = pixmap.scaled(pixmap.width()*0.8, pixmap.height()*0.8,
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        self.setOffset(-pixmap.width()/2, -pixmap.height()/2)
        self.setPos(coords.center())


class PersonItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem that displays the mini-figure of a person."""
    def __init__(self, person, coords):
        super().__init__()
        self.person = person
        self.coords = coords
        self.setPixmap(utils.getPixmap('mk/players/{}.png'.format(person.hero.name.lower())))
        if person.hero == player.Hero.Norowas:
            self.setOffset(-73, -180)
        elif person.hero == player.Hero.Arythea:
            self.setOffset(-43, -133)
        elif person.hero == player.Hero.Goldyx:
            self.setOffset(-85, -140)
        elif person.hero == player.Hero.Tovak:
            self.setOffset(-120, -90)
        else:
            assert False
        self.setPos(coords.center())
        
    def move(self, coords):
        """Move the PersonItem to the specified hex."""
        self.coords = coords
        self.setPos(coords.center())
        