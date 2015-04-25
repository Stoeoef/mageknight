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
from .core import Element

__all__ = ['EnemyCategory', 'Attack', 'Enemy', 'UnknownEnemy']


class EnemyCategory(enum.Enum):
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
    
    def all(self):
        """Return all enemies from this category. List enemies multiple times according to the 'count'
        attribute."""
        enemies = []
        for id in Enemy._enemyData[self].keys():
            enemy = Enemy(self, id)
            enemies.append(enemy)
            if enemy.count > 1:
                enemies.extend(Enemy(self, id) for _ in range(enemy.count-1))
        return enemies
   
    
class Attack:
    """An enemy attack. It consists of an element and a value. The value is either the amount of damage
    or -- if element == Element.summoner -- the EnemyCategory of the summoned enemy. *element* defaults to
    physical or summoner attack, depending on *value*. 
    """
    def __init__(self, value, element=None):
        if element is None:
            element = Element.physical if isinstance(value, int) else Element.summoner
        assert isinstance(element, Element)
        assert isinstance(value, int) or (element == Element.summoner and isinstance(value, EnemyCategory))
        self.element = element
        self.value = value
        
    
class Enemy:
    """An enemy token. It is initialized using its EnemyCategory and its id (e.g. 'altem_mages').
    It has the attributes
        type, id, name, armor, attack, fame,
        fortified, physicalResistance, iceResistance, fireResistance, swift, brutal, poison, paralyze
    (attributes in the second line are booleans).
    """
    _enemyData = {}
    _enemyData[EnemyCategory.maraudingOrcs] = {
        'prowlers': ('Prowlers', 2, 3, Attack(4), 2),
        'diggers': ('Diggers', 2, 3, Attack(3), 2, 'fortified'),
        'cursed_hags': ('Cursed Hags', 2, 5, Attack(3), 3, 'poison'),
        'wolf_riders': ('Wolf Riders', 2, 4, Attack(3), 3, 'swift'),
        'ironclads': ('Ironclads', 2, 3, Attack(4), 4, 'brutal', 'physicalResistance'),
        'orc_summoners': ('Orc Summoners', 2, 4, Attack(EnemyCategory.dungeon), 4),
    }
    _enemyData[EnemyCategory.keep] = {
        'crossbowmen': ('Crossbowmen', 3, 4, Attack(4), 3, 'swift'),
        'guardsmen': ('Guardsmen', 3, 7, Attack(3), 3, 'fortified'),
        'swordsmen': ('Swordsmen', 2, 5, Attack(6), 4),
        'golems': ('Golems', 2, 5, Attack(2), 4, 'physicalResistance'),
    }
    _enemyData[EnemyCategory.mageTower] = {
        'monks': ('Monks', 2, 5, Attack(5), 4, 'poison'),
        'illusionists': ('Illusionists', 2, 3, Attack(EnemyCategory.dungeon), 4, 'physicalResistance'),
        'ice_mages': ('Ice Mages', 2, 6, Attack(5, Element.ice), 5, 'iceResistance'),
        'ice_golems': ('Ice Golems', 1, 4, Attack(2, Element.ice), 5, 'paralyze', 'physicalResistance', 'iceResistance'),
        'fire_mages': ('Fire Mages', 2, 5, Attack(6, Element.fire), 5, 'fireResistance'),
        'fire_golems': ('Fire Golems', 1, 4, Attack(3, Element.fire), 5, 'brutal', 'physicalResistance', 'fireResistance'),
    }
    _enemyData[EnemyCategory.dungeon] = {
        'minotaur': ('Minotaur', 2, 5, Attack(5), 4, 'brutal'),
        'gargoyle': ('Gargoyle', 2, 4, Attack(5), 4, 'physicalResistance'),
        'medusa': ('Medusa', 2, 4, Attack(6), 5, 'paralyze'),
        'crypt_worm': ('Crypt Worm', 2, 6, Attack(6), 5, 'fortified'),
        'werewolf': ('Werewolf', 2, 5, Attack(7), 5, 'swift'),
    }
    _enemyData[EnemyCategory.city] = {
        'freezers': ('Freezers', 3, 7, Attack(3, Element.ice), 7, 'fireResistance', 'swift', 'paralyze'),
        'gunners': ('Gunners', 3, 6, Attack(6, Element.fire), 7, 'iceResistance', 'brutal'),
        'altem_guardsmen': ('Altem Guardsmen', 2, 7, Attack(6), 8, 'fortified', 'physicalResistance', 'iceResistance', 'fireResistance'),
        'altem_mages': ('Altem Mages', 2, 8, Attack(4, Element.coldFire), 8, 'fortified', 'physicalResistance', 'brutal', 'poison'),
    }
    _enemyData[EnemyCategory.draconum] = {
        'swamp_dragon': ('Swamp Dragon', 2, 9, Attack(5), 7, 'swift', 'poison'),
        'fire_dragon': ('Fire Dragon', 2, 7, Attack(9, Element.fire), 8, 'physicalResistance', 'fireResistance'),
        'ice_dragon': ('Ice Dragon', 2, 7, Attack(6, Element.ice), 8, 'physicalResistance', 'iceResistance', 'paralyze'),
        'high_dragon': ('High Dragon', 2, 9, Attack(6, Element.coldFire), 9, 'fireResistance', 'iceResistance', 'brutal'),
    }
    
    def __init__(self, category, id):
        assert isinstance(category, EnemyCategory)
        
        # Basic data
        self.category = category
        self.id = id
        data = self._enemyData[category][id]
        self.name, self.count, self.armor, self.attack, self.fame = data[:5]
        
        # Attributes
        attrs = data[5:]
        allAttrs = ['fortified', 'swift', 'brutal', 'poison', 'paralyze']
        for attr in allAttrs:
            setattr(self, attr, attr in attrs)
            
        # Resistances
        self.resistances = []
        if 'physicalResistance' in attrs:
            self.resistances.append(Element.physical)
        if 'iceResistance' in attrs:
            self.resistances.append(Element.ice)
        if 'fireResistance' in attrs:
            self.resistances.append(Element.fire)
        if 'iceResistance' in attrs and 'fireResistance' in attrs:
            self.resistances.append(Element.coldFire)
        
    def pixmap(self, gray=False):
        """Return the front side of this enemy token. If *gray* is True, return a grayscale version."""
        dir = 'mk/enemies/' if not gray else 'mk/enemies/gray/'
        return utils.getPixmap('{}{}_{}.png'.format(dir, self.category.name, self.id))
    

def get(id):
    for category, aDict in Enemy._enemyData.items():
        if id in aDict:
            return Enemy(category, id)
    else: raise ValueError("There is no enemy with id '{}'.".format(id))
    

class UnknownEnemy:
    """Represents an unknown enemy of a certain category."""
    def __init__(self, category):
        self.category = category
        
    def pixmap(self):
        return self.category.pixmap()
    
