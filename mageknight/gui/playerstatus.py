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

from PyQt5 import QtCore, QtWidgets

from mageknight import utils
from mageknight.matchdata import Mana


class PlayerColumn(QtWidgets.QWidget):
    """The PlayerColumn contains one PlayerStatus widget for each player."""
    def __init__(self, match):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        for player in match.players:
            layout.addWidget(PlayerStatus(match, player))
        layout.addStretch(1)
            
    
class PlayerStatus(QtWidgets.QFrame):
    """A PlayerStatus widget displays information about one player: name, level, fame, crystals etc."""
    def __init__(self, match, player):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.match = match
        self.player = player
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        nameLabel = QtWidgets.QLabel(player.name)
        layout.addWidget(nameLabel)
        
        rowLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(rowLayout)
        
        rowLayout.addWidget(LevelTokenWidget(player))
        rowLayout.addWidget(TacticWidget(player))
        rowLayout.addWidget(FameReputationWidget(player))
        
        rowLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(rowLayout)
        rowLayout.addWidget(CardCountWidget(player))
        
        rowLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(rowLayout)
        rowLayout.addWidget(PointsWidget(player))
        
        rowLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(rowLayout)
        for color in Mana.basicColors():
            rowLayout.addWidget(CrystalsWidget(player, color))
        

