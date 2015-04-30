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
from . import effects, cards


class Player(QtCore.QObject):
    """A Mage Knight player. This class manages the player's status."""
    levelChanged = QtCore.pyqtSignal(int)
    fameChanged = QtCore.pyqtSignal(int)
    reputationChanged = QtCore.pyqtSignal(int) # reputationPosition changed
    tacticChanged = QtCore.pyqtSignal(PlayerTactic)
    crystalsChanged = QtCore.pyqtSignal()
    cardCountChanged = QtCore.pyqtSignal()
    handCardsChanged = QtCore.pyqtSignal()
    unitsChanged = QtCore.pyqtSignal()
                                
    def __init__(self, name, hero=None):
        super().__init__()
        self.match = None
        self.name = name
        self.hero = None
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
        
        self.units = []
        
        if hero is not None:
            self.setHero(hero)
            
    def setHero(self, hero):
        self.hero = hero
        self.drawPile = hero.getDeedDeck()
    
    @property
    def unitCount(self):
        return len(self.units)
    
    @property
    def unitLimit(self):
        """Return the number of units the player might own simultaneously."""
        return (self.level+1) // 2
        
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
        
    def addWounds(self, wounds, toDiscardPile=False):
        if not toDiscardPile:
            for _ in range(wounds):
                self.addCard(cards.get('wound'))
        else:
            for _ in range(wounds):
                self.addToDiscardPile(cards.get('wound'))
                
    def heal(self, fromDiscardPile=False):
        theList = self.handCards if not fromDiscardPile else self.discardPile
        for card in theList:
            if card.isWound:
                self.removeCard(card)
                break
        
    def addCard(self, card):
        self.match.stack.push(stack.Call(self._insertCard, self.handCardCount, card),
                              stack.Call(self._removeCard, card))
    
    def removeCard(self, card):
        index = self.handCards.index(card)
        self.match.stack.push(stack.Call(self._removeCard, card),
                              stack.Call(self._insertCard, index, card))
    
    def discard(self, card):
        assert card in self.handCards
        self.removeCard(card)
        self.addToDiscardPile(card)
    
    def addToDiscardPile(self, card):
        self.match.stack.push(stack.Call(self._insertCardToDiscardPile, 0, card),
                              stack.Call(self._removeCardFromDiscardPile, card))
        
    def putOnDrawPile(self, card):
        self.match.stack.push(stack.Call(self._insertCardToDrawPile, len(self.drawPile), card),
                              stack.Call(self._removeCardFromDrawPile, card))
        
    def _insertCard(self, index, card):
        self.handCards.insert(index, card)
        self.handCardsChanged.emit()
        self.cardCountChanged.emit()
        
    def _removeCard(self, card):
        self.handCards.remove(card)
        self.handCardsChanged.emit()
        self.cardCountChanged.emit()
    
    def _insertCardToDiscardPile(self, index, card):
        self.discardPile.insert(index, card)
        self.cardCountChanged.emit()
        
    def _removeCardFromDiscardPile(self, card):
        self.discardPile.remove(card)
        self.cardCountChanged.emit()
        
    def _insertCardToDrawPile(self, index, card):
        self.drawPile.insert(index, card)
        self.cardCountChanged.emit()
        
    def _removeCardFromDrawPile(self, card):
        self.drawPile.remove(card)
        self.cardCountChanged.emit()
        
    def addFame(self, fame):
        self.match.stack.push(stack.Call(self._addFame, fame),
                              stack.Call(self._addFame, -fame))
            
    def _addFame(self, fame):
        self.fame += fame # fame might be negative and is allowed to drop below 0
        self.fameChanged.emit(self.fame)
    
    def addReputation(self, reputation):
        old = self.reputation
        new = max(MIN_REPUTATION, min(old+reputation, MAX_REPUTATION))
        self.match.stack.push(stack.Call(self._setReputation, new),
                              stack.Call(self._setReputation, old))
        
    def _setReputation(self, reputation):
        if reputation != self.reputation: 
            self.reputation = reputation
            self.reputationChanged.emit(reputation)
            
    def addUnit(self, unit):
        self.match.stack.push(stack.Call(self._insertUnit, len(self.units), unit),
                              stack.Call(self._removeUnit, unit))
        
    def removeUnit(self, unit):
        index = self.units.index(unit)
        self.match.stack.push(stack.Call(self._removeUnit, unit),
                              stack.Call(self._insertUnit, index, unit))
                              
    def _insertUnit(self, index, unit):
        self.units.insert(index, unit)
        unit.owner = self
        self.unitsChanged.emit()
        
    def _removeUnit(self, unit):
        self.units.remove(unit)
        unit.owner = None
        self.unitsChanged.emit()
        
    def spendUnit(self, unit):
        self.match.stack.push(stack.Call(self._spendUnit, unit),
                              stack.Call(self._readyUnit, unit))
    
    def readyUnit(self, unit):
        self.match.stack.push(stack.Call(self._readyUnit, unit),
                              stack.Call(self._spendUnit, unit))
        
    def _spendUnit(self, unit):
        assert unit.isReady
        unit.isReady = False
        self.unitsChanged.emit()
        
    def _readyUnit(self, unit):
        assert not unit.isReady
        unit.isReady = True
        self.unitsChanged.emit()
        
    def woundUnit(self, unit, wounds=1):
        self.match.stack.push(stack.Call(self._woundUnit, unit, wounds),
                              stack.Call(self._healUnit, unit, wounds))
        
    def _woundUnit(self, unit, wounds):
        assert not unit.isWounded
        assert wounds in (1, 2)
        unit.wounds = wounds
        self.unitsChanged.emit()
    
    def healUnit(self, unit):
        assert unit.isWounded
        self.match.stack.push(stack.Call(self._healUnit, unit, 1),
                              stack.Call(self._woundUnit, unit, 1))
        
    def _healUnit(self, unit, wounds):
        assert unit.wounds >= wounds
        unit.wounds -= wounds
        self.unitsChanged.emit()
        
    