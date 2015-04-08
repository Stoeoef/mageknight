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

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

mainWindow = None # mainWindow instance

class MainWindow(QtWidgets.QWidget):
    """Main window of the application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Mage Knight"))
        global mainWindow
        mainWindow = self
        
        from mageknight import match
        self.match = match.Match()
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.setSpacing(0)
        leftLayout.setContentsMargins(0,0,0,0)
        layout.addLayout(leftLayout, 1)
        
        from mageknight.gui import topbar, mapview, playerarea
        self.topBar = topbar.TopBar(self.match)
        leftLayout.addWidget(self.topBar)
        self.mapView = mapview.MapView(self, self.match)
        leftLayout.addWidget(self.mapView, 1)
        self.playerColumn = playerarea.PlayerColumn(self.match)
        layout.addWidget(self.playerColumn)
        
        self.resize(1000, 700)
        
        self._views = {}
        
    def getView(self, viewId):
        if viewId not in self._views:
            self._views[viewId] = QtWidgets.QDialog(self) # TODO implement views
            self._views[viewId].resize(100, 100)
        return self._views[viewId]
