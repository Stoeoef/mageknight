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

import enum

from PyQt5 import QtCore

from mageknight import utils


MIN_REPUTATION = -7
MAX_REPUTATION = 7
REPUTATION_MODIFIERS = ('X', -5, -3, -2, -1, -1, 0, 0, 0, 1, 1, 2, 2, 3, 5)  


class Hero(enum.Enum):
    """One of the heros of Mage Knight."""
    Norowas = 1
    Tovak = 2
    Arythea = 3
    Goldyx = 4

    
class Tactic(enum.Enum):
    """A tactic card, either from day or night rounds."""
    none = 0 # used before a tactic is selected
    earlyBird = 1
    rethink = 2
    manaSteal = 3
    planning = 4
    greatStart = 5
    theRightMoment = 6
    fromTheDusk = 7
    longNight = 8
    manaSearch = 9
    midnightMeditation = 10
    preparation = 11
    sparingPower = 12
    
    @property
    def roundType(self):
        from mageknight import match
        if self is Tactic.none:
            return None
        elif self.value <= 6:
            return match.RoundType.day
        else: return match.RoundType.night
    
    def pixmap(self, size=None):
        """Return a pixmap containing the tactic card."""
        if self is Tactic.none:
            return None
        else:
            name = '{}{}.jpg'.format('d' if self.value <= 6 else 'n', self.value)
            return utils.getPixmap('mk/cards/tactics/'+name, size)
    
    
class PlayerTactic:
    """A tactic card as played by a player. Additionally to a Tactic, this class can store things like a
    mana die or cards lying on the tactic card."""
    def __init__(self, tactic):
        self.tactic = tactic
        self.flipped = False
        self.cardCount = None
        self.manaDie = None
    
    # Redirect properties to the actual tactic
    @property
    def name(self):
        return self.tactic.name
    
    @property
    def roundType(self):
        return self.tactic.roundType
    
    def pixmap(self):
        return self.tactic.pixmap()

    
class Player(QtCore.QObject):
    """A Mage Knight player. This class manages the player's status."""
    levelChanged = QtCore.pyqtSignal(int)
    fameChanged = QtCore.pyqtSignal(int)
    reputationChanged = QtCore.pyqtSignal(int) # reputationPosition changed
    tacticChanged = QtCore.pyqtSignal(PlayerTactic)
    crystalsChanged = QtCore.pyqtSignal()
    cardCountChanged = QtCore.pyqtSignal()
    pointsChanged = QtCore.pyqtSignal()
                                
    def __init__(self, name, hero=None):
        super().__init__()
        self.name = name
        self.hero = hero
        self.tactic = PlayerTactic(Tactic.manaSteal)
        self.level = 1
        self.armor = 2
        self.cardLimit = 5
        self.fame = 0
        self.reputation = 0
        from mageknight import match
        self.crystals = {color: 0 for color in match.Mana.basicColors()}
        
        self.handCardCount = 5
        self.drawPileCount = 11
        self.discardPileCount = 0
        self.movementPoints = 0
        self.influencePoints = 0
    
    @property
    def reputationModifier(self):
        return REPUTATION_MODIFIERS[self.reputation - MIN_REPUTATION]
