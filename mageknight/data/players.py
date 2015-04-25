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

from mageknight import utils
from mageknight.data import RoundType

__all__ = ['MIN_REPUTATION', 'MAX_REPUTATION', 'REPUTATION_NONE', 'REPUTATION_MODIFIERS',
           'Hero', 'Tactic', 'PlayerTactic']


MIN_REPUTATION = -7
MAX_REPUTATION = 7
REPUTATION_NONE = 'X' # lowest field on the reputation track 
REPUTATION_MODIFIERS = (REPUTATION_NONE, -5, -3, -2, -1, -1, 0, 0, 0, 1, 1, 2, 2, 3, 5)


class Hero(enum.Enum):
    """One of the heros of Mage Knight."""
    Norowas = 1
    Tovak = 2
    Arythea = 3
    Goldyx = 4
    
    def getDeedDeck(self):
        """Return the start deed deck for this hero."""
        ids = ['concentration', 'crystallize', 'determination', 'improvisation', 'mana_draw',
               'march', 'march', 'promise', 'rage', 'rage', 'stamina', 'stamina',
               'swiftness', 'swiftness', 'threaten', 'tranquility'
              ]
        if self is Hero.Norowas:
            ids[ids.index('promise')] = 'noble_manners'
        elif self is Hero.Tovak:
            ids[ids.index('determination')] = 'cold_toughness'
        elif self is Hero.Arythea:
            ids[ids.index('rage')] = 'battle_versatility'
        elif self is Hero.Goldy:
            ids[ids.index('concentration')] = 'will_focus'
            
        from mageknight.core import cards
        return [cards.get(id) for id in ids]
            
    
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
        if self is Tactic.none:
            return None
        elif self.value <= 6:
            return RoundType.day
        else: return RoundType.night
    
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
