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

from mageknight import utils
from mageknight.gui import stock


class PlayerArea(QtWidgets.QWidget):
    """This area contains the player's skills, hand cards and units."""
    def __init__(self, match, player):
        super().__init__()
        self.match = match
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.view = QtWidgets.QGraphicsView()
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.scene = PlayerAreaScene(match, player, self)
        self.view.setScene(self.scene)
        layout.addWidget(self.view)
        
        
class PlayerAreaScene(QtWidgets.QGraphicsScene):
    def __init__(self, match, player, parent):
        super().__init__(parent)
        self.match = match
        self.player = player
        self.setBackgroundBrush(QtGui.QBrush(Qt.darkGray))
        
        # Skills (maximum image size is 216x142)
        size = QtCore.QSize(76, 50)
        self.skills = stock.Stock(size)
        self.skills.setColumnCount(1)
        self.addItem(self.skills)
        
        for skill in ['norowas_1', 'norowas_2', 'norowas_3']:
            item = SkillItem(skill, size)
            self.skills.addItem(item)
        
        # Hand cards (maximum image size is 365x514
        size = QtCore.QSize(107, 150)
        self.cards = stock.Stock(size)
        self.cards.setColumnCount(5)
        self.cards.setPos(self.skills.x() + self.skills.boundingRect().right() + 10, 0)
        self.addItem(self.cards)
        player.handCardsChanged.connect(self._updateHandCards)
        self._updateHandCards()
            
        # Units
        size = QtCore.QSize(107, 150)
        self.units = stock.Stock(size)
        self.units.setColumnCount(3)
        self.units.setPos(self.cards.x() + self.cards.boundingRect().right() + 40, 0)
        self.addItem(self.units)
        
        for unit in ['regular_units/peasants', 'regular_units/foresters', 'regular_units/northern_monks']:
            item = UnitItem(unit, size)
            self.units.addItem(item)
        
    def _updateHandCards(self):
        for item in self.cards.items():
            if item.card not in self.player.handCards:
                self.cards.removeItem(item)
        for i, card in enumerate(self.player.handCards):
            items = self.cards.items()
            if i >= len(items) or items[i].card != card:
                self.cards.insertItem(i, CardItem(card, self.cards.objectSize))


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
        
    def boundingRect(self):
        return QtCore.QRectF(0, 0, self._scaled.width(), self._scaled.height())
    
    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self._scaled)
        
    def scaleFactor(self):
        return min(self._scaled.width() / self.pixmap.width(), self._scaled.height() / self.pixmap.height())


# Use different subclasses to implement stuff like used/wounded units etc.
class SkillItem(GraphicsPixmapObject):
    def __init__(self, skill, size): # TODO: currently *skill* is just a string
        super().__init__(utils.getPixmap('mk/skills/'+skill+'.jpg'), size)
        

class CardItem(GraphicsPixmapObject):
    """This item displays a deed card and allows the user to choose one of the effects of the card."""
    def __init__(self, card, size):
        super().__init__(card.pixmap(), size)
        self.card = card
    
    def mousePressEvent(self, event):
        event.accept()
        
    def mouseReleaseEvent(self, event):
        # TODO: Currently this supports only action cards
        if 295*self.scaleFactor() < event.pos().y() < 395*self.scaleFactor():
            self.scene().match.playCard(self.card, 0)
        elif 395*self.scaleFactor() < event.pos().y() < 495*self.scaleFactor():
            self.scene().match.playCard(self.card, 1)
        event.accept()
        
    
class UnitItem(GraphicsPixmapObject):
    def __init__(self, unit, size): # TODO: currently *unit* is just a string
        super().__init__(utils.getPixmap('mk/cards/'+unit+'.jpg'), size)
        
        