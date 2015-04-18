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

import functools

from PyQt5 import QtCore, QtWidgets
translate = QtCore.QCoreApplication.translate

from mageknight.gui import mainwindow
from mageknight.data import * # @UnusedWildImport


class ChooseDialog(QtWidgets.QDialog):
    def __init__(self, options):
        super().__init__(mainwindow.mainWindow)
        self.setWindowTitle(self.tr('Choose one'))
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.options = options       
        self.index = None
        for i, option in enumerate(options):
            button = QtWidgets.QPushButton(str(option))
            button.clicked.connect(functools.partial(self._choose, i))
            layout.addWidget(button)
        
    def _choose(self, index):
        self.index = index
        self.accept()
        
    @property
    def chosenOption(self):
        if self.index is not None:
            return self.options[self.index]
        else: return None
        
        
def choose(options):
    dialog = ChooseDialog(options)
    dialog.exec_()
    if dialog.chosenOption is not None:
        return dialog.chosenOption
    else: raise CancelAction()


def chooseManaColor(match=None, available=False, basic=True, fromList=None):
    if fromList is not None:
        colors = fromList
    else:
        assert match is not None
        if available:
            colors = [color for color in Mana if match.hasMana(color)]
            if len(colors) == 0:
                raise InvalidAction("You don't have mana")
        else:
            colors = Mana.basicColors()
    return choose(colors) # TODO: implement a nicer dialog, using crystal icons


def chooseCard(player, type=None, allowWounds=False):
    from mageknight.core import cards as cardsModule
    cards = []
    for card in player.handCards:
        if type is not None and not isinstance(card, type):
            continue
        if isinstance(card, cardsModule.Wound) and not allowWounds:
            continue
        cards.append(card)
    if len(cards) > 0:
        return choose(cards)
    else: raise InvalidAction("You don't have a suitable card")
