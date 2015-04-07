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

class EnemyType(enum.Enum):
    maraudingOrcs = 1
    keep = 2
    dungeon = 3
    mageTower = 4
    draconum = 5
    city = 6
    
    def pixmap(self):
        return utils.getPixmap('mk/enemies/{}_back.png'.format(self.name))


class Enemy:
    def __init__(self, type, name):
        assert isinstance(type, EnemyType)
        self.type = type
        self.name = name
        
    def pixmap(self):
        if self.name is None:
            return self.type.pixmap()
        return utils.getPixmap('mk/enemies/{}_{}.png'.format(self.type.name, self.name))
    
    