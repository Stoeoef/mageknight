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

from PyQt5 import QtCore
translate = QtCore.QCoreApplication.translate

from mageknight.data import * # @UnusedWildImport
from mageknight.core import effects
from mageknight.core.assets import BasicAction, ActionCard
from mageknight.gui import dialogs



class BattleVersatility(BasicAction):
    name = 'battle_versatility'
    title = translate('cards', 'Battle Versatility')
    color = Mana.red
    effectType = EffectType.combat
    
    def basicEffect(self, match, player):
        options = [effects.AttackPoints(2),
                   effects.BlockPoints(2),
                   effects.AttackPoints(1, range=AttackRange.range)
                  ]
        effect = dialogs.choose(options)
        match.effects.add(effect)
    
    def strongEffect(self, match, player):
        options = [effects.AttackPoints(4),
                   effects.BlockPoints(4),
                   effects.AttackPoints(3, element=Element.fire),
                   effects.BlockPoints(3, element=Element.fire),
                   effects.AttackPoints(3, range=AttackRange.range),
                   effects.AttackPoints(2, range=AttackRange.siege)
                  ]
        effect = dialogs.choose(options)
        match.effects.add(effect)


class ColdToughness(BasicAction):
    name = 'cold_toughness'
    title = translate('cards', 'Cold Toughness')
    color = Mana.blue
    effectType = EffectType.combat
    
    def basicEffect(self, match, player):
        options = [effects.AttackPoints(2, element=Element.ice),
                   effects.BlockPoints(3, element=Element.ice),
                  ]
        effect = dialogs.choose(options)
        match.effects.add(effect)
    
    def strongEffect(self, match, player):
        assert len(match.combat.selectedEnemies()) == 1
        enemy = match.combat.selectedEnemies()[0] # TODO: redirect for summoners?
        
        points = 5
        for ability in 'fortified', 'brutal', 'swift', 'paralyze', 'poison':
            if getattr(enemy, ability):
                points += 1
                
        if enemy.attack.element in [Element.ice, Element.fire]:
            points += 1
        elif enemy.attack == Element.coldFire:
            points += 2
            
        # 'points += len(enemy.resistances)' does not work correctly if enemy has cold fire resistance
        for element in [Element.physical, Element.ice, Element.fire]:
            if element in enemy.resistances:
                points += 1
                
        match.effects.add(effects.BlockPoints(points, element=Element.ice))
        

class Concentration(BasicAction):
    name = 'concentration'
    title = translate('cards', 'Concentration')
    color = Mana.green
    effectType = EffectType.special
    
    def basicEffect(self, match, player):
        color = dialogs.chooseManaColor(fromList=[Mana.blue, Mana.white, Mana.red])
        match.effects.add(effects.ManaTokens(color))
        
    def strongEffect(self, match, player):
        self._strongEffect(match, player, 2)
    
    # This method is also used for Will Focus
    def _strongEffect(self, match, player, amount):
        concentration = effects.Concentration(amount)
        match.effects.add(concentration)
        card = dialogs.chooseCard(player, type=ActionCard)
        player.handCards.remove(card)
        card.strongEffect(match, player)
        match.effects.remove(concentration)
        
    
class Crystallize(BasicAction):
    name = 'crystallize'
    title = translate('cards', 'Crystallize')
    color = Mana.blue
    effectType = EffectType.special
    
    def basicEffect(self, match, player):
        color = dialogs.chooseManaColor(match, available=True)
        match.payMana(color)
        player.addCrystal(color)
        
    def strongEffect(self, match, player):
        color = dialogs.chooseManaColor(match, available=False)
        player.addCrystal(color)
        
    
class Determination(BasicAction):
    name = 'determination'
    title = translate('cards', 'Determination')
    color = Mana.blue
    effectType = EffectType.combat
    
    def basicEffect(self, match, player):
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
    
    def strongEffect(self, match, player):
        match.effects.add(effects.BlockPoints(5))
    
    
class Improvisation(BasicAction):
    name = 'improvisation'
    title = translate('cards', 'Improvisation')
    color = Mana.red
    effectType = EffectType.unknown
    
    def _effect(self, match, player, amount):
        card = dialogs.chooseCard(player)
        player.handCards.remove(card)
        options = [effects.MovePoints(amount),
                   effects.InfluencePoints(amount),
                   effects.AttackPoints(amount),
                   effects.BlockPoints(amount)
                  ]
        match.effects.add(dialogs.choose(options))
        
    def basicEffect(self, match, player):
        self._effect(match, player, 3)
        
    def strongEffect(self, match, player):
        self._effect(match, player, 5)
    

