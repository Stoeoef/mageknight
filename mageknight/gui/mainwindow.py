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
        
    def availableViews(self):
        """Return a list of (view id, view title)-tuples for all available views. Views are popup windows
        offer additional game information (e.g. the fame board)."""
        return [
            ('fame', self.tr("Fame board")),
            ('cards', self.tr("Cards"))
        ]
        
    def getView(self, viewId):
        """Return the view with the given id. Create it when it is first requested.
        Known ids are:
            - fame: The fame/reputation board
        """
        if viewId not in self._views:
            if viewId == 'fame':
                from mageknight.gui import fameview
                self._views[viewId] = fameview.FameView(self, self.match)
            elif viewId == 'cards':
                from mageknight.gui import cardsview
                self._views[viewId] = cardsview.CardsView(self)
            else:
                raise ValueError("Invalid view id: '{}'".format(viewId))
        return self._views[viewId]
