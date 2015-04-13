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

import enum

from mageknight import utils

__all__ = ['EnemyType', 'AttackType', 'Attack', 'Enemy']


class EnemyType(enum.Enum):
    """A type (i.e. color) of an enemy token."""
    maraudingOrcs = 1
    keep = 2
    dungeon = 3
    mageTower = 4
    draconum = 5
    city = 6
    
    def pixmap(self):
        """Return the back side of the enemy tokens of this type."""
        return utils.getPixmap('mk/enemies/{}_back.png'.format(self.name))


class AttackType(enum.Enum):
    """The type of an enemy attack."""
    physical = 1
    fire = 2
    ice = 3
    coldFire = 4
    summoner = 5


class Attack:
    """An enemy attack. It consists of a type and a value. The value is either the amount of damage
    or -- if type == AttackType.summoner -- the EnemyType of the summoned enemy. *type* defaults to
    physical or summoner attack, depending on *value*. 
    """
    def __init__(self, value, type=None):
        if type is None:
            type = AttackType.physical if isinstance(value, int) else AttackType.summoner
        assert isinstance(type, AttackType)
        assert isinstance(value, int) or (type == AttackType.summoner and isinstance(value, EnemyType))
        self.type = type
        self.value = value
    
    
class Enemy:
    """An enemy token. It is initialized using its EnemyType and its id (e.g. 'altem_mages').
    It has the attributes
        type, id, name, armor, attack, fame,
        fortified, physicalResistance, iceResistance, fireResistance, swift, brutal, poison, paralyze
    (attributes in the second line are booleans).
    """
    _enemyData = {}
    _enemyData[EnemyType.maraudingOrcs] = {
        'prowlers': ('Prowlers', 2, 3, Attack(4), 2),
        'diggers': ('Diggers', 2, 3, Attack(3), 2, 'fortified'),
        'cursed_hags': ('Cursed Hags', 2, 5, Attack(3), 3, 'poison'),
        'wolf_riders': ('Wolf Riders', 2, 4, Attack(3), 3, 'swift'),
        'ironclads': ('Ironclads', 2, 3, Attack(4), 4, 'brutal', 'physicalResistance'),
        'orc_summoners': ('Orc Summoners', 2, 4, Attack(EnemyType.dungeon), 4),
    }
    _enemyData[EnemyType.keep] = {
        'crossbowmen': ('Crossbowmen', 3, 4, Attack(4), 3, 'swift'),
        'guardsmen': ('Guardsmen', 3, 7, Attack(3), 3, 'fortified'),
        'swordsmen': ('Swordsmen', 2, 5, Attack(6), 4),
        'golems': ('Golems', 2, 5, Attack(2), 4, 'physicalResistance'),
    }
    _enemyData[EnemyType.mageTower] = {
        'monks': ('Monks', 2, 5, Attack(5), 4, 'poison'),
        'illusionists': ('Illusionists', 2, 3, Attack(EnemyType.dungeon), 4, 'physicalResistance'),
        'ice_mages': ('Ice Mages', 2, 6, Attack(5, AttackType.ice), 5, 'iceResistance'),
        'ice_golems': ('Ice Golems', 1, 4, Attack(2, AttackType.ice), 5, 'paralyze', 'physicalResistance', 'iceResistance'),
        'fire_mages': ('Fire Mages', 2, 5, Attack(6, AttackType.fire), 5, 'fireResistance'),
        'fire_golems': ('Fire Golems', 1, 4, Attack(3, AttackType.fire), 5, 'brutal', 'physicalResistance', 'fireResistance'),
    }
    _enemyData[EnemyType.dungeon] = {
        'minotaur': ('Minotaur', 2, 5, Attack(5), 4, 'brutal'),
        'gargoyle': ('Gargoyle', 2, 4, Attack(5), 4, 'physicalResistance'),
        'medusa': ('Medusa', 2, 4, Attack(6), 5, 'paralyze'),
        'crypt_worm': ('Crypt Worm', 2, 6, Attack(6), 5, 'fortified'),
        'werewolf': ('Werewolf', 2, 5, Attack(7), 5, 'swift'),
    }
    _enemyData[EnemyType.city] = {
        'freezers': ('Freezers', 3, 7, Attack(3, AttackType.ice), 7, 'fireResistance', 'swift', 'paralyze'),
        'gunners': ('Gunners', 3, 6, Attack(6, AttackType.fire), 7, 'iceResistance', 'brutal'),
        'altem_guardsmen': ('Altem Guardsmen', 2, 7, Attack(6), 8, 'fortified', 'physicalResistance', 'iceResistance', 'fireResistance'),
        'altem_mages': ('Altem Mages', 2, 8, Attack(4, AttackType.coldFire), 8, 'fortified', 'physicalResistance', 'brutal', 'poison'),
    }
    _enemyData[EnemyType.draconum] = {
        'swamp_dragon': ('Swamp Dragon', 2, 9, Attack(5), 7, 'swift', 'poison'),
        'fire_dragon': ('Fire Dragon', 2, 7, Attack(9, AttackType.fire), 8, 'physicalResistance', 'fireResistance'),
        'ice_dragon': ('Ice Dragon', 2, 7, Attack(6, AttackType.ice), 8, 'physicalResistance', 'iceResistance', 'paralyze'),
        'high_dragon': ('High Dragon', 2, 9, Attack(6, AttackType.coldFire), 9, 'fireResistance', 'iceResistance', 'brutal'),
    }
    
    def __init__(self, type, id):
        assert isinstance(type, EnemyType)
        self.type = type
        self.id = id
        data = self._enemyData[type][id]
        self.name, self.count, self.armor, self.attack, self.fame = data[:5]
        attrs = ['fortified', 'physicalResistance', 'iceResistance', 'fireResistance',
                 'swift', 'brutal', 'poison', 'paralyze']
        assert all(attr in attrs for attr in data[5:])
        for attr in attrs:
            setattr(self, attr, attr in data[5:])
        
    def pixmap(self):
        """Return the front side of this enemy token."""
        return utils.getPixmap('mk/enemies/{}_{}.png'.format(self.type.name, self.id))
    