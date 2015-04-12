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

from mageknight.match.data import InvalidAction
 
 
class MatchAdapter:
    def __init__(self, match, player):
        self._match = match
        self._player = player
        
    def __getattr__(self, attr):
        return getattr(self._match, attr)
    
    def movePlayer(self, coords):
        try:
            self._match.movePlayer(self._player, coords)
        except InvalidAction as e:
            print(e)