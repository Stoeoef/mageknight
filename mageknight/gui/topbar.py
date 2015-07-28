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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt 

from mageknight import utils
from mageknight.data import Mana, AttackRange, InvalidAction


class TopBar(QtWidgets.QWidget):
    def __init__(self, match):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        self.roundWidget = RoundWidget(match)
        layout.addWidget(self.roundWidget)
        self.manaSourceWidget = ManaSourceWidget(match)
        layout.addWidget(self.manaSourceWidget)
        self.buttonBar = ButtonBar(match)
        layout.addWidget(self.buttonBar, 1)
        
        cheatBar = CheatBar(match)
        layout.addWidget(cheatBar)


class RoundWidget(QtWidgets.QLabel):
    ROMAN_NUMBERS = ['I', 'II', 'III', 'IV', 'V', 'VI']
    
    def __init__(self, match):
        super().__init__()
        match.roundChanged.connect(self._roundChanged)
        self._roundChanged(match.round) # initialize
        
    def _roundChanged(self, round):
        self.setText(self.tr('Round {}: {}').format(self.ROMAN_NUMBERS[round.number-1], round.type.name))
        

class ManaSourceWidget(QtWidgets.QWidget):
    """This widget displays the mana dice in the source. It always reserves enough space for all dice, even
    if some of them are currently absent.
    """
    SIZE = 30
    INNER_SPACE = 10
    OUTER_SPACE = 0
    
    def __init__(self, match):
        super().__init__()
        self.match = match
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                 QtWidgets.QSizePolicy.Fixed))
        self._pixmaps = {
           color: utils.getPixmap('mk/mana/die_{}.png'.format(color.name))
                           .scaled(self.SIZE, self.SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                for color in Mana
        }
        self.match.source.changed.connect(self._sourceChanged)
        self._sourceChanged() # initialize
    
    def _sourceChanged(self):
        self._dice = list(self.match.source)
        self.update()
        
    def sizeHint(self):
        count = self.match.source.count
        return QtCore.QSize(count*self.SIZE + (count-1)*self.INNER_SPACE + 2*self.OUTER_SPACE,
                            self.SIZE + 2*self.OUTER_SPACE)
    
    def paintEvent(self, paintEvent):
        super().paintEvent(paintEvent)
        painter = QtGui.QPainter(self)
        for i, manaDie in enumerate(self._dice):
            pixmap = self._pixmaps[manaDie]
            point = QtCore.QPoint(self.OUTER_SPACE + i*(self.SIZE+self.INNER_SPACE), self.OUTER_SPACE)
            painter.drawPixmap(point, pixmap)
        
#     def mouseReleaseEvent(self, event):
#         for i in range(len(self._dice)):
#             rect = QtCore.QRect(self.OUTER_SPACE + i*(self.SIZE+self.INNER_SPACE), self.OUTER_SPACE,
#                                 self.SIZE, self.SIZE)
#             if rect.contains(event.pos()):
#                 self.match.chooseSourceDie(i)
            
        
        
    
class ButtonBar(QtWidgets.QToolBar):
    """The bar of buttons at the top."""
    def __init__(self, match):
        super().__init__()
        self.match = match
        from mageknight.gui import mainwindow
        for action in mainwindow.mainWindow.viewActions:  # @UndefinedVariable
            self.addAction(action)
            
        stretch = QtWidgets.QWidget()
        stretch.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.addWidget(stretch)

        self.addAction(self.match.stack.createUndoAction())
        self.addAction(self.match.stack.createRedoAction())
        
            

class CheatBar(QtWidgets.QToolBar):
    def __init__(self, match):
        super().__init__()
        self.match = match
        import functools
        from mageknight.core import effects
        for pointsType in [effects.MovePoints, effects.InfluencePoints,
                           effects.BlockPoints, effects.AttackPoints]:
            effect = pointsType(4)
            action = QtWidgets.QAction(effect.title[:2], self)
            action.triggered.connect(functools.partial(self._clicked, match.effects.add, effect))
            self.addAction(action)
            
        effect = effects.AttackPoints(4, range=AttackRange.siege)
        action = QtWidgets.QAction('Si', self)
        action.triggered.connect(functools.partial(self._clicked, match.effects.add, effect))
        self.addAction(action)
            
        action = QtWidgets.QAction('Ma', self)
        action.triggered.connect(functools.partial(self._clicked, self._addMana))
        self.addAction(action)
        
        action = QtWidgets.QAction('Ca', self)
        action.triggered.connect(functools.partial(self._clicked, self.match.currentPlayer.drawCards, 1))
        self.addAction(action)
        
    def _clicked(self, method, *args):
        self.match.stack.beginMacro()
        args = args[:-1] # hack: remove the last argument which comes from the "triggered" signal
        try:
            method(*args)
            self.match.stack.endMacro()
        except InvalidAction as e:
            print(e)
            self.match.stack.abortMacro()
        
    def _addMana(self):
        from mageknight.gui import dialogs
        from mageknight.core import effects
        color = dialogs.chooseManaColor(self.match, basic=False)
        if color is not None:
            self.match.effects.add(effects.ManaTokens(color))
        