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
# 

import functools

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from mageknight import utils
from mageknight.data import CombatRewardType
from . import playerarea, stock


class EndOfTurnView(QtWidgets.QDialog):
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setWindowTitle(self.tr("End of turn"))
        self.match = match
        layout = QtWidgets.QVBoxLayout(self)
        
        self.label = QtWidgets.QLabel("Combat rewards")
        layout.addWidget(self.label)
        self._buttons = []
        self.buttonLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.buttonLayout)
        
        self.scene = RewardsScene(self, self.match)
        view = QtWidgets.QGraphicsView(self.scene)
        view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(view)
        
        match.stateChanged.connect(self._update)
        match.combat.rewardsChanged.connect(self._update)
        self._update()
        
    def _update(self):
        for button in self._buttons:
            self.buttonLayout.removeWidget(button)
            button.setParent(None)
        self._buttons = []
            
        for reward in self.match.combat.rewards:
            if reward.count > 1:
                title = self.tr("{} ({}x)".format(reward.type.title, reward.count))
            else: title = reward.type.title
            button = QtWidgets.QPushButton(title)
            if reward.items is None:
                button.clicked.connect(functools.partial(self._rewardTypeChosen, reward))
            else:
                button.setEnabled(False)
            self._buttons.append(button)
            self.buttonLayout.addWidget(button)
        self.scene.update(self.match)
        
    def _rewardTypeChosen(self, reward):
        self.match.chooseRewardType(reward)


class RewardsScene(QtWidgets.QGraphicsScene):
    CRYSTAL_SIZE = QtCore.QSize(30, 30)
    CARD_SIZE = QtCore.QSize(107, 150)
    
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setBackgroundBrush(QtGui.QBrush(Qt.darkGray))
        self.stock = stock.Stock(RewardsScene.CARD_SIZE)
        self.addItem(self.stock)
        self.currentReward = None
        self.match = match
        
    def update(self, match):
        if len(self.match.combat.rewards) == 0:
            self.currentReward = None
            self.stock.clear()
            return
            
        for reward in self.match.combat.rewards:
            if reward.items is not None and reward != self.currentReward:
                self.currentReward = reward
                self.stock.clear()
                if reward.type is CombatRewardType.crystal:
                    self.stock.objectSize = RewardsScene.CRYSTAL_SIZE
                else: self.stock.objectSize = RewardsScene.CARD_SIZE
                break
            
        if self.currentReward is None:
            self.stock.clear()
        else:
            if self.currentReward.type is CombatRewardType.crystal:
                itemClass = ManaDieItem
            elif self.currentReward.type is CombatRewardType.unit:
                itemClass = playerarea.UnitItem
            else:
                itemClass = playerarea.CardItem
            self.stock.sync(itemClass, self.currentReward.items)
            
    def cardClicked(self, card, action):
        self.match.chooseRewardItem(self.currentReward, card)


class ManaDieItem(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, color, size):
        pixmap = utils.getPixmap('mk/mana/die_{}.png'.format(color.name), size)
        super().__init__(pixmap)
        self.color = color
        
    @property
    def object(self):
        return self.color
        