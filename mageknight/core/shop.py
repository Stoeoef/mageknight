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

from PyQt5 import QtCore

from mageknight.data import InvalidAction
from mageknight.attributes import * # @UnusedWildImport
from mageknight.core import assets


class Shop(AttributeObject):
    """The shop contains the advanced actions, spells, units and skills that can be obtained at various
    occasions (mainly interaction, but also level-up etc.).
    """

    advancedActionsChanged = QtCore.pyqtSignal()
    advancedActions = ListAttribute(assets.AdvancedAction)
    
    spellsChanged = QtCore.pyqtSignal()
    spells = ListAttribute(assets.Spell)
    
    unitsChanged = QtCore.pyqtSignal()
    units = ListAttribute(assets.Unit)
    
    monasteryOfferChanged = QtCore.pyqtSignal()
    monasteryOffer = ListAttribute(assets.AdvancedAction)
    
    commonSkillOfferChanged = QtCore.pyqtSignal()
    commonSkillOffer = ListAttribute(assets.Card) # TODO: use skill
    
    advancedActionsPile = ListAttribute(assets.AdvancedAction)
    spellsPile = ListAttribute(assets.Spell)
    artifactsPile = ListAttribute(assets.Artifact)
    regularUnitsPile = ListAttribute(assets.RegularUnit)
    eliteUnitsPile = ListAttribute(assets.EliteUnit)
    
    def __init__(self, match):
        super().__init__(match.stack)
        self.match = match
        
    @staticmethod
    def create(match):
        shop = Shop(match)
        shop.advancedActionsPile = assets.AdvancedAction.all()
        shop.spellsPile = assets.Spell.all()
        shop.artifactsPile = assets.Artifact.all()
        shop.regularUnitsPile = assets.RegularUnit.all()
        shop.eliteUnitsPile = assets.EliteUnit.all()
        for pile in [shop.advancedActionsPile, shop.spellsPile, shop.artifactsPile,
                     shop.regularUnitsPile, shop.eliteUnitsPile]:
            random.shuffle(pile)
        return shop
        
    def refreshUnits(self):
        unitCount = len(self.match.players) + 2
        self.units = self.regularUnitsPile[-unitCount:]
        del self.regularUnitsPile[-unitCount:]
    
    def revealAdvancedAction(self):
        self.stack.revealNewInformation()
        if len(self.advancedActions) >= 3 or len(self.advancedActionsPile) == 0:
            raise InvalidAction("Cannot reveal another advanced action")
        action = self.advancedActionsPile.pop()
        self.advancedActions.append(action)
        
    def revealAdvancedActions(self):
        while len(self.advancedActions) < 3 and len(self.advancedActionsPile) > 0:
            action = self.advancedActionsPile.pop()
            self.advancedActions.append(action)
        
        