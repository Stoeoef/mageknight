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

import types

from mageknight.data import State, CancelAction, InvalidAction


class EnhancedDecorator:
    """This decorator enhances a decorator: The enhanced decorator can be used as follows:
        @dec
        def function  # results in function = dec(function)
        
        @dec(argument, kwarg=2)
        def f2                   # results in f2 = dec(f2, argument, kwarg=2)
    
    The point is that one does not have to use parentheses in the first case.
    """
    def __init__(self, decorator):
        self.decorator = decorator
        
    def __call__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], types.FunctionType) and len(kwargs) == 0:
            return self.decorator(args[0])
        else:
            def wrapper(f):
                return self.decorator(f, *args, **kwargs)
            return wrapper
        
    
@EnhancedDecorator
def action(f, *states):
    """This decorator is used to wrap player actions. It has the following functions:
        - The action will be wrapped into an undo/redo macro.
        - If the user cancels the action (e.g. by canceling a dialog) or if he chooses an invalid action,
          the macro will be aborted. In particular, all steps taken so far will be undone.
        - If a list of states is specified, it will check whether the current state is contained in the list
          and abort if not.
    """
    def wrapper(self, *args, **kwargs):
        nonlocal states
        if len(states) == 1 and not isinstance(states[0], State): # a single list of states
            states = states[0]
        if len(states) > 0 and self.state not in states:
            print("Cannot perform this action in state '{}'.".format(self.state.name))
            return
        self.stack.beginMacro()
        try:
            f(self, *args, **kwargs)
            self.stack.endMacro(abortIfEmpty=True) # the macro is often empty, when new info was revealed
        except CancelAction: # action was aborted e.g. by canceling a dialog
            self.stack.abortMacro()
        except InvalidAction as e:
            print(e)
            self.stack.abortMacro()
            
    return wrapper
    
