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


class Stock(QtWidgets.QGraphicsObject):
    """This item arranges its child items in a nice layout. All child items must be of size *childSize*
    (if a child is smaller it will still get the specified space). When items are inserted or removed,
    animations are used to move all items to their new position.
    Warning: For these animations to work, all items must be subclasses of QGraphicsObject.
    """
    SPACING = 10 # spacing between items and borders
    
    def __init__(self, objectSize):
        super().__init__()
        self.objectSize = objectSize
        self._size = QtCore.QSizeF(600, 400)
        self._anims = QtCore.QParallelAnimationGroup(self)
        
    def size(self):
        """Return the size occupied by this stock."""
        return self._size
    
    def setSize(self, size):
        """Set the size that can be used to layout child items."""
        if size != self._size:
            self._size = QtCore.QSizeF(size)
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
        self.scene().removeItem(item)
        item.setParentItem(None)
        self.layout()
    
    def boundingRect(self):
        return QtCore.QRectF(self.pos(), self._size)
    
    def paint(self, painter, option, widget):
        return # TODO: paint something or set the correct flag
    
    def layout(self):
        """Recompute the position of all items."""
        self._anims.stop()
        self._anims.clear()
        column = 0
        x = self.SPACING
        y = self.SPACING
        width = self.objectSize.width()
        for item in self.childItems():
            if column > 0 and x + self.SPACING + width > self._size.width():
                # go to next row
                x = self.SPACING
                y += self.SPACING + self.objectSize.height()
                column = 0
            animation = QtCore.QPropertyAnimation(item, "pos", self)
            self._anims.addAnimation(animation)
            animation.setDuration(500)
            animation.setEndValue(QtCore.QPointF(x, y))
            animation.start()
            x += self.SPACING + width
            column += 1
        