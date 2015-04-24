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

from mageknight.data import Terrain


class TerrainCostsView(QtWidgets.QDialog):
    """Display the fame board and the players' shield tokens on it in a QGraphicsView."""
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Terrain costs"))
        self.match = match
        
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel()
        layout.addWidget(self.label)
        self.match.terrainCostsChanged.connect(self._update)
        self._update()

    def _update(self):
        lines = []
        for terrain in Terrain:
            if self.match.isTerrainPassable(terrain):
                # TODO: display translated terrain titles
                lines.append("{}: {}".format(terrain.name, self.match.terrainCosts[terrain]))
            
        self.label.setText('<br />'.join(lines))
        