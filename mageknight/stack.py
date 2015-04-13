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

"""Improved QUndoStack. This is a simplified version of the stack used in Maestro."""

from PyQt5 import QtCore, QtGui, QtWidgets
  

class UndoStackError(RuntimeError):
    """This error is raised when methods of UndoStack are improperly used (e.g. call endMacro when no macro
    is built."""


class UndoStack(QtCore.QObject):
    """An UndoStack stores UndoCommands and provides undo/redo. It provides the same API as QUndoStack but
       improves it in several ways:
      
         - every object that has two methods undo and redo can be used as undo command,
         - the attempt to modify the stack during undo/redo will lead to a RuntimeError,
         - it is possible to abort a macro (similar to rollback in transactional DBs)
          
    """
    canRedoChanged = QtCore.pyqtSignal(bool)
    canUndoChanged = QtCore.pyqtSignal(bool)
    indexChanged = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._commands = []        # undo commands on the stack
        self._index = 0            # Position before the command that will be executed on redo
        self._activeMacros = []    # list of nested macros that are being built (first is outermost)
        self._inUndoRedo = False   # True during undo and redo
        self._undoAction = UndoRedoAction(self, redo=False)
        self._redoAction = UndoRedoAction(self, redo=True)
    
    def index(self):
        """Return the current position of the stack. stack.command(stack.index()) is the command that will
        be redone next."""
        return self._index
    
    def isComposing(self):
        """Return whether a macro is currently being built."""
        return len(self._activeMacros) > 0
    
    def count(self):
        """Return the number of commands on the stack."""
        return len(self._commands)
    
    def command(self, index):
        """Return the UndoCommand at the given index. stack.command(stack.index()) is the command that will
        be redone next."""
        return self._commands[index]
        
    def beginMacro(self):
        """Begin a new macro and return it.""" 
        if self._inUndoRedo:
            raise UndoStackError("Cannot begin a macro during undo/redo.")
        macro = Macro()
        self._activeMacros.append(macro)
        return macro
        # Macros are not added to their parent macro or to the stack unless they are finished.
        # (This makes abortMacro easier)
            
    def push(self, redoCall, undoCall=None):
        """Add a command to the stack and call its redo-method. This method may be either invoked
            - with a single command (something that has two methods 'redo' and 'undo'),
            - or with two Call-instances which will be executed on redo or undo, respectively.
        """
        assert not isinstance(redoCall, Macro) # will not work correctly
        if self._inUndoRedo:
            raise UndoStackError("Cannot push a command during undo/redo.")
        if isinstance(redoCall, Call):
            assert undoCall is not None
            command = GenericCommand(redoCall, undoCall)
        newMacro = len(self._activeMacros) == 0
        if newMacro:
            self.beginMacro()
        command.redo()
        self._activeMacros[-1].add(command)
        if newMacro:
            self.endMacro()
        
    def endMacro(self, abortIfEmpty=False):
        """Ends composition of a macro command. If *abortIfEmpty* is True and no commands have been added
        to the macro, it will simply be dropped (and never reach the stack)."""
        if len(self._activeMacros) == 0:
            raise UndoStackError("Cannot end a macro when no macro is being built.")
        if self._inUndoRedo:
            raise UndoStackError("Cannot end a macro during undo/redo.")

        macro = self._activeMacros.pop(-1)           
    
        # Remember that Macros are not added to their parent macro or to the stack unless they are finished.
        if len(self._activeMacros) > 0:
            self._activeMacros[-1].add(macro)
        else:
            # outermost macro has been closed
            if abortIfEmpty and macro.isEmpty():
                self._activeMacros = []
                return
            self._commands[self._index:] = [macro] # overwrite rest of the stack
            self._index += 1
            self._emitSignals()
            self._activeMacros = []
            
    def abortMacro(self):
        """Abort the current macro: Undo all commands that have been added to it and delete the macro. This
        is better than endMacro+undo because it doesn't leave an unfinished macro on the stack."""
        if len(self._activeMacros) == 0:
            raise UndoStackError("Cannot abort macro, because no macro is being built.")
        if self._inUndoRedo:
            raise UndoStackError("Cannot end a macro during undo/redo.")
        
        for macro in reversed(self._activeMacros):
            macro.abort()
        self._activeMacros = []
        # No need to change the stack because active macros have not been added to the stack.
        
    def clear(self):
        """Delete all commands on the stack."""
        if self._inUndoRedo or self.isComposing():
            raise UndoStackError("Cannot clear the stack during undo/redo or while a macro is built.")
        self._clear()
        
    def _clear(self):
        """Unconditionally delete all commands, active macros and everything from the stack."""
        self._commands = []
        self._activeMacros = []
        self._index = 0
        self._emitSignals()
        self._inUndoRedo = False         
           
    def canUndo(self):
        """Returns whether there is a command that can be undone."""
        return self._index > 0
    
    def canRedo(self):
        """Returns whether there is a command that can be redone."""
        return self._index < len(self._commands)

    def createRedoAction(self):
        """Return a QAction that will trigger the redo-method and changes its state (enabled, name...)
        according to the stack's index."""
        return self._redoAction
    
    def createUndoAction(self):
        """Return a QAction that will trigger the undo-method and changes its state (enabled, name...)
        according to the stack's index."""
        return self._undoAction

    def undo(self):
        """Undo the last command/macro."""
        self.setIndex(self._index-1)
    
    def redo(self):
        """Redo the next command/macro."""
        self.setIndex(self._index+1)
                
    def setIndex(self, index):
        """Undo/redo commands until there are *index* commands left that can be undone."""
        if self._inUndoRedo or self.isComposing():
            raise UndoStackError("Cannot change index during undo/redo or while a macro is built.""")
        if index != self._index:
            if not 0 <= index <= len(self._commands):
                raise ValueError("Invalid index {} (there are {} commands on the stack)."
                                 .format(index, len(self._commands)))
            self._inUndoRedo = True
            try:
                if index < self._index:
                    for command in reversed(self._commands[index:self._index]):
                        command.undo()
                else:
                    for command in self._commands[self._index:index]:
                        command.redo()
            except Exception as e:
                # TODO: improve error output
                print("Exception during undo/redo.")
                print("Undostack cleared")
                self._clear()
                print(e)
                return
            self._index = index
            self._inUndoRedo = False
            self._emitSignals()
    
    def _emitSignals(self):
        """Emit signals after self._index changed."""
        self.indexChanged.emit(self._index)
        self.canRedoChanged.emit(self.canRedo())
        self.canUndoChanged.emit(self.canUndo())


