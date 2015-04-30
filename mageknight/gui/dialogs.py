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
    def __init__(self, options, labelFunc=str, title=translate('ChooseDialog', "Choose one"),
                 text=None, default=None):
        super().__init__(mainwindow.mainWindow)
        self.setWindowTitle(title)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.options = options       
        self.index = None
        self.default = default

        if text is not None:
            label = QtWidgets.QLabel(text)
            label.setWordWrap(True)
            layout.addWidget(label)
            
        for i, option in enumerate(options):
            button = QtWidgets.QPushButton(labelFunc(option))
            button.clicked.connect(functools.partial(self._choose, i))
            layout.addWidget(button)
        
    def _choose(self, index):
        self.index = index
        self.accept()
        
    @property
    def chosenOption(self):
        if self.index is not None:
            return self.options[self.index]
        else: return self.default
        
        
def choose(options, **kwargs):
    dialog = ChooseDialog(options, **kwargs)
    dialog.exec_()
    if dialog.chosenOption is not None:
        return dialog.chosenOption
    else: raise CancelAction()
    
    
def chooseIndex(options, **kwargs):
    dialog = ChooseDialog(options, **kwargs)
    dialog.exec_()
    if dialog.index is not None:
        return dialog.index
    else: raise CancelAction()


def chooseManaColor(match=None, available=False, basic=True, fromList=None, default=None):
    if fromList is not None:
        colors = fromList
    else:
        if available:
            assert match is not None
            colors = [color for color in Mana if match.hasMana(color)]
            if len(colors) == 0:
                raise InvalidAction("You don't have mana")
        else:
            colors = Mana.basicColors() if basic else list(Mana)
        
    # remove duplicates
    colorOptions = []
    for color in colors:
        if color not in colorOptions:
            colorOptions.append(color)
    return choose(colorOptions, default=default) # TODO: implement a nicer dialog, using crystal icons


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
    

def ask(question, title=''):
    button = QtWidgets.QMessageBox.question(mainwindow.mainWindow, title, question)
    return button == QtWidgets.QMessageBox.Yes    

