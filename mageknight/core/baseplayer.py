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

from PyQt5 import QtCore

from mageknight.data import * # @UnusedWildImport
from mageknight import stack
from . import effects


class Player(QtCore.QObject):
    """A Mage Knight player. This class manages the player's status."""
    levelChanged = QtCore.pyqtSignal(int)
    fameChanged = QtCore.pyqtSignal(int)
    reputationChanged = QtCore.pyqtSignal(int) # reputationPosition changed
    tacticChanged = QtCore.pyqtSignal(PlayerTactic)
    crystalsChanged = QtCore.pyqtSignal()
    cardCountChanged = QtCore.pyqtSignal()
    handCardsChanged = QtCore.pyqtSignal()
                                
    def __init__(self, name, hero=None):
        super().__init__()
        self.match = None
        self.name = name
        self.hero = hero
        self.tactic = PlayerTactic(Tactic.manaSteal)
        self.level = 1
        self.armor = 2
        self.cardLimit = 5
        self.fame = 0
        self.reputation = 0
        self.crystals = {color: 0 for color in Mana.basicColors()}
        
        self.drawPile = []
        self.handCards = []
        self.discardPile = []
    
    @property
    def drawPileCount(self):
        return len(self.drawPile)
    
    @property
    def handCardCount(self):
        return len(self.handCards)
    
    @property
    def discardPileCount(self):
        return len(self.discardPile)
    
    @property
    def reputationModifier(self):
        return REPUTATION_MODIFIERS[self.reputation - MIN_REPUTATION]
    
    def addMana(self, color):
        self.match.effects.add(effects.ManaTokens(color))
        
    def removeMana(self, color):
        self.match.effects.remove(effects.ManaTokens(color))
        
    def addCrystal(self, color):
        assert color.isBasic
        self.match.stack.push(stack.Call(self._addCrystal, color),
                              stack.Call(self._removeCrystal, color))
    
    def removeCrystal(self, color):
        assert color.isBasic and self.crystals[color] > 0
        self.match.stack.push(stack.Call(self._removeCrystal, color),
                              stack.Call(self._addCrystal, color))
        
    def _addCrystal(self, color):
        assert self.crystals[color] < 3
        self.crystals[color] += 1
        self.crystalsChanged.emit()
        
    def _removeCrystal(self, color):
        assert self.crystals[color] > 0
        self.crystals[color] -= 1
        self.crystalsChanged.emit()
        
    def removeCard(self, card):
        index = self.handCards.index(card)
        self.match.stack.push(stack.Call(self._removeCard, card),
                              stack.Call(self._insertCard, index, card))
    
    def _insertCard(self, index, card):
        self.handCards.insert(index, card)
        self.handCardsChanged.emit()
        
    def _removeCard(self, card):
        self.handCards.remove(card)
        self.handCardsChanged.emit()
    