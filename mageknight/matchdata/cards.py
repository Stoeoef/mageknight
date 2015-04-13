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
from .core import Mana

# TODO: __all__


class Card:
    pass

class ActionCard(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/{}/{}.jpg'
                            .format('advanced_actions' if self.isAdvanced else 'basic_actions', self.name))
        
    
class BasicAction(ActionCard):
    isAdvanced = False


class AdvancedAction(ActionCard):
    isAdvanced = True


class March(BasicAction):
    name = 'march'
    title = translate('cards', 'March')
    color = Mana.green
    
    def basicEffect(self, match, player):
        player.changeMovePoints(2)
        
    def strongEffect(self, match, player):
        player.changeMovePoints(4)


class Stamina(BasicAction):
    name = 'stamina'
    title = translate('cards', 'Stamina')
    color = Mana.blue
    
    def basicEffect(self, match, player):
        player.changeMovePoints(2)
        
    def strongEffect(self, match, player):
        player.changeMovePoints(4)
        
        
def getActionCard(name):
    for subclass in BasicAction.__subclasses__() + AdvancedAction.__subclasses__():
        if subclass.name == name:
            return subclass()
    else: raise ValueError("There is no action card with name '{}'.".format(name))
