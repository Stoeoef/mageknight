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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from mageknight import map, hexcoords, utils, enemies


class MapView(QtWidgets.QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setScene(MapModel(parent))
        self.scale(0.5, 0.5)
        self.setBackgroundBrush(Qt.black)
        
    def zoomIn(self):
        self.scale(1.2, 1.2)
        
    def zoomOut(self):
        self.scale(1 / 1.2, 1 / 1.2)
        


class MapModel(QtWidgets.QGraphicsScene):
    def __init__(self, parent): # parent is necessary or segfaults occur
        super().__init__(parent)
        self.map = map.Map(map.MapShape.wedge)
        self._enemyItems = {}
        self._personItems = {}
        self.map.tileAdded.connect(self._tileAdded)
        self.map.shieldTokenAdded.connect(self._shieldTokenAdded)
        self.map.enemiesChanged.connect(self._enemiesChanged)
        self.map.personChanged.connect(self._personChanged)
        self._addAllTiles()
        
        # Debug: Create some stuff
        self.map.addShieldToken('arythea', hexcoords.HexCoords(1,3))
        self.map.addEnemy(enemies.Enemy(enemies.EnemyType['city'], 'altem_mages'), hexcoords.HexCoords(1,1))
        self.map.addPerson('norowas', hexcoords.HexCoords(0,2))
        self.map.addPerson('arythea', hexcoords.HexCoords(1,2))
        self.map.addPerson('goldyx', hexcoords.HexCoords(2,2))
        self.map.addPerson('tovak', hexcoords.HexCoords(3,2))
    
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
        
    def _enemiesChanged(self, coords):
        if coords in self._enemyItems:
            for item in self._enemyItems[coords]:
                self.removeItem(item)
        self._enemyItems[coords] = []
            
        enemies = self.map.enemies[coords]
        pixmaps = [e.pixmap() for e in enemies]
        for pixmap in pixmaps:
            pixmap = pixmap.scaled(pixmap.width()*0.8, pixmap.height()*0.8,
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item = QtWidgets.QGraphicsPixmapItem(pixmap)
            item.setPos(coords.center())
            item.setOffset(-pixmap.width()/2, -pixmap.height()/2)
            self.addItem(item)
            self._enemyItems[coords].append(item)
    
    def _personChanged(self, person):
        if person not in self._personItems:
            self._personItems[person] = PersonItem(person, self.map.persons[person])
            self.addItem(self._personItems[person])
        elif person not in self.map.persons:
            self.removeItem(self._personItems[person])
            del self._personItems[person]
        else:
            self._personItems[person].setPos(self.map.persons[person].center())
        
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        print(hexcoords.HexCoords.fromPixel(event.scenePos()))


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
        
        # Debugging code
        painter.save()
        pen = QtGui.QPen(Qt.magenta)
        pen.setWidth(7)
        painter.setPen(pen)
        font = painter.font()
        font.setPointSize(20)
        painter.setFont(font)
        #self._drawBorder(painter, self.coords)
        self._drawText(painter, self.coords)
        for n in self.coords.neighbors():
            self._drawText(painter, n)
        painter.restore()

    # debug methods
    def _drawBorder(self, painter, coords):
        corners = hexcoords.HexCoords(0,0).corners()
        lastCorner = corners[-1]
        for corner in corners:
            painter.drawLine(lastCorner, corner)
            lastCorner = corner
            
    def _drawText(self, painter, coords):
        terrain = self.scene().map.terrainAt(coords)
        site = self.scene().map.siteAt(coords)
        center = coords.center()-self.coords.center()
        painter.drawText(center, terrain.name)
        if site != map.Site.none:
            painter.drawText(center+QtCore.QPointF(0, painter.fontMetrics().height()), site.name)
        

class PersonItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem that displays the mini-figure of a person."""
    def __init__(self, person, coords):
        super().__init__()
        self.person = person
        self.setPixmap(utils.getPixmap('mk/players/{}.png'.format(person)))
        if person == 'norowas':
            self.setOffset(-73, -180)
        elif person == 'arythea':
            self.setOffset(-43, -133)
        elif person == 'goldyx':
            self.setOffset(-85, -140)
        elif person == 'tovak':
            self.setOffset(-120, -90)
        self.setPos(coords.center())
        