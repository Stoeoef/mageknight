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
from . import baseeffectlist

from .effects import * # @UnusedWildImport


class EffectList(baseeffectlist.EffectList):
    def add(self, effect):
        if isinstance(effect, PointsEffect) and not isinstance(effect, HealPoints) \
                and self.find(Concentration) is not None:
            # if several Concentration effects are active, only the last one counts
            effect.points += self.find(Concentration, reverse=True).extra
        super().add(effect)
