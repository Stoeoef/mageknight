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
from mageknight.data import * # @UnusedWildImport
from . import effects


class Card:
    """Abstract base class for all cards. Note that two instances are always considered different."""
    def __repr__(self):
        return type(self).__name__


def get(name):
    """Return the card of the given name."""
    # action cards
    for subclass in BasicAction.__subclasses__() + AdvancedAction.__subclasses__():
        if subclass.name == name:
            return subclass()
    if name == 'wound':
        return Wound()
    raise ValueError("There is no card with name '{}'.".format(name))
    
    
class ActionCard(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/{}/{}.jpg'
                            .format('advanced_actions' if self.isAdvanced else 'basic_actions', self.name))

    
class BasicAction(ActionCard):
    isAdvanced = False


class AdvancedAction(ActionCard):
    isAdvanced = True


class Wound(Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/wound.jpg')


class BattleVersatility(BasicAction):
    name = 'battle_versatility'
    title = translate('cards', 'Battle Versatility')
    color = Mana.red
    
    def basicEffect(self, match, player):
        options = [effects.AttackPoints(2),
                   effects.BlockPoints(2),
                   effects.AttackPoints(1, range=AttackRange.range)
                  ]
        effect = dialogs.choose(options)
        match.effects.add(effect)
    
    
    def strongEffect(self, match, player):
        options = [effects.AttackPoints(4),
                   effects.BlockPoints(4),
                   effects.AttackPoints(3, type=AttackType.fire),
                   effects.BlockPoints(3, type=BlockType.fire),
                   effects.AttackPoints(3, range=AttackRange.range),
                   effects.AttackPoints(2, range=AttackRange.siege)
                  ]
        effect = dialogs.choose(options)
        match.effects.add(effect)


class ColdToughness(BasicAction):
    name = 'cold_toughness'
    title = translate('carsd', 'Cold Toughness')
    color = Mana.blue
    
    def basicEffect(self, match, player):
        options = [effects.AttackPoints(2, type=AttackType.ice),
                   effects.BlockPoints(3, type=BlockType.ice),
                  ]
        effect = dialogs.choose(options)
        match.effects.add(effect)
    
    def strongEffect(self, match, player):
        match.effects.add(effects.ColdToughness())
        

class Concentration(BasicAction):
    name = 'concentration'
    title = translate('cards', 'Concentration')
    color = Mana.green
    
    def basicEffect(self, match, player):
        color = dialogs.chooseManaColor(fromList=[Mana.blue, Mana.white, Mana.red])
        match.effects.add(effects.ManaTokens(color))
        
    def strongEffect(self, match, player):
        concentration = effects.Concentration(2)
        match.effects.add(concentration)
        card = dialogs.chooseCard(player, type=ActionCard)
        player.removeCard(card)
        card.strongEffect(match, player)
        match.effects.remove(concentration)
        
    
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
        
    
class Determination(BasicAction):
    name = 'determination'
    title = translate('cards', 'Determination')
    color = Mana.blue
    
    def basicEffect(self, match, player):
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
    
    def strongEffect(self, match, player):
        match.effects.add(effects.BlockPoints(5))
    
    
class Improvisation(BasicAction):
    name = 'improvisation'
    title = translate('cards', 'Improvisation')
    color = Mana.red
    
    def _effect(self, match, player, amount):
        card = dialogs.chooseCard(player)
        player.removeCard(card)
        options = [effects.MovePoints(amount),
                   effects.InfluencePoints(amount),
                   effects.AttackPoints(amount),
                   effects.BlockPoints(amount)
                  ]
        match.effects.add(dialogs.choose(options))
        
    def basicEffect(self, match, player):
        self._effect(match, player, 3)
        
    def strongEffect(self, match, player):
        self._effect(match, player, 5)
    
    
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
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
    
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




        
