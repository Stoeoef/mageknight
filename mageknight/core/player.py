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

from . import baseplayer, cards

class Player(baseplayer.Player):                                
    def initDeedDeck(self):
        names = ['improvisation', 'threaten', 'rage', 'crystallize', 'march', 'march', 'mana_draw', 'tranquility', ] #TODO: 
        self.drawPile = [cards.get(name) for name in names]
        self.cardCountChanged.emit()
        
    def drawCards(self, count=None):
        self.match.revealNewInformation()
        if count is None:
            count = self.cardLimit - self.handCardCount
        count = min(count, self.drawPileCount)
        if count > 0:
            self.handCards.extend(self.drawPile[-count:])
            del self.drawPile[-count:]
            self.cardCountChanged.emit()
            self.handCardsChanged.emit()
        
    def addCrystal(self, color):
        """Contrary to base implementation: If player already has three crystals of the given color,
        automatically add token instead of crystal.""" 
        assert color.isBasic
        if self.crystals[color] < 3:
            super().addCrystal(color)
        else: self.addToken(color)
        
    
