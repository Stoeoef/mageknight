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

from PyQt5 import QtCore

from mageknight.gui import dialogs
from mageknight.data import * # @UnusedWildImport
from . import effects, sites, assets
from mageknight.attributes import * # @UnusedWildImport
    

class EnemyInCombat:
    def __init__(self, enemy, site, isProvokable):
        self.enemy = enemy
        self.site = site
        self.effects = []
        self.isProvokable = isProvokable
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
        

class Combat(AttributeObject):
    combatStarted = QtCore.pyqtSignal()
    enemiesChanged = QtCore.pyqtSignal()
    rewardsChanged = QtCore.pyqtSignal()
    
    enemies = ListAttribute(EnemyInCombat, 
                            itemAttributes=[('isAlive', bool),
                                            ('isSelected', bool),
                                            ('isBlocked', bool),
                                            ('isProvokable', bool),
                                            ('damage', int)
                                           ])
    rewards = ListAttribute(CombatReward,
                            itemAttributes=[('count', int), 
                                            ('items', list)])
    effectsPlayed = BoolAttribute()
    currentReward = Attribute(CombatReward)
    woundsAssignedToHero = IntAttribute() # count wounds received in this combat (for knock out)
    
    def __init__(self, match):
        super().__init__(match.stack)
        self.match = match
        
    def hasSelectedEnemy(self):
        return any(enemy.isSelected for enemy in self.enemies)
        
    def selectedEnemies(self):
        return [enemy for enemy in self.enemies if enemy.isSelected]
            
    def clearSelection(self):
        for enemy in self.enemies:
            self.enemies.setIsSelected(enemy, False)

    def init(self, site=None, unitsAllowed=True, nightRules=False):
        """Initialize a combat. This sets the state to 'initCombat'. During this state (provokable) enemies
        may be added to the combat using 'addEnemies'. Finally, the combat must be started with 'start'.
        For the arguments see 'start'.
        """
        assert not self.match.state.inCombat
        # TODO: support unitsAllowed, nightRules
                    
        # Reset various stuff
        self.enemies = []
        self.rewards = []
        self.currentReward = None
        self.effectsPlayed = False
        self.woundsAssignedToHero = 0
        for unit in self.match.currentPlayer.units:
            self.match.currentPlayer.units.setIsProtected(unit, False)
        self.match.setState(State.initCombat)
        
        if site is not None:
            self.addEnemies(site)
        
    def addEnemies(self, site, provokable=False):
        assert self.match.state is State.initCombat
        enemies = [EnemyInCombat(enemy, site, provokable) for enemy in site.enemies]
        self.enemies.extend(enemies)
        
    def start(self, site=None, unitsAllowed=True, nightRules=False):
        """Start a combat.
            - site: If given, all enemies from this site will be added to the combat.
            - unitsAllowed: whether units take part 
            - nightRules: whether night rules apply during this combat (dungeon, tomb)
        """
        if self.match.state is not State.initCombat:
            self.init(site, unitsAllowed=unitsAllowed, nightRules=nightRules)
        # Note: if no enemies are provokable, this will skip to the next state automatically
        self.setState(State.provokeMarauders)
        self.combatStarted.emit()
        
    def setState(self, state):
        """Set the match state. During combat, use this instead of match.setState. This method will skip
        unnecessary states (e.g. skip to combatEnd, if all enemies are defeated).
        """ 
        self.clearSelection()
        self.effectsPlayed = False
        
        # Whenever a state is not needed for some reason, we skip to the next state instead
        if state is State.provokeMarauders and not any(e.isProvokable for e in self.enemies):
            state = State.rangeAttack
        if not any(enemy.isAlive for enemy in self.enemies):
            state = State.combatEnd
        if state is State.block and not any(enemy.isAttacking for enemy in self.enemies):
            state = State.attack
        if state is State.assignDamage and \
                not any(enemy.isAttacking and enemy.damage > 0 for enemy in self.enemies):
            state = State.attack
        
        self.match.setState(state)
        
        # State specific actions (typically we initialize the selection)
        if state is State.provokeMarauders:
            self.match.setState(state)
            for enemy in self.enemies:
                self.enemies.setIsSelected(enemy, not enemy.isProvokable)
            
        if self.match.state is not State.combatEnd:
            # If only one enemy is active, select it
            activeEnemies = [e for e in self.enemies if self.isEnemyActive(e)]
            if len(activeEnemies) == 1:
                self.enemies.setIsSelected(activeEnemies[0], True)
        else:
            sites = set()
            for enemy in self.enemies:
                sites.add(enemy.site)
            for site in sites:
                # Rewards will be added here
                site.onCombatEnd(self.match, self.match.currentPlayer)
            self.match.updateActions() # is often different after site.onCombatEnd
            
            # Reset various stuff
            for unit in self.match.currentPlayer.units:
                self.match.currentPlayer.units.setIsProtected(unit, False)
            self.enemies = []
            
    def checkEffectPlayable(self, effect=None, type=EffectType.unknown):
        self.effectsPlayed = True
        
        state = self.match.state
        assert state.inCombat
        
        if state in (State.provokeMarauders, State.assignDamage):
            raise InvalidAction("Cannot play any effects now.")
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
                    # Rules: marauding enemies are not fortified when fighting in a fortified site
                    if any(isinstance(enemy.site, sites.FortifiedSite) for enemy in self.selectedEnemies()):
                        fortificationLevel += 1
                        print([(e.site, e) for e in self.selectedEnemies()])
                    
                    if fortificationLevel == 2:
                        # Note: We cannot skip this combat state even if enemies are twice fortified,
                        # because the user might play an "Enemy loses fortifications" effect.
                        raise InvalidAction("Enemies are twice fortified.")
                    elif fortificationLevel == 1 and effect.range != AttackRange.siege:
                            raise InvalidAction("Enemies are fortified. Must play siege attack.")

                elif state != State.attack:
                    raise InvalidAction("Cannot play attack points now")
    
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
        if self.match.state is State.provokeMarauders and not select and not enemy.isProvokable:
            raise InvalidAction("This enemy must take part.")
                
        if select and self.match.state in [State.block, State.assignDamage]:
            # only one enemy can be targeted in these phases. Thus: deselect all others
            for e in self.enemies:
                self.enemies.setIsSelected(e, e == enemy)
        else:
            self.enemies.setIsSelected(enemy, select)
        
    def next(self):
        state = self.match.state
        if not state.inCombat:
            raise InvalidAction("Cannot go to next combat state now.")
        if not self.hasSelectedEnemy():
            raise InvalidAction("Must select an enemy first.")
        if state == State.provokeMarauders:
            self.enemies = [e for e in self.enemies if e.isSelected]
            self.setState(State.rangeAttack)
            return
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
        for enemy in enemies:
            self.enemies.remove(enemy)
            enemy.site.onEnemyKilled(self.match, self.match.currentPlayer, enemy.enemy)
            
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
            self.enemies.setIsBlocked(enemy, True)
            
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
        self.woundsAssignedToHero += woundCount
        if enemy.poison:
            player.addWounds(woundCount, toDiscardPile=True)
        if enemy.paralyze or self.woundsAssignedToHero >= self.match.currentPlayer.cardLimit:
            player.knockOut()
        self.enemies.setDamage(enemy, 0)
        
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
        self.enemies.setDamage(enemy, damage)
        self.match.currentPlayer.units.setIsProtected(unit, True) # cannot assign damage to this unit again
        
        if damage == 0: # otherwise let the user assign damage to another unit or press "next"
            self.next()
            
    def chooseRewardType(self, reward):
        assert reward in self.rewards
        if self.currentReward is not None:
            raise InvalidAction("Choose your reward first.")
        
        if reward.type is CombatRewardType.crystal:
            for _ in range(reward.count):
                color = Mana.random()
                self.rewards.addItems(reward, [color])
                if color is Mana.black:
                    self.match.currentPlayer.addFame(1)
                    continue
                while color is Mana.gold:
                    color = dialogs.chooseManaColor(default=Mana.gold) # query as long as necessary...
                self.match.currentPlayer.addCrystal(color)
            self.rewards.remove(reward)
            if len(self.rewards) == 0:
                self.match.setState(State.endOfTurn)
            self.match.revealNewInformation()
        
        elif reward.type is CombatRewardType.artifact:
            # rules: choose n artifacts from n+1
            self.currentReward = reward
            self.rewards.addItems(reward, self.match.shop.takeArtifacts(reward.count + 1))
        
        elif reward.type is CombatRewardType.unit:
            self.currendReward = reward
            self.rewards.addItems(reward, self.match.shop.units)
            
    def chooseRewardItem(self, reward, item):
        assert self.currentReward is not None
        
        if reward.type is CombatRewardType.unit:
            assert isinstance(item, assets.Unit)
            self.match._getUnit(self.match.currentPlayer, item, reward=True)
            
        else:
            self.match.currentPlayer.drawPile.append(item)
            # TODO: remove advanced actions, spells from offer
        
        self.rewards.removeItems(reward, [item])
        self.rewards.setCount(reward, reward.count-1)
        if reward.count <= 0:
            self.currentReward = None
            self.rewards.remove(reward)
        
        if len(self.rewards) == 0:
            self.match.setState(State.endOfTurn)
        