class ManaDraw(BasicAction):
    name = 'mana_draw'
    title = translate('cards', 'Mana Draw')
    color = Mana.white
    effectType = EffectType.special
    
    def basicEffect(self, match, player):
        match.source.limit += 1
        
    def strongEffect(self, match, player):
        if len(match.source) == 0:
            raise InvalidAction('No die in source.')
        oldColor = dialogs.chooseManaColor(fromList=match.source)
        newColor = dialogs.chooseManaColor(fromList=[Mana.red, Mana.blue, Mana.green, Mana.white, Mana.black])
        match.source.remove(oldColor)
        match.effects.add(effects.ManaTokens({newColor: 2}))
 
    
class March(BasicAction):
    name = 'march'
    title = translate('cards', 'March')
    color = Mana.green
    effectType = EffectType.movement
    
    def basicEffect(self, match, player):
        match.effects.add(effects.MovePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.MovePoints(4))


class NobleManners(BasicAction):
    name = 'noble_manners'
    title = translate('cards', 'Noble Manners')
    color = Mana.white
    effectType = EffectType.influence
    
    def basicEffect(self, match, player):
        match.effects.add(effects.InfluencePoints(2))
        if match.state is State.interaction:
            player.fame += 1
    
    def strongEffect(self, match, player):
        match.effects.add(effects.InfluencePoints(4))
        if match.state is State.interaction:
            player.reputation += 1
            player.fame += 1
    
    
class Promise(BasicAction):
    name = 'promise'
    title = translate('cards', 'Promise')
    color = Mana.green
    effectType = EffectType.influence
    
    def basicEffect(self, match, player):
        match.effects.add(effects.InfluencePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.InfluencePoints(4))
        
    
class Rage(BasicAction):
    name = 'rage'
    title = translate('cards', 'rage')
    color = Mana.red
    effectType = EffectType.combat
    
    def basicEffect(self, match, player):
        options = [effects.AttackPoints(2), effects.BlockPoints(2)]
        match.effects.add(dialogs.choose(options))
    
    def strongEffect(self, match, player):
        match.effects.add(effects.AttackPoints(4))


class Stamina(BasicAction):
    name = 'stamina'
    title = translate('cards', 'Stamina')
    color = Mana.blue
    effectType = EffectType.movement
    
    def basicEffect(self, match, player):
        match.effects.add(effects.MovePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.MovePoints(4))
    

class Swiftness(BasicAction):
    name = 'swiftness'
    title = translate('cards', 'Swiftness')
    color = Mana.white
    effectType = EffectType.unknown
    
    def basicEffect(self, match, player):
        match.effects.add(effects.MovePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.AttackPoints(3, range=AttackRange.range))


class Threaten(BasicAction):
    name = 'threaten'
    title = translate('cards', 'Threaten')
    color = Mana.red
    effectType = EffectType.influence
    
    def basicEffect(self, match, player):
        match.effects.add(effects.InfluencePoints(2))
        
    def strongEffect(self, match, player):
        match.effects.add(effects.InfluencePoints(5))
        player.addReputation(-1)


class Tranquility(BasicAction):
    name = 'tranquility'
    title = translate('cards', 'Tranquility')
    color = Mana.green
    effectType = EffectType.healing
        
    def basicEffect(self, match, player):
        effect = effects.HealPoints(1)
        index = dialogs.chooseIndex([effect, translate('cards', "Draw a card")])
        if index == 0:
            match.effects.add(effects.HealPoints(1))
        else: player.drawCards(1)
        
    def strongEffect(self, match, player):
        effect = effects.HealPoints(2)
        index = dialogs.chooseIndex([effect, translate('cards', "Draw two cards")])
        if index == 0:
            match.effects.add(effects.HealPoints(2))
        else: player.drawCards(2)
        
        
class WillFocus(BasicAction):
    name = 'will_focus'
    title = translate('cards', 'Will Focus')
    color = Mana.green
    effectType = EffectType.special
     
    def basicEffect(self, match, player):
        color = dialogs.chooseManaColor()
        if color != Mana.green:
            match.effects.add(effects.ManaTokens(color))
        else: player.addCrystal(Mana.green)
        
    def strongEffect(self, match, player):
        Concentration._strongEffect(self, match, player, 2)
        