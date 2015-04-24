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
from mageknight.data import * # @UnusedWildImport
        

class BaseCombat(QtCore.QObject):
    combatStarted = QtCore.pyqtSignal()
    enemiesChanged = QtCore.pyqtSignal()
    
    def __init__(self, match):
        super().__init__()
        self.match = match
        self.effectsPlayed = False
        self.enemies = []
        
    def setEnemies(self, enemies):
        self.match.stack.push(stack.Call(self._setEnemies, enemies),
                              stack.Call(self._setEnemies, self.enemies))
        
    def _setEnemies(self, enemies):
        self.enemies = enemies
        self.enemiesChanged.emit()
    
    def hasSelectedEnemy(self):
        return any(enemy.isSelected for enemy in self.enemies)
        
    def selectedEnemies(self):
        return [enemy for enemy in self.enemies if enemy.isSelected]
                
    def setEffectsPlayed(self, effectsPlayed):
        if effectsPlayed != self.effectsPlayed:
            self.match.stack.push(stack.Call(self._setEffectsPlayed, effectsPlayed),
                                  stack.Call(self._setEffectsPlayed, self.effectsPlayed))
    
    def _setEffectsPlayed(self, effectsPlayed):
        self.effectsPlayed = effectsPlayed
        
    def setEnemySelected(self, enemy, selected):
        if selected != enemy.isSelected:
            self.match.stack.push(stack.Call(self._setEnemySelected, enemy, selected),
                                  stack.Call(self._setEnemySelected, enemy, not selected))

    def _setEnemySelected(self, enemy, selected):
        enemy.isSelected = selected
        self.enemiesChanged.emit()
            
    def clearSelection(self):
        self.match.stack.push(stack.Call(self._setSelection, []),
                              stack.Call(self._setSelection, self.selectedEnemies()))
                              
    def _setSelection(self, enemies):
        for enemy in self.enemies:
            enemy.isSelected = enemy in enemies
        self.enemiesChanged.emit()
        
    def killEnemies(self, enemies):
        self.match.stack.push(stack.Call(self._setEnemiesAlive, enemies, False),
                              stack.Call(self._setEnemiesAlive, enemies, True))
        
    def _setEnemiesAlive(self, enemies, alive):
        for enemy in enemies:
            assert enemy.isAlive != alive # otherwise undoing killEnemies will lead to problems
            enemy.isAlive = alive
        self.enemiesChanged.emit()
        
    def blockEnemy(self, enemy):
        self.match.stack.push(stack.Call(self._setEnemyBlocked, enemy, True),
                              stack.Call(self._setEnemyBlocked, enemy, False))
        
    def _setEnemyBlocked(self, enemy, isBlocked):
        if isBlocked != enemy.isBlocked:
            enemy.isBlocked = isBlocked
            self.enemiesChanged.emit()
        
    def setDamage(self, enemy, damage):
        self.match.stack.push(stack.Call(self._setDamage, enemy, damage),
                              stack.Call(self._setDamage, enemy, enemy.damage))
    
    def _setDamage(self, enemy, damage):
        if damage != enemy.damage:
            enemy.damage = damage
            self.enemiesChanged.emit()
            
    def setUnitProtected(self, unit, protected):
        if protected != unit.isProtected:
            self.match.stack.push(stack.Call(self._setUnitProtected, unit, protected),
                                  stack.Call(self._setUnitProtected, unit, not protected))
        
    def _setUnitProtected(self, unit, protected):
        unit.isProtected = protected
        