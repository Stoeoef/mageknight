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

mainWindow = None # mainWindow instance

class MainWindow(QtWidgets.QWidget):
    """Main window of the application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Mage Knight"))
        global mainWindow
        mainWindow = self
        
        self.viewActions = [ToggleViewAction(self, view, title) for view, title in self.availableViews()]
        self._views = {}
        
        from mageknight import core, client
        from mageknight.data import Hero
        players = [core.Player('Nameless Player', Hero.Norowas)]
        self.match = core.Match(players)
        self.client = client.LocalMatchClient(self.match, players[0])
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.setSpacing(0)
        leftLayout.setContentsMargins(0,0,0,0)
        layout.addLayout(leftLayout, 1)
        
        from mageknight.gui import topbar, mapview, playerarea, playerstatus, effectlist, actionlist
        self.topBar = topbar.TopBar(self.client)
        leftLayout.addWidget(self.topBar)
        
        centerLayout = QtWidgets.QHBoxLayout()
        leftLayout.addLayout(centerLayout, 1)
        self.mapView = mapview.MapView(self, self.client)
        centerLayout.addWidget(self.mapView, 1)
        
        rightLayout = QtWidgets.QVBoxLayout()
        centerLayout.addLayout(rightLayout)
        
        self.actionList = actionlist.ActionList(self.client)
        rightLayout.addWidget(self.actionList)
        
        self.effectList = effectlist.EffectList(self.client)
        rightLayout.addWidget(self.effectList)
        
        self.playerArea = playerarea.PlayerArea(self.client, players[0])
        leftLayout.addWidget(self.playerArea)
        
        self.playerColumn = playerstatus.PlayerColumn(self.client)
        layout.addWidget(self.playerColumn)
        
        self.resize(1000, 700)
        
        # Show combat view automatically if combat starts
        self.match.combat.combatStarted.connect(lambda: self.showView('combat'))
        
        
        # TODO: remove debugging stuff
        from mageknight.core import units
        self.match.currentPlayer.addUnit(units.get('foresters'))
            
        #QtCore.QTimer.singleShot(0, lambda: self.showView('combat'))
        #from mageknight.data import enemies
        #self.match.combat.begin([enemies.get('prowlers'), enemies.get('medusa')])
        
    def availableViews(self):
        """Return a list of (view id, view title)-tuples for all available views. Views are popup windows
        offer additional game information (e.g. the fame board)."""
        return [
            ('combat', self.tr("Combat")),
            ('shop', self.tr("Shop")),
            ('fame', self.tr("Fame board")),
            ('terrain', self.tr("Terrain")),
            ('cards', self.tr("Cards")),
        ]
        
    def getView(self, viewId):
        """Return the view with the given id. Create it when it is first requested.
        Known ids are:
            - fame: The fame/reputation board
        """
        if viewId not in self._views:
            if viewId == 'combat':
                from mageknight.gui import combatview
                self._views[viewId] = combatview.CombatView(self, self.client)
            elif viewId == 'shop':
                from mageknight.gui import shop
                self._views[viewId] = shop.ShopView(self, self.client)
            elif viewId == 'fame':
                from mageknight.gui import fameview
                self._views[viewId] = fameview.FameView(self, self.client)
            elif viewId == 'terrain':
                from mageknight.gui import terraincostsview
                self._views[viewId] = terraincostsview.TerrainCostsView(self, self.client)
            elif viewId == 'cards':
                from mageknight.gui import cardsview
                self._views[viewId] = cardsview.CardsView(self)
            else:
                raise ValueError("Invalid view id: '{}'".format(viewId))
        return self._views[viewId]

    def showView(self, viewId):
        self.setViewVisible(viewId, True)
        
    def setViewVisible(self, viewId, visible):
        for action in self.viewActions:
            if action.viewId == viewId:
                action.setChecked(visible)
        
        
class ToggleViewAction(QtWidgets.QAction):
    """An action that is used to show/hide a view (see MainWindow.getView)."""
    def __init__(self, parent, viewId, title):
        super().__init__(parent)
        self.viewId = viewId
        self.setText(title)
        self.setCheckable(True)
        self.toggled.connect(self._triggered)
        self._connected = False
        
    def _triggered(self, checked):
        from mageknight.gui import mainwindow
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
