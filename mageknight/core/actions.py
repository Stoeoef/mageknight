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

from PyQt5 import QtCore

from mageknight import stack


class Action:
    def __init__(self, id, title):
        self.id = id
        self.title = title
        
        
class ActionList(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    
    def __init__(self, match):
        super().__init__()
        self.match = match
        self._list = []
        
    def __iter__(self):
        return iter(self._list)
    
    def __len__(self):
        return len(self._list)
    
    def __contains__(self, item):
        return item in self._list
    
    def __getitem__(self, index):
        return self._list[index]
    
    def add(self, id, title):
        if id in (action.id for action in self._list):
            return
        i = 0
        while i < len(self._list) and self._list[i].title < title:
            i += 1
        action = Action(id, title)
        self.match.stack.push(stack.Call(self._insert, i, action),
                              stack.Call(self._remove, action))
    
    def remove(self, action):
        index = self._list.index(action)
        self.match.stack.push(stack.Call(self._remove, action),
                              stack.Call(self._insert, index, action))
        
    def _insert(self, index, action):
        self._list.insert(index, action)
        self.changed.emit()
        
    def _remove(self, action):
        self._list.remove(action)
        self.changed.emit()
        
    