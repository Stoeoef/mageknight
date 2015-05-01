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
translate = QtCore.QCoreApplication.translate

from mageknight import utils
from mageknight.core import cards, effects
from mageknight.data import * # @UnusedWildImport


class Artifact(cards.Card):
    def pixmap(self):
        return utils.getPixmap('mk/cards/artifacts/{}.jpg'.format(self.name))


class RubyRing(Artifact):
    name = 'ruby_ring'
    title = translate('cards', "Ruby Ring")
    
    def basicEffect(self, match, player):
        match.effects.add(effects.ManaTokens(Mana.red))
        player.addCrystal(Mana.red)
        player.fame += 1
        
        
class SapphireRing(Artifact):
    name = 'sapphire_ring'
    title = translate('cards', "Sapphire Ring")
    
    def basicEffect(self, match, player):
        match.effects.add(effects.ManaTokens(Mana.blue))
        player.addCrystal(Mana.blue)
        player.fame += 1
        
        
class DiamondRing(Artifact):
    name = 'diamond_ring'
    title = translate('cards', "Diamond Ring")
    
    def basicEffect(self, match, player):
        match.effects.add(effects.ManaTokens(Mana.white))
        player.addCrystal(Mana.white)
        player.fame += 1
        
        
class EmeraldRing(Artifact):
    name = 'emerald_ring'
    title = translate('cards', "Emerald Ring")
    
    def basicEffect(self, match, player):
        match.effects.add(effects.ManaTokens(Mana.green))
        player.addCrystal(Mana.green)
        player.fame += 1
