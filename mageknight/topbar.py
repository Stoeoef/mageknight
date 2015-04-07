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
        self.buttonBar = ButtonBar(match)
        layout.addWidget(self.buttonBar, 1)


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
    INNER_SPACE = 10
    OUTER_SPACE = 0
    
    def __init__(self, theMatch):
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                 QtWidgets.QSizePolicy.Fixed))
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
        return QtCore.QSize(count*self.SIZE + (count-1)*self.INNER_SPACE + 2*self.OUTER_SPACE,
                            self.SIZE + 2*self.OUTER_SPACE)
    
    def paintEvent(self, paintEvent):
        super().paintEvent(paintEvent)
        painter = QtGui.QPainter(self)
        for i, manaDie in enumerate(self._dice):
            pixmap = self._pixmaps[manaDie]
            point = QtCore.QPoint(self.OUTER_SPACE + i*(self.SIZE+self.INNER_SPACE), self.OUTER_SPACE)
            painter.drawPixmap(point, pixmap)
            
        
class ToggleViewAction(QtWidgets.QAction):
    def __init__(self, parent, viewId, title):
        super().__init__(parent)
        self.viewId = viewId
        self.setText(title)
        self.setCheckable(True)
        self.triggered.connect(self._triggered)
        self._connected = False
        
    def _triggered(self, checked):
        from mageknight import mainwindow
        view = mainwindow.mainWindow.getView(self.viewId)  # @UndefinedVariable
        if checked:
            if not self._connected:
                view.installEventFilter(self)
                self._connected = True
            view.show()
        else:
            view.hide()
            
    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Close:
            self.setChecked(False)
        return False # do not filter the event
        
    
class ButtonBar(QtWidgets.QToolBar):
    def __init__(self, match):
        super().__init__()
        self.match = match
        for view, title in [('fame', 'Fame'), ('shop', 'Shop'), ('tiles', 'Tiles'), ('lexicon', 'Lexicon')]:
            self.addAction(ToggleViewAction(self, view, title))
            