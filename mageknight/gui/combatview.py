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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from mageknight.data import CombatState
from mageknight import utils
from mageknight.gui import stock, misc


class CombatView(QtWidgets.QDialog):
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Combat"))
        layout = QtWidgets.QVBoxLayout(self)
        scene = CombatScene(self, match)
        view = QtWidgets.QGraphicsView(scene)
        view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(view)
        
        
class CombatScene(QtWidgets.QGraphicsScene):
    drawSelection = True
    
    def __init__(self, parent, match):
        super().__init__(parent)
        self.setBackgroundBrush(QtGui.QBrush(Qt.darkGray))
        self.match = match
        self.combat = match.combat
        self.match.combat.stateChanged.connect(self._refresh)
        
        fm = QtGui.QFontMetrics(self.font())
        group = misc.VerticalGroup(alignment=Qt.AlignLeft)
        self.addItem(group)
        
        self.title1 = misc.Title()
        group.addItem(self.title1)
        self.enemies = stock.Stock(EnemyItem.size(fm))
        group.addItem(self.enemies)
        self.title2 = misc.Title()
        group.addItem(self.title2)
            
        # Button bar
        buttonBar = QtWidgets.QGraphicsWidget()
        layout = QtWidgets.QGraphicsLinearLayout(Qt.Horizontal, buttonBar)
        self.okButton = QtWidgets.QPushButton(self.tr("Ok"))
        self.okButton.clicked.connect(lambda: self.match.combatNext()) # does not work without lambda!
        self.skipButton = QtWidgets.QPushButton(self.tr("Skip"))
        self.skipButton.clicked.connect(lambda: self.match.combatSkip()) # same
        for button in self.okButton, self.skipButton:
            proxy = QtWidgets.QGraphicsProxyWidget()
            proxy.setWidget(button)
            layout.addItem(proxy)
        group.addItem(buttonBar)
        layout.activate() # otherwise the following item will be positioned on top of the buttons
        
        self.stock = stock.Stock(EnemyItem.size(fm))
        group.addItem(self.stock)
        self.combat.enemiesChanged.connect(self._refresh)
        
        self._refresh()
        
    def _refresh(self):
        self._updateTitles()
        self._updateEnemies()
        self._updateButtons()
        
    def _updateTitles(self):
        state = self.combat.state
        if state == CombatState.rangeAttack:
            self.title1.setText(self.tr("1. Ranged/siege attack phase"))
            selected = self.combat.selectedEnemies()
            if len(selected) == 0:
                self.title2.setText(self.tr("Choose enemies"))
            else: self.title2.setText(self.tr("Play attack"))

        elif state == CombatState.block:
            self.title1.setText(self.tr("2. Block phase"))
            selected = self.combat.selectedEnemies()
            if len(selected) == 0:
                self.title2.setText(self.tr("Choose enemy"))
            else: self.title2.setText(self.tr("Play block"))
            
        elif state == CombatState.assignDamage:
            self.title1.setText(self.tr("3. Assign damage phase"))
            selected = self.combat.selectedEnemies()
            if len(selected) == 0:
                self.title2.setText(self.tr("Choose enemy"))
            else:
                damage = self.combat.selectedEnemies()[0].damage
                self.title2.setText(self.tr("Assign {} damage").format(damage))
            
        elif state == CombatState.attack:
            self.title1.setText(self.tr("4. Attack phase"))
            selected = self.combat.selectedEnemies()
            if len(selected) == 0:
                self.title2.setText(self.tr("Choose enemies"))
            else: self.title2.setText(self.tr("Play attack"))
            
        else:
            self.title1.setText(self.tr("No combat"))
            self.title2.setText('')
            
    def _updateEnemies(self):
        state = self.combat.state
        if state in [CombatState.noCombat, CombatState.end]:
            self.enemies.clear()
            self.stock.clear()
        else:
            self.enemies.sync(EnemyItem, self.match.combat.enemies)
            if state == CombatState.assignDamage:
                from . import playerarea
                self.stock.sync(playerarea.UnitItem, self.match.currentPlayer.units)
            else:
                self.stock.clear()

        for item in self.enemies.items():
            if state in [CombatState.rangeAttack, CombatState.attack]:
                item.setGray(not item.enemy.isAlive)
            elif state == CombatState.block:
                item.setGray(not item.enemy.isAttacking)
            elif state == CombatState.assignDamage:
                item.setGray(not item.enemy.isAttacking or item.enemy.damage == 0)
                
    def _updateButtons(self):
        state = self.combat.state
        if state in [CombatState.noCombat, CombatState.end]:
            self.okButton.setVisible(False)
            self.skipButton.setVisible(False)
        else:
            self.okButton.setVisible(True)
            if state != CombatState.assignDamage:
                self.okButton.setText(self.tr("Ok"))
                self.skipButton.setVisible(True)
            else:
                self.okButton.setText("Assign damage to hero")
                self.skipButton.setVisible(False)
        
    def enemyClicked(self, enemy):
        self.match.setEnemySelected(enemy, not enemy.isSelected)
        
    def unitClicked(self, unit, action):
        self.match.assignDamageToUnit(unit)
        
    def buttonClicked(self, buttonId):
        if buttonId == 'ok':
            self.match.combatNext()
        elif buttonId == 'skip':
            self.match.combatSkip()

    
