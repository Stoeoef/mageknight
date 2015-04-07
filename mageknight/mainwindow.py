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


class MainWindow(QtWidgets.QWidget):
    """Main window of the application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mage Knight")
        from mageknight import match
        self.match = match.Match()
        
        layout = QtWidgets.QHBoxLayout(self)
        leftLayout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(leftLayout)
        
        from mageknight import topbar, mapview
        self.topBar = topbar.TopBar(self.match)
        leftLayout.addWidget(self.topBar)
        self.mapView = mapview.MapView(self, self.match)
        leftLayout.addWidget(self.mapView, 1)
        
        self.resize(1000, 700)
