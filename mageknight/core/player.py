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

import random

from PyQt5 import QtCore

from mageknight.attributes import * # @UnusedWildImport
from mageknight.data import * # @UnusedWildImport
from mageknight import stack
from . import effects, units, cards


class Player(AttributeObject):
    levelChanged = QtCore.pyqtSignal(int)
    level = IntAttribute(default=1, sendValue=True)
    
    fameChanged = QtCore.pyqtSignal(int)
    fame = IntAttribute(sendValue=True)
    
    reputationChanged = QtCore.pyqtSignal(int)
    reputation = IntAttribute(sendValue=True, minimum=MIN_REPUTATION, maximum=MAX_REPUTATION, strict=False)
    
    tacticChanged = QtCore.pyqtSignal(PlayerTactic)
    tactic = Attribute(PlayerTactic, sendValue=True)
    
    armor = IntAttribute(default=2)
    cardLimit = IntAttribute(default=5)
    
    cardCountChanged = QtCore.pyqtSignal()
    handCardsChanged = QtCore.pyqtSignal()
    drawPile = ListAttribute(cards.Card, signal='cardCountChanged')
    handCards = ListAttribute(cards.Card, signal='handCardsChanged') # is connected to cardCountChanged in __init__
    discardPile = ListAttribute(cards.Card, signal='cardCountChanged')
    
    unitsChanged = QtCore.pyqtSignal()
    units = ListAttribute(units.Unit,
                          itemAttributes=[('isReady', bool),
                                          ('wounds', int),
                                          ('isProtected', bool)])
    
    crystalsChanged = QtCore.pyqtSignal()
    
    def __init__(self, match, name, hero):
        super().__init__(match.stack)
        self.match = match
        self.name = name
        self.hero = hero
        self.crystals = {color: 0 for color in Mana.basicColors()}
        self.drawPile = hero.getDeedDeck()
        self.tactic = PlayerTactic(Tactic.earlyBird)
    
    @property
    def unitLimit(self):
        """Return the number of units the player might own simultaneously."""
        return (self.level+1) // 2
    
    @property
    def reputationModifier(self):
        return REPUTATION_MODIFIERS[self.reputation - MIN_REPUTATION]
                                        
    def initCards(self):
        """Initialize cards at the beginning of a round."""
        self.drawPile.extend(self.handCards)
        self.drawPile.extend(self.discardPile)
        self.handCards = []
        self.discardPile = []
        random.shuffle(self.drawPile)
        self.handCardsChanged.connect(self.cardCountChanged)
        self.handCardsChanged.emit()
        
    def modifiedCardLimit(self):
        limit = self.cardLimit
        map = self.match.map
        keeps = [site for site in map.sites.values() if site.type is Site.keep and site.owner is self]
        playerCoords = map.persons[self]
        if any(keep.coords == playerCoords or keep.coords.isNeighborOf(playerCoords) for keep in keeps):
            limit += len(keeps)
        # TODO: cities
        return limit
        
    def drawCards(self, count=None):
        self.match.revealNewInformation()
        if count is None:
            count = self.modifiedCardLimit() - len(self.handCards)
        count = min(count, len(self.drawPile))
        if count > 0:
            self.handCards.extend(self.drawPile[-count:])
            del self.drawPile[-count:]
            self.cardCountChanged.emit()
            self.handCardsChanged.emit()
        
    def discard(self, card):
        self.handCards.remove(card)
        self.discardPile.append(card)
    
    def addMana(self, color):
        self.match.effects.add(effects.ManaTokens(color))
        
    def removeMana(self, color):
        self.match.effects.remove(effects.ManaTokens(color))
        
    def addCrystal(self, color):
        assert color.isBasic
        if self.crystals[color] < 3:
            self.match.stack.push(stack.Call(self._addCrystal, color),
                                  stack.Call(self._removeCrystal, color))
        else: self.addToken(color)
    
    def removeCrystal(self, color):
        assert color.isBasic and self.crystals[color] > 0
        self.match.stack.push(stack.Call(self._removeCrystal, color),
                              stack.Call(self._addCrystal, color))
        
    def knockOut(self):
        """Discard all non-wound cards from the hand."""
        for card in list(self.handCards):
            if not card.isWound():
                self.discard(card)
        
    def addWounds(self, wounds, toDiscardPile=False):
        theList = self.handCards if not toDiscardPile else self.discardPile
        from . import cards
        for _ in range(wounds):
            theList.append(cards.get('wound'))
                
    def heal(self, fromDiscardPile=False):
        theList = self.handCards if not fromDiscardPile else self.discardPile
        for card in theList:
            if card.isWound:
                self.removeCard(card)
                break
    
    def healUnit(self, unit):
        if unit.wounds > 0:
            self.units.setWounds(unit, unit.wounds - 1)
            
    def woundUnit(self, unit, wounds=1):
        self.units.setWounds(unit, unit.wounds + wounds)
    
    def _addCrystal(self, color):
        assert self.crystals[color] < 3
        self.crystals[color] += 1
        self.crystalsChanged.emit()
        
    def _removeCrystal(self, color):
        assert self.crystals[color] > 0
        self.crystals[color] -= 1
        self.crystalsChanged.emit()