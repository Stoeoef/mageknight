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
        
        # Hand cards (maximum image size is 365x514)
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
        player.unitsChanged.connect(self._updateUnits)
        self._updateUnits()
        
    def _updateHandCards(self):
        self.cards.sync(CardItem, self.player.handCards)
                
    def _updateUnits(self):
        unitItemCount = sum(1 for item in self.units.items() if isinstance(item, UnitItem))
        self.units.sync(UnitItem, self.player.units, end=unitItemCount) # don't sync UnitSlots
        
        # Sync UnitSlots
        slotDifference = len(self.units.items()) - self.player.unitLimit
        if slotDifference > 0: # too many slot items
            for _ in range(slotDifference):
                self.units.removeItemAt(self.player.unitCount) # always remove the first slot
        elif slotDifference < 0:
            for _ in range(-slotDifference):
                self.units.addItem(UnitSlot(self.player, self.units.objectSize))
            
    def unitClicked(self, unit, action):
        if action is not None:
            self.match.activateUnit(unit, action)


# Use different subclasses to implement stuff like spent/wounded units etc.
class SkillItem(stock.GraphicsPixmapObject):
    def __init__(self, skill, size): # TODO: currently *skill* is just a string
        super().__init__(utils.getPixmap('mk/skills/'+skill+'.jpg'), size)
        

class CardItem(stock.GraphicsPixmapObject):
    """This item displays a deed card and allows the user to choose one of the effects of the card."""
    def __init__(self, card, size):
        super().__init__(card.pixmap(), size)
        self.card = card
        
    @property
    def object(self):
        return self.card
    
    def mousePressEvent(self, event):
        event.accept()
        
    def mouseReleaseEvent(self, event):
        # TODO: Currently this supports only action cards
        if 295*self.scaleFactor() < event.pos().y() < 395*self.scaleFactor():
            self.scene().match.playCard(self.card, 0)
        elif 395*self.scaleFactor() < event.pos().y() < 495*self.scaleFactor():
            self.scene().match.playCard(self.card, 1)
        event.accept()
        
    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu()
        for effect in self.scene().match.sidewaysEffects():
            menu.addAction(str(effect))
        selectedAction = menu.exec_(event.screenPos())
        if selectedAction is not None:
            index = menu.actions().index(selectedAction)
            self.scene().match.playSideways(self.card, index)


class UnitItem(stock.GraphicsPixmapObject):    
    """This item displays a unit card along with the player's token (if the unit is spent) and optionally
    wounds and a banner. Clicking on one of the unit's action will activate the unit.
    """
    _playerTokens = {} # cache for player tokens. Maps player -> pixmap
    _wound = None
    
    def __init__(self, unit, size):
        super().__init__(unit.pixmap(), size)
        self.unit = unit
        
    @property
    def object(self):
        return self.unit
    
    @staticmethod
    def _getPlayerToken(player, size):
        if player not in UnitItem._playerTokens:
            size = size.width() * 0.65
            size = QtCore.QSize(size, size)
            token = utils.getPixmap('mk/players/level_token_back_{}.png'
                                    .format(player.hero.name.lower()),
                                    size=size)
            UnitItem._playerTokens[player] = token
        return UnitItem._playerTokens[player]
        
    def paint(self, painter, option, widget):
        # Note that the additional painting done here does not affect the tooltip,
        # which still shows the original pixmap
        super().paint(painter, option, widget)
        if not self.unit.isReady or self.unit.isWounded:
            assert self.unit.owner is not None
            painter.fillRect(self.boundingRect(), QtGui.QColor(0, 0, 0, 100))
            if self.unit.isWounded:
                if UnitItem._wound is None:
                    size = self.size() * 0.8
                    UnitItem._wound = utils.getPixmap('mk/cards/wound.jpg', size=size)
                pixmap = UnitItem._wound
                point = self.boundingRect().center() - pixmap.rect().center()
                if self.unit.wounds == 1:
                    painter.drawPixmap(point, pixmap)
                else:
                    size = self.size() * 0.6
                    pixmap = utils.getPixmap('mk/cards/wound.jpg', size=size)
                    painter.drawPixmap(0, 0, pixmap)
                    point = self.boundingRect().bottomRight() - pixmap.rect().bottomRight()
                    painter.drawPixmap(point, pixmap)
                
            if not self.unit.isReady:
                token = UnitItem._getPlayerToken(self.unit.owner, self.size())
                painter.drawPixmap(self.boundingRect().center() - token.rect().center(), token)
           
    def mousePressEvent(self, event):
        event.accept()
        
    def mouseReleaseEvent(self, event):
        for action in reversed(self.unit.actions):
            if event.pos().y() >= action.pos*self.scaleFactor():
                self.scene().unitClicked(self.unit, action)
                break
        else: self.scene().unitClicked(self.unit, None)
        event.accept()


class UnitSlot(QtWidgets.QGraphicsObject):
    """This item is used to mark an empty unit slot."""
    def __init__(self, owner, size):
        super().__init__()
        self.owner = owner
        self.size = size
        
    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.size.width(), self.size.height())
    
    def paint(self, painter, option, widget):
        token = UnitItem._getPlayerToken(self.owner, self.size)
        point = self.boundingRect().center() - token.rect().center()
        painter.drawPixmap(point, token)
        painter.fillRect(self.boundingRect(), QtGui.QColor(0, 0, 0, 100))
