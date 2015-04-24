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

import random

from mageknight.data import InvalidAction
from . import baseshop


class Shop(baseshop.BaseShop):
    """The shop contains the advanced actions, spells, units and skills that can be obtained at various
    occasions (mainly interaction, but also level-up etc.).
    """
    def __init__(self, match):
        super().__init__(match)
        
    def refreshUnits(self):
        self.units = []
        unitCount = len(self.match.players) + 2
        for _ in range(unitCount):
            self.units.append(_take(self.regularUnitsPile))
        self.unitsChanged.emit()
    
    def revealAdvancedAction(self):
        self.stack.revealNewInformation()
        if len(self.advancedActions) >= 3 or len(self.advancedActionsPile) == 0:
            raise InvalidAction("Cannot reveal another advanced action")
        self.advancedActions.append(_take(self.advancedActionsPile))
        self.advancedActionsChanged.emit()
        
    def revealAdvancedActions(self):
        while len(self.advancedActions) < 3 and len(self.advancedActionsPile) > 0:
            self.advancedActions.append(_take(self.advancedActionsPile))
        self.advancedActionsChanged.emit()
        
        
    
def _take(list):
    """Remove and return a random element from *list*."""
    return list.pop(random.randint(0, len(list)-1))
