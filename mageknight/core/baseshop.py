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
from mageknight.core import cards, units


class BaseShop(QtCore.QObject):
    advancedActionsChanged = QtCore.pyqtSignal()
    spellsChanged = QtCore.pyqtSignal()
    unitsChanged = QtCore.pyqtSignal()
    monasteryOfferChanged = QtCore.pyqtSignal()
    commonSkillOfferChanged = QtCore.pyqtSignal()
    
    def __init__(self, match):
        super().__init__()
        self.match = match
        
        # Create piles and fill them with all cards/units
        self.advancedActionsPile = []
        for cardClass in cards.AdvancedAction.__subclasses__(): # @UndefinedVariable
            self.advancedActionsPile.append(cardClass())
        self.spellsPile = []
        for spellClass in cards.Spell.__subclasses__(): # @UndefinedVariable
            self.spellsPile.append(spellClass())
        self.regularUnitsPile = []
        for unitClass in units.RegularUnit.__subclasses__(): # @UndefinedVariable
            for _ in range(unitClass.count):
                self.regularUnitsPile.append(unitClass())
        self.eliteUnitsPile = []
        for unitClass in units.EliteUnit.__subclasses__(): # @UndefinedVariable
            for _ in range(unitClass.count):
                self.regularUnitsPile.append(unitClass())
        
        # Create offers
        self.advancedActions = []
        self.spells = []
        self.units = []
        self.monasteryOffer = []
        self.commonSkillOffer = []
    
    def takeAdvancedAction(self, card):
        index = self.advancedActions.index(card)
        self.match.stack.push(stack.Call(self._removeAdvancedAction, card),
                              stack.Call(self._insertAdvancedAction, index, card))
        
    def _insertAdvancedAction(self, index, card):
        assert len(self.advancedActions) < 3
        self.advancedActions.insert(index, card)
        self.advancedActionsChanged.emit()
        
    def _removeAdvancedAction(self, card):
        self.advancedActions.remove(card)
        self.advancedActionsChanged.emit()
    
    def takeUnit(self, unit):
        index = self.units.index(unit)
        self.match.stack.push(stack.Call(self._removeUnit, unit),
                              stack.Call(self._insertUnit, index, unit))
        
    def _insertUnit(self, index, unit):
        self.units.insert(index, unit)
        self.unitsChanged.emit()
        
    def _removeUnit(self, unit):
        self.units.remove(unit)
        self.unitsChanged.emit()
            