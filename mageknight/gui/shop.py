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
from mageknight.gui import stock, misc


class ShopView(QtWidgets.QDialog):
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Shop: Available Actions, Spells, Units and Skills"))
        layout = QtWidgets.QVBoxLayout(self)
        scene = ShopScene(match)
        view = QtWidgets.QGraphicsView(scene)
        view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        view.ensureVisible(QtCore.QRectF(0,0,1,1), 10, 10)
        layout.addWidget(view)
        
        
class ShopScene(QtWidgets.QGraphicsScene):
    def __init__(self, match):
        super().__init__()
        self.match = match
        self.setBackgroundBrush(QtGui.QBrush(Qt.black))
        
        size = QtCore.QSize(107, 150) # Maximum card image size is 365x514
        SPACING = 10
        
        # Advanced actions
        group1 = misc.VerticalGroup()
        group1.setPos(0, 0)
        self.addItem(group1)
        title = misc.Title(self.tr("Adv. Actions"))
        group1.addItem(title)
        drawCardPixmap = utils.getPixmap('mk/draw_card.png', size=QtCore.QSize(50, 40))
        drawItem = QtWidgets.QGraphicsPixmapItem(drawCardPixmap)
        group1.addItem(drawItem)
        self.advancedActions = stock.Stock(size)
        self.advancedActions.setColumnCount(1)
        group1.addItem(self.advancedActions)
        self.match.shop.advancedActionsChanged.connect(self._updateAdvancedActions)
        self._updateAdvancedActions()
        
        # Spells
        x = group1.sceneBoundingRect().right() + 2*SPACING
        group2 = misc.VerticalGroup()
        group2.setPos(x, 0)
        self.addItem(group2)
        title = misc.Title(self.tr("Spells"))
        group2.addItem(title)
        drawItem = QtWidgets.QGraphicsPixmapItem(drawCardPixmap)
        group2.addItem(drawItem)
        self.spells = stock.Stock(size)
        self.spells.setColumnCount(1)
        group2.addItem(self.spells)
        self.match.shop.spellsChanged.connect(self._updateSpells)
        self._updateSpells()

        # Units
        x = group2.sceneBoundingRect().right() + 2*SPACING
        group3 = misc.VerticalGroup(alignment=Qt.AlignLeft)
        group3.setPos(x, 0)
        self.addItem(group3)
        title = misc.Title(self.tr("Units"))
        group3.addItem(title)
        self.units = stock.Stock(size)
        self.units.setRowCount(2)
        group3.addItem(self.units)
        self.match.shop.unitsChanged.connect(self._updateUnits)
        self._updateUnits()
            
        # Monastery
        title = misc.Title(self.tr("Monastery Offer"))
        group3.addItem(title)
        self.monasteryOffer = stock.Stock(size)
        self.monasteryOffer.setRowCount(1)
        group3.addItem(self.monasteryOffer)
        self.match.shop.monasteryOfferChanged.connect(self._updateMonasteryOffer)
        self._updateMonasteryOffer()
        
        # Common Skill Offer
        y = max(group1.sceneBoundingRect().bottom(),
                group2.sceneBoundingRect().bottom(),
                group3.sceneBoundingRect().bottom())
        y += 2*SPACING
        group4 = misc.VerticalGroup(alignment=Qt.AlignLeft)
        group4.setPos(0, y)
        self.addItem(group4)
        title = misc.Title(self.tr("Common Skill Offer"))
        group4.addItem(title)
        size = QtCore.QSize(76, 50) # (maximum image size is 216x142)
        self.skills = stock.Stock(size)
        self.skills.setRowCount(2)
        group4.addItem(self.skills)
        self.match.shop.commonSkillOfferChanged.connect(self._updateCommonSkillOffer)
        self._updateCommonSkillOffer()
        
    def buy(self, area, object):
        if area == self.units:
            self.match.recruitUnit(object)
          
    def _updateAdvancedActions(self):
        self.advancedActions.sync(ShopItem, self.match.shop.advancedActions)
          
    def _updateSpells(self):
        self.spells.sync(ShopItem, self.match.shop.spells)
        
    def _updateUnits(self):
        self.units.sync(ShopItem, self.match.shop.units)
        
    def _updateMonasteryOffer(self):
        self.monasteryOffer.sync(ShopItem, self.match.shop.monasteryOffer)
        
    def _updateCommonSkillOffer(self):
        self.skills.sync(ShopItem, self.match.shop.commonSkillOffer)
        

class ShopItem(stock.GraphicsPixmapObject):
    """This item displays a deed card and allows the user to choose one of the effects of the card."""
    def __init__(self, object, size):
        super().__init__(object.pixmap(), size)
        self.object = object
        
    def mousePressEvent(self, event):
        event.accept()
        
    def mouseReleaseEvent(self, event):
        self.scene().buy(self.parentItem(), self.object)
        event.accept()
