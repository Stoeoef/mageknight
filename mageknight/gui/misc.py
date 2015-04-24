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

"""Miscellaneous components to use in QGraphicsScenes."""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class Title(QtWidgets.QGraphicsSimpleTextItem):
    """Display a title text."""
    SIZE = 16
    
    def __init__(self, title=''):
        super().__init__(title)
        font = self.font()
        font.setPointSize(self.SIZE)
        self.setFont(font)
        self.setBrush(QtGui.QBrush(Qt.yellow))
        
    def boundingRect(self):
        if self.text() != '':
            return super().boundingRect()
        else:
            return QtCore.QRectF(0, 0, 1, QtGui.QFontMetrics(self.font()).height())
        

class VerticalGroup(QtWidgets.QGraphicsItem):
    """Organize items in a column layout. *alignment* specifies the horizontal alignment."""
    SPACING = 10
    
    def __init__(self, alignment=Qt.AlignCenter):
        super().__init__()
        self.alignment = alignment
        
    def addItem(self, item):
        self.prepareGeometryChange()
        items = self.childItems()
        if self.alignment == Qt.AlignLeft:
            x = 0
        elif self.alignment == Qt.AlignCenter:
            width = item.boundingRect().width()
            myWidth = self.boundingRect().width()
            if width <= myWidth:
                x = (myWidth - width) / 2
            else: # move all other items
                x = 0
                offset = (width - myWidth) / 2
                for it in items:
                    it.setX(it.x() + offset)
        if len(items) > 0:
            y = items[-1].y() + items[-1].boundingRect().height()
        else: y = 0
        item.setPos(x, y)
        item.setParentItem(self)
        
    def paint(self, painter, option, widget):
        pass
    
    def boundingRect(self):
        return self.childrenBoundingRect()
