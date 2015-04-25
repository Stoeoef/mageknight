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

from . import baseplayer
from mageknight.data import Site


class Player(baseplayer.Player):                                
    def initCards(self):
        """Initialize cards at the beginning of a round."""
        self.drawPile.extend(self.handCards)
        self.drawPile.extend(self.discardPile)
        self.handCards = []
        self.discardPile = []
        random.shuffle(self.drawPile)
        self.cardCountChanged.emit()
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
            count = self.modifiedCardLimit() - self.handCardCount
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
        
    def knockOut(self):
        """Discard all non-wound cards from the hand."""
        for card in list(self.handCards):
            if not card.isWound():
                self.discard(card)
    
    
