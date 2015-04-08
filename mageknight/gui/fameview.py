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

import math, collections

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from mageknight import utils


class FameView(QtWidgets.QDialog):
    """Display the fame board and the players' shield tokens on it in a QGraphicsView."""
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Fame board"))
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        view = QtWidgets.QGraphicsView()
        view.scale(0.5, 0.5)
        view.setScene(FameViewScene(parent, match))
        layout.addWidget(view)
        
    
class FameViewScene(QtWidgets.QGraphicsScene):
    """QGraphicsScene containing the fame board (as background) and the players' shield tokens on it."""
    def __init__(self, parent, match):
        super().__init__(parent)
        self.match = match
        self.setBackgroundBrush(Qt.black)
        self.bgPixmap = utils.getPixmap('mk/fame_board.jpg')
        self.setSceneRect(QtCore.QRectF(0, 0, self.bgPixmap.width(), self.bgPixmap.height()))
    
        # Create shield tokens for each player
        self.fameItems = {}
        self.reputationItems = {}
        self.addItem
        for player in match.players:
            self.fameItems[player] = ShieldTokenItem(player)
            self.addItem(self.fameItems[player])
            self.reputationItems[player] = ShieldTokenItem(player)
            self.addItem(self.reputationItems[player])
            player.fameChanged.connect(self.updateFame)
            player.reputationChanged.connect(self.updateReputation)

        self.updateFame()
        self.updateReputation()
        
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        painter.drawPixmap(rect, self.bgPixmap, rect)
        
    def _posFromFame(self, fame):
        """Return the row and column on the fame board that belongs to *fame*."""
        fame = fame % 120
        # The first numbers in row n is (n+1)^2-1
        row = int(math.sqrt(fame + 1))-1 
        column = fame - ((row+1)**2-1)
        return row, column
        
    # For each row one the fame board:
    # x-coord of first field, y-coord of all fields and x-offset between neighbor fields
    _rowData = [(160, 70, 253), (140, 195, 167), (163, 319, 131), (154, 442, 111), (149, 568, 99),
                (145, 692, 90), (140, 816, 83.5), (140, 940, 78.4), (139, 1065, 74.5), (137, 1188, 71.6)]
    
    def updateFame(self):
        """Update the displayed fame of all players (we always need to update all players, even if only
        one player has changed, because items on the same field are shifted slightly).
        """ 
        # First find out the positions where the items should be placed without shifting
        coords = collections.defaultdict(list)
        for player, item in self.fameItems.items():
            row, column = self._posFromFame(player.fame)
            x, y, offset = self._rowData[row]
            point = (x + column*offset, y)
            coords[point].append(item)
            
        # when several items should be placed at the same position, shift them vertically
        for (x, y), items in coords.items():
            if len(items) == 1:
                items[0].setPos(x, y)
                items[0].setZValue(1)
            else:
                offset = 20 if len(items) <= 2 else 30
                for i, item in enumerate(items):
                    item.setPos(x, y+offset - 2*offset*i/(len(items)-1))
                    item.setZValue(i+1)

    # For each field on the reputation track:
    # (x,y)-coordinates of the position for the first and second shield token on that field.
    _repData = [(966, 116, 966, 132), # -7
                (1036, 142, 1032, 160),
                (1106, 168, 1100, 188),
                (1182, 182, 1174, 200),
                (1258, 192, 1250, 208),
                (1328, 216, 1316, 236),
                (1386, 246, 1374, 266),
                (1450, 310, 1434, 324),
                (1494, 396, 1468, 404),
                (1502, 460, 1472, 464),
                (1504, 536, 1474, 536),
                (1486, 612, 1462, 612),
                (1484, 684, 1464, 682),
                (1478, 758, 1462, 756),
                (1470, 828, 1454, 828)
            ]
    
    def updateReputation(self):
        """Update the displayed reputation of all players (we always need to update all players, even if only
        one player has changed, because items on the same field are shifted slightly).
        """ 
        # First find out the positions where the items should be placed without shifting
        coords = collections.defaultdict(list)
        from mageknight.player import MIN_REPUTATION
        for player, item in self.reputationItems.items():
            repData = self._repData[player.reputation - MIN_REPUTATION]
            coords[repData].append(item)
        
        for (x1, y1, x2, y2), items in coords.items():
            # items are positioned at (x1, y1), shifted towards (x2,y2) multiple times
            xOffset = x2-x1
            yOffset = y2-y1
            # How often do we want to shift?
            if len(items) == 1:
                multipliers = [1]
            elif len(items) == 2:
                multipliers = [0, 2]
            else: multipliers = range(len(items))
            
            for i, m, item in zip(range(len(items)), multipliers, items):
                item.setPos(x1 + m*xOffset, y1 + m*yOffset)
                item.setZValue(i+1)
        
    
class ShieldTokenItem(QtWidgets.QGraphicsPixmapItem):
    """A QGraphicsItem containing the shield token of the given player."""
    def __init__(self, player):
        super().__init__()
        pixmap = utils.getPixmap('mk/players/shield_{}.png'.format(player.hero.name.lower()))
        self.setPixmap(pixmap)
        self.setOffset(-pixmap.width()//2, -pixmap.height()//2)
