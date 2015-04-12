# -*- coding: utf-8 -*-
# Maestro Music Manager  -  https://github.com/maestromusic/maestro
# Copyright (C) 2009-2015 Martin Altmayer, Michael Helmling
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

"""Improved QUndoStack."""

from PyQt5 import QtWidgets


class UndoStack(QtWidgets.QUndoStack):
    def push(self, command, redoCall=None, undoCall=None):
        """Add a command to the stack and call its redo-method. This method may be either invoked
            - with a single command (something that has a 'text' attribute
              and two methods 'redo' and 'undo'),
            - or with a (translated) text and two Call-instances which will be executed on redo or undo,
              respectively.
        """
        if isinstance(command, str):
            assert redoCall is not None and undoCall is not None
            command = GenericCommand(command, redoCall, undoCall)
        super().push(command)
  

class Call:
    """A wrapper around a function call with arbitrary arguments and keyword arguments."""
    def __init__(self, callable, *args, **kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        
    def execute(self):
        self.callable(*self.args, **self.kwargs)
        

class GenericCommand(QtWidgets.QUndoCommand):
    """Generic command that executes two Call-instances on redo and undo. It is not necessary to create
    such commands manually, simply submit the arguments to stack.push."""
    def __init__(self, text, redoCall, undoCall):
        super().__init__(text)
        self.redoCall = redoCall
        self.undoCall = undoCall
        
    def redo(self):
        self.redoCall.execute()
        
    def undo(self):
        self.undoCall.execute()

