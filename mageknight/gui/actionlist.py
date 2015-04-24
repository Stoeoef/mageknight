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
# 

import functools

from PyQt5 import QtWidgets


class ActionList(QtWidgets.QWidget):
    def __init__(self, match):
        super().__init__()
        self.match = match
        self.match.actions.changed.connect(self._update)
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self._update()
        
    def _update(self):
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i)
            self.layout.removeWidget(widget)
            widget.setParent(None)
            
        for action in self.match.actions:
            button = QtWidgets.QPushButton(action.title)
            button.clicked.connect(functools.partial(self.match.activateAction, action.id))
            self.layout.addWidget(button)