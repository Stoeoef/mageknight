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

import math

from mageknight.data import * # @UnusedWildImport
from . import basecombat, effects, sites

    
class EnemyInCombat:
    def __init__(self, enemy):
        self.enemy = enemy
        self.effects = []
        self.isAlive = True
        self.isSelected = False
        self.isBlocked = False
        self.damage = enemy.attack.value
        if enemy.brutal:
            self.damage *= 2
        
    @property
    def isAttacking(self):
        return self.isAlive and not self.isBlocked # TODO: check self.effects for "enemy does not attack" 
        
    def __getattr__(self, attr):
        return getattr(self.enemy, attr)
        

class Combat(basecombat.BaseCombat):
    def begin(self, enemies):
        enemies = [EnemyInCombat(enemy) for enemy in enemies]
        self.setEnemies(enemies)
        self.match.updateActions()
        self.setState(State.rangeAttack)
        # TODO: reset other stuff?
        for unit in self.match.currentPlayer.units:
            self.setUnitProtected(unit, False)
        self.combatStarted.emit()
    
    def checkEffectPlayable(self, effect=None, type=EffectType.unknown):
        self.setEffectsPlayed(True)
        
        state = self.match.state
        assert state.inCombat
        site = self.match.map.siteAtPlayer(self.match.currentPlayer)
        
        if state is State.assignDamage:
            raise InvalidAction("Cannot play effects during assign damage phase.")
        else:
            if not self.hasSelectedEnemy():
                raise InvalidAction("Must select enemies first.")
        
        if effect is not None:
            type = effect.type
            
        if type in [EffectType.healing, EffectType.movement, EffectType.influence]:
            raise InvalidAction("Cannot play healing/movement/influence during combat.")
        
        if effect is not None: 
            if isinstance(effect, effects.BlockPoints):
                if state != State.block:
                    raise InvalidAction("Cannot play block points now")
            elif isinstance(effect, effects.AttackPoints):
                if state == State.rangeAttack:
                    if effect.range == AttackRange.normal:
                        raise InvalidAction("Can only play ranged/siege attack now")
                    fortificationLevel = 0
                    if any(enemy.fortified for enemy in self.selectedEnemies()):
                        fortificationLevel += 1
                    if site is not None and isinstance(site, sites.FortifiedSite) \
                            and any(enemy.enemy in site.enemies for enemy in self.selectedEnemies()):
                        # Rules: additionally provoked marauding enemies are not fortified
                        fortificationLevel += 1
                    
                    if fortificationLevel == 2:
                        # Note: We cannot skip this combat state if enemies are twice fortified,
                        # because the user might play an "Enemy loses fortifications" effect.
                        raise InvalidAction("Enemies are twice fortified.")
                    elif fortificationLevel == 1 and effect.range != AttackRange.siege:
                            raise InvalidAction("Enemies are fortified. Must play siege attack.")

                elif state != State.attack:
                    raise InvalidAction("Cannot play attack points now")
        
    def setState(self, state):
        self.clearSelection()
        self.setEffectsPlayed(False)
        
        # Skip states under certain circumstances
        if not any(enemy.isAlive for enemy in self.enemies):
            state = State.combatEnd
        if state == State.block and not any(enemy.isAttacking for enemy in self.enemies):
            state = State.attack
        if state == State.assignDamage and \
                not any(enemy.isAttacking and enemy.damage > 0 for enemy in self.enemies):
            state = State.attack
        
        self.match.setState(state)
        if self.match.state != State.combatEnd:
            # If only one enemy is active, select it
            activeEnemies = [e for e in self.enemies if self.isEnemyActive(e)]
            if len(activeEnemies) == 1:
                self.setEnemySelected(activeEnemies[0], True)
        else:
            # Combat end
            site = self.match.map.siteAtPlayer(self.match.currentPlayer)
            if site is not None: # note: self.remainingEnemies must still work here
                site.onCombatEnd(self.match, self.match.currentPlayer)
            self.setEnemies([])
    
    def remainingEnemies(self):
        return [enemy.enemy for enemy in self.enemies if enemy.isAlive]
    
    def isEnemyActive(self, enemy):
        """Return whether the given enemy can be targeted in the current phase
        (e.g. alive and not blocked yet)."""
        if not enemy.isAlive:
            return False
        if self.match.state == State.block:
            return not enemy.isBlocked
        if self.match.state == State.assignDamage:
            return enemy.isAttacking and enemy.damage > 0
        return True
        
    def setEnemySelected(self, enemy, select):
        if not self.match.state.inCombat:
            raise InvalidAction("Cannot select/deselect an enemy currently.")
        if self.effectsPlayed:
            raise InvalidAction("Cannot change enemy selection after playing effects.")
        if select and not self.isEnemyActive(enemy):
            raise InvalidAction("Cannot select this enemy.")
                
        if select and self.match.state in [State.block, State.assignDamage]:
            # only one enemy can be targeted in these phases. Thus: deselect all others
            for e in self.enemies:
                super().setEnemySelected(e, e == enemy)
        else:
            super().setEnemySelected(enemy, select)
        
    def next(self):
        state = self.match.state
        if not state.inCombat:
            raise InvalidAction("Cannot go to next combat state now.")
        if not self.hasSelectedEnemy():
            raise InvalidAction("Must select an enemy first.")
        if state == State.rangeAttack:
            self.resolveAttack(ranged=True)
        elif state == State.block:
            self.resolveBlock()
        elif state == State.assignDamage:
            self.assignDamageToHero()
        elif state == State.attack:
            self.resolveAttack()
        # reenter the state (will skip to the next state if e.g. all enemies are dead)
        self.setState(state) 
        
    def skip(self):
        state = self.match.state
        if state == State.rangeAttack:
            self.setState(State.block)
        elif state == State.block:
            self.setState(State.assignDamage)
        elif state == State.attack:
            self.setState(State.combatEnd)
        else:
            raise InvalidAction("Cannot skip to next combat state now.")
        
    def resolveAttack(self, ranged=False):
        armor = 0
        resistances = set()
        for enemy in self.selectedEnemies():
            # Rules: cold fire block is only inefficient if a single enemy has both fire and ice resistance
            resistances.update(enemy.resistances)
            armor += enemy.armor
        
        efficientPoints = 0
        inefficientPoints = 0
        attacks = self.match.effects.findEffects(effects.AttackPoints)
        for effect in attacks:
            # note: in checkEffectPlayable we made sure only ranged/siege attacks were played
            if effect.element in resistances:
                inefficientPoints += effect.points
            else: efficientPoints += effect.points
            self.match.effects.remove(effect)
            
        points = efficientPoints + inefficientPoints // 2
        if points >= armor:
            self.killEnemies(self.selectedEnemies())
            
    def killEnemies(self, enemies):
        super().killEnemies(enemies)
        self.match.currentPlayer.addFame(sum(e.fame for e in enemies)) # TODO: halve in certain cases
            
    def resolveBlock(self):
        # TODO: Handle summoners
        assert len(self.selectedEnemies()) == 1
        enemy = self.selectedEnemies()[0]
        if enemy.attack.element == Element.physical:
            effectiveBlocks = list(Element)
        elif enemy.attack.element == Element.fire:
            effectiveBlocks = [Element.ice, Element.coldFire]
        elif enemy.attack.element == Element.ice:
            effectiveBlocks = [Element.fire, Element.coldFire]
        else:
            effectiveBlocks = [Element.coldFire]
        
        efficientPoints = 0
        inefficientPoints = 0
        blocks = self.match.effects.findEffects(effects.BlockPoints)
        for effect in blocks:
            if effect.element in effectiveBlocks:
                efficientPoints += effect.points
            else: inefficientPoints += effect.points
            self.match.effects.remove(effect)
            
        necessaryPoints = enemy.attack.value
        if enemy.swift:
            necessaryPoints *= 2
            
        if efficientPoints + inefficientPoints // 2 >= necessaryPoints:
            self.blockEnemy(enemy)
            
    def assignDamageToHero(self):
        if self.match.state != State.assignDamage:
            raise InvalidAction("Cannot assign damage in this state.")
        assert len(self.selectedEnemies()) == 1
        enemy = self.selectedEnemies()[0]
        player = self.match.currentPlayer
        if enemy.damage == 0:
            return
        
        woundCount = math.ceil(enemy.damage / player.armor)
        player.addWounds(woundCount)
        if enemy.poison:
            player.addWounds(woundCount, toDiscardPile=True)
        if enemy.paralyze:
            player.knockOut()
        self.setDamage(enemy, 0)
        
    def assignDamageToUnit(self, unit):
        if self.match.state != State.assignDamage:
            raise InvalidAction("Cannot assign damage in this state.")
        if not self.hasSelectedEnemy():
            raise InvalidAction("Must select an enemy first.")
        if unit.isWounded or unit.isProtected:
            raise InvalidAction("Cannot assign damage to this unit.")
        
        enemy = self.selectedEnemies()[0]
        damage = enemy.damage
        assert damage > 0
        if enemy.attack.element in unit.resistances:
            damage = max(0, damage - unit.armor)
        if damage > 0:
            if not enemy.paralyze:
                self.match.currentPlayer.woundUnit(unit, wounds=1 if not enemy.poison else 2)
            else: self.match.currentPlayer.removeUnit(unit)
            damage = max(0, damage - unit.armor)
        self.setDamage(enemy, damage)
        self.setUnitProtected(unit, True) # cannot assign damage to this unit again
        
        if damage == 0: # otherwise let the user assign damage to another unit or press "next"
            self.next()
            