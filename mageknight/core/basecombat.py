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
    rewardsChanged = QtCore.pyqtSignal()
    
    def __init__(self, match):
        super().__init__()
        self.match = match
        self.enemies = []
        self.effectsPlayed = False
        self.rewards = []
        self.currentReward = None

    def setEnemies(self, enemies):
        self.match.stack.push(stack.Call(self._setEnemies, enemies),
                              stack.Call(self._setEnemies, self.enemies))
        
    def _setEnemies(self, enemies):
        self.enemies = enemies
        self.enemiesChanged.emit()
        
    def addEnemies(self, enemies):
        self.setEnemies(self.enemies + enemies)
        
    def _find(self, enemy):
        assert isinstance(enemy, Enemy) # not EnemyInCombat
        for enemyInCombat in self.enemies:
            if enemyInCombat.enemy == enemy:
                return enemyInCombat
        else: raise ValueError("Enemy '{}' is not part of this combat".format(enemy))
        
    def setEnemiesProvokable(self, enemies, isProvokable):
        enemies = [e for e in enemies if e.isProvokable != isProvokable]
        if len(enemies) > 0:
            self.match.stack.push(stack.Call(self._setEnemiesProvokable, enemies, isProvokable),
                                  stack.Call(self._setEnemiesProvokable, enemies, not isProvokable))
    
    def _setEnemiesProvokable(self, enemies, isProvokable):
        for enemy in enemies:
            enemy.isProvokable = isProvokable
        
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
        enemies = [e for e in enemies if e.isAlive]
        if len(enemies) > 0:
            self.match.stack.push(stack.Call(self._setEnemiesAlive, enemies, False),
                                  stack.Call(self._setEnemiesAlive, enemies, True))
        
    def _setEnemiesAlive(self, enemies, alive):
        for enemy in enemies:
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
                
    def setRewards(self, rewards):
        self.match.stack.push(stack.Call(self._setRewards, rewards),
                              stack.Call(self._setRewards, self.rewards))
        
    def _setRewards(self, rewards):
        self.rewards = rewards
        self.rewardsChanged.emit()
        
    def addReward(self, reward):
        self.setRewards(self.rewards + [reward])
        
    def removeReward(self, reward):
        rewards = [r for r in self.rewards if r != reward]
        self._setRewards(rewards)
        
    def addRewardItems(self, reward, items):
        newItems = reward.items + items if reward.items is not None else list(items)
        self.match.stack.push(stack.Call(self._setRewardItems, reward, newItems),
                              stack.Call(self._setRewardItems, reward, reward.items))
    
    def removeRewardItem(self, reward, item):
        newItems = [it for it in reward.items if it != item]
        self.match.stack.push(stack.Call(self._setRewardItems, reward, newItems),
                              stack.Call(self._setRewardItems, reward, reward.items))
        
    def _setRewardItems(self, reward, items):
        reward.items = items
        self.rewardsChanged.emit()
        
    def setCurrentReward(self, reward):
        assert reward is None or reward in self.rewards
        self.match.stack.push(stack.Call(self._setCurrentReward, reward),
                              stack.Call(self._setCurrentReward, self.currentReward))
    
    def _setCurrentReward(self, reward):
        self.currentReward = reward
        self.rewardsChanged.emit()
        
    def setRewardCount(self, reward, count):
        self.match.stack.push(stack.Call(self._setRewardCount, reward, count),
                              stack.Call(self._setRewardCount, reward, reward.count))
        
    def _setRewardCount(self, reward, count):
        reward.count = count
        self.rewardsChanged.emit()
        
        
        