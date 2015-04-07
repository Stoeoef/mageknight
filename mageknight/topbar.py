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

from mageknight import match, utils

class TopBar(QtWidgets.QWidget):
    def __init__(self, match):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        self.roundWidget = RoundWidget(match)
        layout.addWidget(self.roundWidget)
        self.manaSourceWidget = ManaSourceWidget(match)
        layout.addWidget(self.manaSourceWidget)
        layout.addStretch()


class RoundWidget(QtWidgets.QLabel):
    ROMAN_NUMBERS = ['I', 'II', 'III', 'IV', 'V', 'VI']
    
    def __init__(self, match):
        super().__init__()
        match.roundChanged.connect(self._roundChanged)
        self._roundChanged(match.round) # initialize
        
    def _roundChanged(self, round):
        self.setText('Round {}: {}'.format(self.ROMAN_NUMBERS[round.number-1], round.type.name))
        

class ManaSourceWidget(QtWidgets.QWidget):
    SIZE = 30
    SPACE = 10
    
    def __init__(self, theMatch):
        super().__init__()
        #self.setFrameShape(QtWidgets.QFrame.Box)
        self._pixmaps = {
           color: utils.getPixmap('mk/die_{}.png'.format(color.name))
                           .scaled(self.SIZE, self.SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                for color in match.Mana
        }
        self.match = theMatch
        self.match.source.changed.connect(self._sourceChanged)
        self._sourceChanged() # initialize
    
    def _sourceChanged(self):
        self._dice = list(self.match.source)
        
    def sizeHint(self):
        count = self.match.source.count
        return QtCore.QSize((self.SIZE+self.SPACE)*count, self.SIZE + self.SPACE)
    
    def paintEvent(self, paintEvent):
        super().paintEvent(paintEvent)
        painter = QtGui.QPainter(self)
        for i, manaDie in enumerate(self._dice):
            pixmap = self._pixmaps[manaDie]
            point = QtCore.QPoint(self.SPACE//2 + i*(self.SIZE+self.SPACE), self.SPACE//2)
            painter.drawPixmap(point, pixmap)
            