class LevelTokenWidget(QtWidgets.QLabel):
    """Display the level token of a player (including level, armor and hand card limit)."""
    SIZE = QtCore.QSize(40, 40)
    
    def __init__(self, player):
        super().__init__()
        player.levelChanged.connect(self.setLevel)
        self._pixmap = None
        self.setLevel(player.level)
             
    def setLevel(self, level):
        """Set the level displayed in this widget."""
        self._pixmap = utils.getPixmap('mk/players/level_token_{}.png'.format((level+1)//2))
        self.setToolTip(utils.html(self._pixmap))
        self.setPixmap(utils.scalePixmap(self._pixmap, self.SIZE))


class FameReputationWidget(QtWidgets.QWidget):
    """Display fame and reputation of a player."""
    def __init__(self, player):
        super().__init__()
        layout = QtWidgets.QGridLayout(self)
        layout.setVerticalSpacing(0)
        
        iconLabel = QtWidgets.QLabel()
        iconLabel.setPixmap(utils.getPixmap('mk/fame_icon.png'))
        layout.addWidget(iconLabel, 0, 0)
        self.fameLabel = QtWidgets.QLabel()
        layout.addWidget(self.fameLabel, 0, 1)
        
        iconLabel = QtWidgets.QLabel()
        iconLabel.setPixmap(utils.getPixmap('mk/reputation_icon.png'))
        layout.addWidget(iconLabel, 1, 0)
        self.reputationLabel = QtWidgets.QLabel()
        layout.addWidget(self.reputationLabel, 1, 1)
        
        player.fameChanged.connect(self.setFame)
        player.reputationChanged.connect(self.setReputation)
        self.setFame(player.fame)
        self.setReputation(player.reputation)
        
    def setFame(self, fame):
        """Set the fame displayed in this widget."""
        self.fameLabel.setText(str(fame))
        
    def setReputation(self, reputation):
        """Set the reputation displayed in this widget."""
        self.reputationLabel.setText(str(reputation))
        
    
class TacticWidget(QtWidgets.QLabel):
    """Display the tactic of a player, along with stuff lying on it (cards, mana die...)."""
    SIZE = QtCore.QSize(36, 50)
    
    def __init__(self, player):
        super().__init__()
        player.tacticChanged.connect(self.setTactic)
        self.setTactic(player.tactic)
        
    def sizeHint(self):
        return self.SIZE
    
    def setTactic(self, tactic):
        """Set the tactic displayed in this widget."""
        if not tactic.flipped:
            pixmap = toolTipPixmap = tactic.pixmap()
        else:
            toolTipPixmap = tactic.pixmap()
            pixmap = utils.getPixmap('mk/cards/tactics/{}_back.jpg'.format(tactic.roundType.name))
        
        # TODO: Implement tactic.manaDie and tactic.cardCount
            
        self.setToolTip(utils.html(toolTipPixmap) if toolTipPixmap is not None else None)
        self.setPixmap(utils.scalePixmap(pixmap, self.SIZE))
    

class CrystalsWidget(QtWidgets.QLabel):
    """Display the number of crystals of a certain color of a player."""
    SIZE = QtCore.QSize(40, 50)
    
    def __init__(self, player, color):
        super().__init__()
        self.player = player
        self.color = color
        player.crystalsChanged.connect(self._crystalsChanged)
        self._crystalsChanged() # initialize
        
        import random # TODO: remove
        self.setCount(random.randint(0,3))
    
    def sizeHint(self):
        return self.SIZE
    
    def setCount(self, number):
        """Set the number displayed in this widget. *number* must be between 0 and 3."""
        self.setPixmap(utils.getPixmap('mk/mana/mana_crystal_{}x{}.png'.format(self.color.name, number),
                                       self.SIZE))
        
    def _crystalsChanged(self):
        self.setCount(self.player.crystals[self.color])
        
        
class CardCountWidget(QtWidgets.QWidget):
    """Display the number of cards in the draw pile, hand and discard pile of a player."""
    def __init__(self, player):
        super().__init__()
        self.player = player
        layout = QtWidgets.QHBoxLayout(self)
        
        toolTip = self.tr("Draw pile")
        label = QtWidgets.QLabel()
        label.setPixmap(utils.getPixmap('mk/draw_pile.png'))
        label.setToolTip(toolTip)
        layout.addWidget(label)
        self.drawPileLabel = QtWidgets.QLabel()
        self.drawPileLabel.setToolTip(toolTip)
        layout.addWidget(self.drawPileLabel)
        
        toolTip = self.tr("Hand cards")
        label = QtWidgets.QLabel()
        label.setPixmap(utils.getPixmap('mk/hand_cards.png'))
        label.setToolTip(toolTip)
        layout.addWidget(label)
        self.handCardLabel = QtWidgets.QLabel()
        self.handCardLabel.setToolTip(toolTip)
        layout.addWidget(self.handCardLabel)
        
        toolTip = self.tr("Discard pile")
        label = QtWidgets.QLabel()
        label.setPixmap(utils.getPixmap('mk/discard_pile.png'))
        label.setToolTip(toolTip)
        layout.addWidget(label)
        self.discardPileLabel = QtWidgets.QLabel()
        self.discardPileLabel.setToolTip(toolTip)
        layout.addWidget(self.discardPileLabel)
        
        player.cardCountChanged.connect(self._cardCountChanged)
        self._cardCountChanged() # initialize
        
    def _cardCountChanged(self):
        self.drawPileLabel.setText(str(self.player.drawPileCount))
        self.handCardLabel.setText(str(self.player.handCardCount))
        self.discardPileLabel.setText(str(self.player.discardPileCount))
        
    
class PointsWidget(QtWidgets.QWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        layout = QtWidgets.QHBoxLayout(self)
        
        toolTip = self.tr("Move points")
        label = QtWidgets.QLabel()
        label.setPixmap(utils.getPixmap('mk/movement.png', QtCore.QSize(20, 20)))
        label.setToolTip(toolTip)
        layout.addWidget(label)
        self.movementLabel = QtWidgets.QLabel()
        self.movementLabel.setToolTip(toolTip)
        layout.addWidget(self.movementLabel)
        
        toolTip = self.tr("Influence points")
        label = QtWidgets.QLabel()
        label.setPixmap(utils.getPixmap('mk/influence.png', QtCore.QSize(20, 20)))
        label.setToolTip(toolTip)
        layout.addWidget(label)
        self.influenceLabel = QtWidgets.QLabel()
        self.influenceLabel.setToolTip(toolTip)
        layout.addWidget(self.influenceLabel)
        
        player.pointsChanged.connect(self._pointsChanged)
        self._pointsChanged() # initialize
    
    def _pointsChanged(self):
        self.movementLabel.setText(str(self.player.movePoints))
        self.influenceLabel.setText(str(self.player.influencePoints))
        