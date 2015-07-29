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

from mageknight import hexcoords, utils
from mageknight.data import * # @UnusedWildImport


class MapView(QtWidgets.QGraphicsView):
    """Displays the map. See MapModel."""
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
    """This scene contains the map tiles and various items on top of it: players, enemies and shield tokens.
    """
    def __init__(self, parent, match):
        super().__init__(parent) # parent is necessary or segfaults occur
        self.match = match
        self.map = match.map
        self._personItems = {}
        self._siteItems = {}
        self._exploreItems = []
        
        self.match.stateChanged.connect(self._stateChanged)
        self.map.tileAdded.connect(self._tileAdded)
        self.map.siteChanged.connect(self._siteChanged)
        self.map.personChanged.connect(self._personChanged)
        
        # Initialize
        for coords in self.map.tiles.keys():
            self._tileAdded(coords)
        for coords in self.map.sites.keys():
            self._siteChanged(coords)
        for person in self.map.persons.keys():
            self._personChanged(person)

    def _tileAdded(self, coords):
        tileItem = TileItem(self.map.tiles[coords], coords)
        self.addItem(tileItem)
        
    def _siteChanged(self, coords):
        if coords not in self._siteItems:
            # Site added
            site = self.map.sites[coords]
            item = SiteItem(site)
            item.setPos(coords.center())
            self._siteItems[coords] = item
            self.addItem(item)
        elif coords not in self.map.sites:
            # Site removed
            self.removeItem(self._siteItems[coords])
            del self._siteItems[coords]
        else:
            # Site changed
            site = self.map.sites[coords]
            self._siteItems[coords]._update()
            self._shiftItemsAt(coords)
            
    def _stateChanged(self, state):
        for item in self._exploreItems:
            self.removeItem(item)
        self._exploreItems = []
        if state is State.explore:
            coords = self.map.persons[self.match.currentPlayer]
            tiles = self.map.getExplorableTiles(coords)
            for tile in tiles:
                item = ExploreItem(tile)
                self._exploreItems.append(item)
                self.addItem(item)
    
    def _shiftItemsAt(self, coords):
        """Shift all enemy tokens and persons at the specified hex slightly, so that the user can see that
        there are multiple items at this position.
        """
        items = []
        if coords in self._siteItems:
            items.extend(self._siteItems[coords]._enemyItems)
        for item in self._personItems.values():
            if item.coords == coords:
                items.append(item)
                
        if len(items) == 1:
            item = items[0]
            item.setZValue(1)
            # EnemyItems are stored within a SiteItem => local coordinate system
            # Persons are stored as toplevel items => scene coordinate system
            if isinstance(item, EnemyItem):
                pos = QtCore.QPointF(0, 0)
            else: pos = coords.center()
            item.setPos(pos)
            
        elif len(items) > 1:
            for i, item in enumerate(items):
                offset = -20 + 40*i/(len(items)-1)
                pos = QtCore.QPointF(offset, 0)
                if not isinstance(item, EnemyItem):
                    pos += coords.center()
                item.setPos(pos)
                item.setZValue(i+1)
    
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
        if self.match.state is State.explore:
            self.match.explore(coords)
        else: self.match.movePlayer(coords)


class TileItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem to display a Mage Knight tile."""
    def __init__(self, tile, coords):
        super().__init__()
        self.tile = tile
        self.coords = coords
        self.setOffset(-3*hexcoords.ALTITUDE, -2.5*hexcoords.SIDE) # position of top left corner
        self.setPixmap(tile.pixmap())
        self.setPos(coords.center())
        

class SiteItem(QtWidgets.QGraphicsItem):
    def __init__(self, site):
        super().__init__()
        self.site = site
        self._enemyItems = []
        self._update()
        self._shieldItem = None
        
    def _update(self):
        self.prepareGeometryChange()
        for item in self.childItems():
            self.scene().removeItem(item)
            self._enemyItems.clear()
            
        for enemy in self.site.enemies:
            item = EnemyItem(enemy)
            self._enemyItems.append(item)
            item.setParentItem(self)
        
        if self.site.owner is not None:
            pixmap = utils.getPixmap('mk/players/shield_{}.png'.format(self.site.owner.hero.name.lower()))
            item = QtWidgets.QGraphicsPixmapItem(pixmap)
            # to make sure that the site below remains visible, we do not center the token vertically
            item.setOffset(-pixmap.width()/2, 0)
            item.setParentItem(self)
    
    def boundingRect(self):
        return self.childrenBoundingRect()
    
    def paint(self, painter, option, widget=None):
        pass

    def __repr__(self):
        return "<SiteItem {} at {}>".format(self.site.type, self.site.coords)

    
class EnemyItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem that displays an enemy token."""
    def __init__(self, enemy):
        super().__init__()
        assert isinstance(enemy, (Enemy, UnknownEnemy))
        self.enemy = enemy
        pixmap = enemy.pixmap()
        pixmap = pixmap.scaled(pixmap.width()*0.8, pixmap.height()*0.8,
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        self.setOffset(-pixmap.width()/2, -pixmap.height()/2)


class PersonItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem that displays the mini-figure of a person."""
    def __init__(self, person, coords):
        super().__init__()
        self.person = person
        self.coords = coords
        self.setPixmap(utils.getPixmap('mk/players/{}.png'.format(person.hero.name.lower())))
        if person.hero == Hero.Norowas:
            self.setOffset(-73, -180)
        elif person.hero == Hero.Arythea:
            self.setOffset(-43, -133)
        elif person.hero == Hero.Goldyx:
            self.setOffset(-85, -140)
        elif person.hero == Hero.Tovak:
            self.setOffset(-120, -90)
        else:
            assert False
        self.setPos(coords.center())
        
    def move(self, coords):
        """Move the PersonItem to the specified hex."""
        self.coords = coords
        self.setPos(coords.center())
        

class ExploreItem(QtWidgets.QGraphicsItem):
    """This item is used to highlight explorable tiles during State.explore."""
    RECT = None
    
    def __init__(self, coords):
        super().__init__()
        self.setPos(coords.center())
        if ExploreItem.RECT is None:
            ExploreItem.RECT = QtCore.QRectF(0, 0, hexcoords.ALTITUDE * 6, hexcoords.SIDE * 5)
            ExploreItem.RECT.translate(-ExploreItem.RECT.center())
        
    def boundingRect(self):
        return ExploreItem.RECT
        rect = QtCore.QRectF(0, 0, ExploreItem.SIZE.width(), ExploreItem.SIZE.height())
        rect = rect.translated(-3*hexcoords.ALTITUDE, -2.5*hexcoords.SIDE) # position of top left corner
        return rect
        
    def paint(self, painter, option, widget):
        coords0 = hexcoords.HexCoords(0, 0)
        points = [0.9 * point for point in coords0.corners()]
        for coords in [coords0] + coords0.neighbors():
            if coords == coords0:
                painter.setBrush(QtGui.QBrush(utils.color("065f93")))
            else: painter.setBrush(QtGui.QBrush(utils.color("44b5f5")))
                
            painter.translate(coords.center())
            painter.drawPolygon(*points)
            painter.translate(-coords.center())
        
        