class EnemyItem(QtWidgets.QGraphicsObject):
    # this is the max width of the text and the max width of the pixmap
    # real size depends on font settings (see boundingRect) 
    SIZE = QtCore.QSize(100, 85) 
    SPACING = 5
    WIDTH = 110 # should be SIZE + 2*SPACING
    MAX_ROWS = 3
    _pixmaps = {}
    _grayPixmaps = {}
    
    def __init__(self, enemy, size):
        super().__init__()
        self.enemy = enemy
        self.gray = False
        lines = [utils.html(enemy.pixmap())] + [str(effect) for effect in enemy.effects]
        self.setToolTip('<br />'.join(lines))
        
    @property
    def object(self):
        return self.enemy
    
    def setGray(self, gray):
        if gray != self.gray:
            self.gray = gray
            self.update()
    
    def _pixmap(self):
        theDict = self._pixmaps if not self.gray else self._grayPixmaps
        if self.enemy.enemy not in theDict:
            pixmap = self.enemy.enemy.pixmap(self.gray)
            theDict[self.enemy.enemy] = utils.scalePixmap(pixmap, self.SIZE)
        return theDict[self.enemy.enemy]
        
    @staticmethod
    def _sizeHelper(fm, pixmapHeight, rows):
        size = QtCore.QSizeF(EnemyItem.SIZE.width(), pixmapHeight)
        size.setWidth(size.width() + 2*EnemyItem.SPACING)
        size.setHeight(size.height() + 2*EnemyItem.SPACING)
        if rows > 0:
            size.setHeight(size.height() + EnemyItem.SPACING + rows * fm.lineSpacing())
        return size
    
    @staticmethod
    def size(fm):
        return EnemyItem._sizeHelper(fm, EnemyItem.SIZE.height(), EnemyItem.MAX_ROWS).toSize()
        
    def boundingRect(self):
        fm = QtGui.QFontMetrics(self.scene().font())
        pixmapHeight = self._pixmap().height()
        rows = min(len(self.enemy.effects), self.MAX_ROWS)
        return QtCore.QRectF(QtCore.QPointF(0, 0), EnemyItem._sizeHelper(fm, pixmapHeight, rows))
    
    def paint(self, painter, option, widget):
#         if self.enemy.isSelected and self.scene().drawSelection:
#             painter.save()
#             pen = painter.pen()
#             pen.setColor(utils.color("3c87c7"))
#             painter.setPen(pen)
#             painter.setBrush(utils.color("c3eefa"))
#             painter.drawRoundedRect(self.boundingRect(), 5, 5)
#             painter.restore()
#         
#         painter.translate(self.SPACING, self.SPACING)
        
        width = self.SIZE.width()
        fm = painter.fontMetrics()
        
        # draw pixmap
        pixmap = self._pixmap()
        if not self.enemy.isSelected:
            painter.setOpacity(0.5)
        painter.drawPixmap((width - pixmap.width()) / 2, 0, pixmap)
        painter.setOpacity(1)
        
        if len(self.enemy.effects) > 0:
            if len(self.enemy.effects) <= self.MAX_ROWS:
                effects = self.enemy.effects
            else:
                effects = self.enemy.effects[:self.MAX_ROWS-1] + ['...']
            # draw effects background
            y = pixmap.height() + self.SPACING
            height = len(effects) * fm.lineSpacing()
            painter.fillRect(0, y, width, height, Qt.white)
            
            # draw text
            for effect in effects:
                text = fm.elidedText(str(effect), Qt.ElideRight, width)
                painter.drawText(0, y, width, fm.height(), Qt.AlignCenter, text)
                y += fm.lineSpacing()
                
    def mousePressEvent(self, event):
        event.accept()
        
    def mouseReleaseEvent(self, event):
        self.scene().enemyClicked(self.enemy)
        event.accept()
    
        