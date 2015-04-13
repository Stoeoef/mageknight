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

from PyQt5 import QtCore
translate = QtCore.QCoreApplication.translate

from mageknight import utils
from mageknight.gui import dialogs
from .core import Mana
from .enemies import AttackRange
from . import effects


class Card:
    pass

class ActionCard(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/{}/{}.jpg'
                            .format('advanced_actions' if self.isAdvanced else 'basic_actions', self.name))
        
    
def getActionCard(name):
    for subclass in BasicAction.__subclasses__() + AdvancedAction.__subclasses__():
        if subclass.name == name:
            return subclass()
    else: raise ValueError("There is no action card with name '{}'.".format(name))
    
    
class BasicAction(ActionCard):
    isAdvanced = False


class AdvancedAction(ActionCard):
    isAdvanced = True


class March(BasicAction):
    name = 'march'
    title = translate('cards', 'March')
    color = Mana.green
    
    def basicEffect(self, match, player):
        match.effects.add(effects.MovePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.MovePoints(4))


class Stamina(BasicAction):
    name = 'stamina'
    title = translate('cards', 'Stamina')
    color = Mana.blue
    
    def basicEffect(self, match, player):
        match.effects.add(effects.MovePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.MovePoints(4))
        
    
class Rage(BasicAction):
    name = 'rage'
    title = translate('cards', 'rage')
    color = Mana.red
    
    def basicEffect(self, match, player):
        index = dialogs.choose(['Attack 2', 'Block 2'])
        match.effects.add((effects.AttackPoints if index == 0 else effects.BlockPoints)(2))
    
    def strongEffect(self, match, player):
        match.effects.add(effects.AttackPoints(4))


class Swiftness(BasicAction):
    name = 'swiftness'
    title = translate('cards', 'Swiftness')
    color = Mana.white
    
    def basicEffect(self, match, player):
        match.effects.add(effects.MovePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.AttackPoints(3, range=AttackRange.range))


class Crystallize(BasicAction):
    name = 'crystallize'
    title = translate('cards', 'Crystallize')
    color = Mana.blue
    
    def basicEffect(self, match, player):
        color = dialogs.chooseManaColor(match, available=True)
        player.addCrystal(color)
        
    def strongEffect(self, match, player):
        color = dialogs.chooseManaColor(match, available=False)
        player.addCrystal(color)
        
    
class Concentration(BasicAction):
    name = 'concentration'
    title = translate('cards', 'Concentration')
    color = Mana.green
    
    def basicEffect(self, match, player):
        colors = [Mana.blue, Mana.white, Mana.red]
        chosenColor = colors[dialogs.choose([color.name for color in colors])]
        match.effects.add(effects.ManaTokens(chosenColor))
        
    def strongEffect(self, match, player):
        concentration = effects.Concentration(2)
        match.effects.add(concentration)
        card = dialogs.chooseCard(player, type=ActionCard)
        card.strongEffect(match, player)
        match.effects.remove(concentration)
        