class Call:
    """A wrapper around a function call with arbitrary arguments and keyword arguments."""
    def __init__(self, callable, *args, **kwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        
    def execute(self):
        self.callable(*self.args, **self.kwargs)
        

class GenericCommand:
    """Generic command that executes two Call-instances on redo and undo. It is not necessary to create
    such commands manually, simply submit the arguments to stack.push."""
    def __init__(self, redoCall, undoCall):
        self.redoCall = redoCall
        self.undoCall = undoCall
        
    def redo(self):
        self.redoCall.execute()
        
    def undo(self):
        self.undoCall.execute()


class Macro:
    """A macro stores a list of undocommands and acts like a command that executes all of them together.
    The class Macro and its methods should never be used directly. Use methods of UndoStack instead.
    """
    def __init__(self):
        self.commands = []
    
    def add(self, commandOrMacro):
        """Add a command or macro to this macro."""
        self.commands.append(commandOrMacro)

    def redo(self):
        """(Re)do this macro and all of the commands inside."""
        for command in self.commands:
            command.redo()
    
    def undo(self):
        """Undo this macro and all of the commands inside."""
        for command in reversed(self.commands):
            command.undo()
            
    def abort(self):
        """Abort this macro during its construction (i.e. between UndoStack.beginMacro and
        UndoStack.endMacro) and undo all of its changes."""
        for command in reversed(self.commands):
            command.undo()
            
    def isEmpty(self):
        """Return whether this macro is empty, i.e. no command has been added to it."""
        return all(isinstance(command, Macro) and command.isEmpty() for command in self.commands)
        
               
class UndoRedoAction(QtWidgets.QAction):
    """QAction that is returned by the methods createUndoAction and createRedoAction."""
    def __init__(self, stack, redo):
        super().__init__(stack)
        self.setText('')
        if redo:
            self.setShortcut(self.tr('Ctrl+Y'))
            self.setIcon(QtGui.QIcon.fromTheme('edit-redo'))
            stack.canRedoChanged.connect(self.setEnabled)
            self.triggered.connect(stack.redo)
        else:
            self.setShortcut(self.tr('Ctrl+Z'))
            self.setIcon(QtGui.QIcon.fromTheme('edit-undo'))
            stack.canUndoChanged.connect(self.setEnabled)
            self.triggered.connect(stack.undo)
