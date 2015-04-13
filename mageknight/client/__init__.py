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

from mageknight.matchdata import *
 
        
class Adapter(QtCore.QObject):
    _attrs = None # subclasses may specify a list of allowed attributes
    
    def __init__(self, object):
        self._object = object
        
    def __getattr__(self, attr):
        if self._attrs is None or attr in self._attrs:
            return getattr(self._object, attr)
        
        
def action(f):
    """This decorator is used to mark player actions, i.e. functions of the client that should be
    redirected to the server.
    This decorator returns a function that calls the method with the same name as *f* of the match object
    with the parameters submitted to *f*. Additionally, the client's player is submitted as first parameter.
    The decorator also adds some error handling.
    """
    def wrapped(self, *args, **kwargs):
        try:
            getattr(self._match, f.__name__)(self._player, *args, **kwargs)
        except InvalidAction as e:
            print(e)
    return wrapped
                

class LocalMatchClient(Adapter):
    
    def __init__(self, match, player):
        self._match = match
        self._player = player
        self.source = ManaSourceAdapter(match.source)
        self.map = MapAdapter(match.map)
        self.players = [PlayerAdapter(player) for player in match.players]
        
    def __getattr__(self, attr):
        return getattr(self._match, attr)
    
    @action
    def playCard(self, card, effectNumber): pass
    @action
    def movePlayer(self, coords): pass

        
class ManaSourceAdapter(Adapter):
    _attrs = ['changed', 'count']
    
    def __len__(self):
        return len(self._object)
    
    def __getitem__(self, index):
        return self._object[index]
    
    def __contains(self, item):
        return item in self._object
    
    def __iter__(self):
        return iter(self._object)
    

class MapAdapter(Adapter):
    _attrs = None # TODO
    

class PlayerAdapter(Adapter):
    _attrs = None # TODO
    