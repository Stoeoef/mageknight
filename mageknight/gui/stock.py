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

import math

from PyQt5 import QtCore, QtWidgets

from mageknight import utils


class Stock(QtWidgets.QGraphicsObject):
    """This item arranges its child items in a nice layout. All child items must be of size *childSize*
    (if a child is smaller it will still get the specified space). When items are inserted or removed,
    animations are used to move all items to their new position.
    Warning: For these animations to work, all items must be subclasses of QGraphicsObject.
    
    By default, a Stock arranges all items in a single row.
    """
    PADDING = 10 # between items and borders
    SPACING = 10 # between items
    
    def __init__(self, objectSize):
        super().__init__()
        self.objectSize = objectSize
        self._anims = QtCore.QParallelAnimationGroup(self)
        self._cols = None
        self._rows = None
        self.setRowCount(1)
        
    def setColumnCount(self, cols):
        """Set the number of columns that the grid layout should use. The layout will always reserve enough
        space for these columns and use as many rows as necessary."""
        assert cols > 0
        if cols != self._cols:
            self._cols = cols
            self._rows = None
            self.layout()
            
    def setRowCount(self, rows):
        """Set the number of rows that the grid layout should use. The layout will always reserve enough
        space for these rows and use as many columns as necessary."""
        assert rows > 0
        if rows != self._rows:
            self._rows = rows
            self._cols = None
            self.layout()
        
    def items(self):
        """Return the list of child items."""
        return self.childItems()
    
    def addItem(self, item):
        """Append an item to the stock."""
        self.insertItem(-1, item)
    
    def insertItem(self, index, item):
        """Insert an item at the specified index (in self.items()) into the stock."""
        assert isinstance(item, QtWidgets.QGraphicsObject)
        self.prepareGeometryChange()
        # Docs: Should not add an item that belongs to the scene
        if item.scene() is not None:
            pos = self.mapFromItem(item, QtCore.QPointF(0, 0))
            item.scene().removeItem(item)
            item.setPos(pos) # this will keep the item's scene position after changing its parent
        item.setParentItem(self) # will add the item to the scene
        if index < 0:
            index += len(self.items())
        if index != len(self.items()) - 1:
            item.stackBefore(self.items()[index])
        self.layout()
        
    def removeItem(self, item):
        """Remove the given item from the stock."""
        self.prepareGeometryChange()
        self.scene().removeItem(item)
        item.setParentItem(None)
        self.layout()
        
    def removeItemAt(self, index):
        """Remove the item with the given index."""
        self.removeItem(self.items()[index])
        
    def clear(self):
        self.prepareGeometryChange()
        for item in self.items():
            self.scene().removeItem(item)
            item.setParentItem(None)
    
    def boundingRect(self):
        if self._cols is not None:
            necessaryRows = math.ceil(len(self.items()) / self._cols)
            width = self._cols * (self.objectSize.width() + self.SPACING) - self.SPACING
            height = necessaryRows * (self.objectSize.height() + self.SPACING) - self.SPACING
        elif self._rows is not None:
            necessaryColumns  = math.ceil(len(self.items()) / self._rows)
            width = necessaryColumns * (self.objectSize.width() + self.SPACING) - self.SPACING 
            height = self._rows * (self.objectSize.height() + self.SPACING) - self.SPACING
        else:
            width = height = 0
        return QtCore.QRectF(0, 0, max(0, width) + 2*self.PADDING, max(0, height) + 2*self.PADDING)
    
    def paint(self, painter, option, widget):
        pass
    
    def _moveItemToPos(self, item, x, y):
        animation = QtCore.QPropertyAnimation(item, b"pos", self)
        self._anims.addAnimation(animation)
        animation.setDuration(500)
        animation.setEndValue(QtCore.QPointF(x, y))
        animation.start()
        
    def layout(self):
        """Recompute the position of all items."""
        self._anims.stop()
        self._anims.clear()
        x = self.PADDING
        y = self.PADDING
        if self._cols is not None: 
            column = 0
            for item in self.childItems():
                if column >= self._cols:
                    # go to next row
                    x = self.PADDING
                    y += self.SPACING + self.objectSize.height()
                    column = 0
                self._moveItemToPos(item, x, y)
                x += self.SPACING + self.objectSize.width()
                column += 1
        elif self._rows is not None:
            row = 0
            for item in self.childItems():
                if row >= self._rows:
                    # go to next row
                    y = self.PADDING
                    x += self.SPACING + self.objectSize.width()
                    row = 0
                self._moveItemToPos(item, x, y)
                y += self.SPACING + self.objectSize.height()
                row += 1
                
    def sync(self, itemClass, objects, end=None):
        """Sync this stock's items with a list of objects (the second argument).
        This method will assume that each item has an
        attribute 'object' holding the object for an item. For the other direction, *itemClass* will be
        used to construct items from objects. The constructor of *itemClass* should take two arguments:
        the object and this stock's object size.
        The optional argument *end* can be used to restrict the syncing to self.items()[:end], i.e. items
        starting with the index *end* will not be touched.
        """
        # because added/removed items will trigger animations,
        # we cannot simply clear the stock and re-add everything
        if end is None:
            end = len(self.items())
        for item in self.items()[:end]: # in particular this creates a copy
            if item.object not in objects:
                self.removeItem(item)
                end -= 1
            else: item.update() # repaint items that were not added/removed
        for i, object in enumerate(objects):
            if i >= end or object != self.items()[i].object:
                item = itemClass(object, self.objectSize)
                self.insertItem(i, item)
                end += 1


class Row(Stock): # TODO: Create an abstract super class and make Row and Stock siblings
    def __init__(self):
        super().__init__(None)
        
    def boundingRect(self):
        width = height = 0
        for item in self.childItems():
            rect = item.boundingRect()
            width += rect.width()
            height = max(rect.height(), height)
        if len(self.childItems()) > 0:
            width += self.SPACING * (len(self.childItems())-1)
        width += 2 * self.PADDING
        height += 2 * self.PADDING
        print(width, height)
        return QtCore.QRectF(0, 0, width, height)
    
    def layout(self):
        self._anims.stop()
        self._anims.clear()
        x = self.PADDING
        items = self.childItems()
        height = max(item.boundingRect().height() for item in items)
        for item in items:
            rect = item.boundingRect()
            y = self.PADDING + (height-rect.height()) / 2
            self._moveItemToPos(item, x, y)
            x += self.SPACING + rect.width()
       
    
    
class GraphicsPixmapObject(QtWidgets.QGraphicsObject):
    """Like QGraphicsPixmapItem, but a subclass of QGraphicsObject as required by stock.Stock.
    As an additional feature, this item draws a version of *pixmap* scaled to *size* (if given) and shows
    the original pixmap as tooltip.
    """
    def __init__(self, pixmap, size=None):
        super().__init__()
        self.pixmap = pixmap
        if size is not None:
            self._scaled = utils.scalePixmap(pixmap, size)
        else: self._scaled = self.pixmap
        self.setToolTip(utils.html(pixmap))
    
    def size(self):
        return self._scaled.size()
    
    def boundingRect(self):
        return QtCore.QRectF(0, 0, self._scaled.width(), self._scaled.height())
    
    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self._scaled)
        
    def scaleFactor(self):
        return min(self._scaled.width() / self.pixmap.width(), self._scaled.height() / self.pixmap.height())
