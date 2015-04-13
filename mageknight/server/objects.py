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

from mageknight import stack
from mageknight.matchdata import * # @UnusedWildImport


class ManaSource(QtCore.QObject):
    """The mana source contains the mana dice available to all players. It behaves like a read-only list, so 
    e.g. 'len(source)' and 'source[2]' work as expected. The additional attribute 'count' stores the initial
    number of dice in the source (typically number of players + 2). The number returned by len(source) can
    be lower due to e.g. Mana Steal.
    """ 
    changed = QtCore.pyqtSignal()
    
    def __init__(self, match, count):
        super().__init__()
        self.match = match
        self.count = count
        self._dice = None
        self.shuffle()
    
    # Methods required for a read-only list
    def __len__(self):
        return len(self._dice)
    
    def __getitem__(self, index):
        return self._dice[index]
    
    def __contains__(self, object):
        return object in self._dice
    
    def __iter__(self):
        return iter(self._dice)
    
    def isValidAtRoundStart(self):
        """Return whether at least half of the dice show a basic colors (as required by the rules at round
        start)."""
        return sum(1 if die.isBasic else 0 for die in self._dice) >= self.count / 2
    
    def remove(self, index):
        color = self._dice[index]
        self.match.stack.push(stack.Call(self._remove, index),
                              stack.Call(self._insert, index, color))
        
    def _insert(self, index, color):
        """Insert a die of the given color at the specified index."""
        self._dice.insert(index, color)
        self.changed.emit()
        
    def _remove(self, index):
        """Remove the die at the given index from the source."""
        self._dice.pop(index)
        self.changed.emit()
        
    def shuffle(self):
        """Shuffle all dice in the source according to the rules."""
        self.match.stack.clear()
        while True:
            self._dice = [Mana.random() for _ in range(self.count)]
            if self.isValidAtRoundStart():
                break
        self.changed.emit()


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
    
    def initDeedDeck(self):
        names = ['march', 'concentration', 'rage', 'crystallize']
        self.drawPile = [cards.getActionCard(name) for name in names]
        self.cardCountChanged.emit()
        
    def drawCards(self, count=None):
        self.match.stack.clear()
        if count is None:
            count = self.cardLimit - self.handCardCount
        count = min(count, self.drawPileCount)
        if count > 0:
            self.handCards.extend(self.drawPile[-count:])
            del self.drawPile[-count:]
            self.cardCountChanged.emit()
            self.handCardsChanged.emit()
        
    def addCrystal(self, color):
        assert color.isBasic
        if self.crystals[color] < 3:
            self.match.stack.push(stack.Call(self._addCrystal, color),
                                  stack.Call(self._removeCrystal, color))
        else:
            self.match.effects.add(effects.ManaTokens(color))
    
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
        