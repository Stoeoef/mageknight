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

"""This module provides some magic to handle undo/redo, type checking and signal emitting transparently.
To use it your class must subclass AttributeObject and contain Attributes in its class dict:

    class Person(AttributeObject):
        name = StringAttribute()
        age = IntAttribute()
        
You must make sure that the constructor of AttributeObject is called and gets a Stack as argument.
Every change to the attributes will then be put on the stack and can consequently be undone. For example:

    >>> p = Person(stack)
    >>> p.name
    ''
    >>> p.name = 'Vladaa'
    >>> p.name
    'Vladaa'
    >>> stack.undo()
    >>> p.name
    ''

Additionally, whenever the attribute value is set, it is checked for the correct type.
If your class contains properly named signals (e.g. nameChanged, ageChanged), these will be emitted when
the attribute's value has changed.
"""

import functools

from PyQt5 import QtCore
from mageknight.stack import Call

__all__ = ['AttributeObject', 'Attribute', 'BoolAttribute',
           'StringAttribute', 'IntAttribute', 'ListAttribute'] 


class AttributeObject(QtCore.QObject):
    """Base class for all class that wish to use attributes. It makes sure that attributes are properly
    initialized."""
    def __init__(self, stack, parent=None):
        super().__init__(parent)
        self.stack = stack
        for key, attr in list(type(self).__dict__.items()):
            if isinstance(attr, Attribute):
                if attr.name is None: # only for the first object of this type
                    attr._init(type(self), key, **attr._kwargs)
                setattr(self, attr._name, attr.default(self))
    
    
class Attribute:
    """Base class for all attributes. For built-in types you will typically want to use the specialized
    subclasses (e.g. BoolAttribute). Arguments are
        
        - type: Only values of this type (and maybe None) are allowed in this attribute.
        - allowNone: Whether the attribute may be set to None.
        - default: the default value, see the 'default' method.
        - signal: name of the signal associated with this attribute. If None, the attribute will try to use
            the canonical name (<attribute name>Changed). If this signal does not exist, the attribute won't
            emit a signal. 
        - sendValue: whether the signal associated with this attribute has an argument - the attribute value.
    
    """
    def __init__(self, type, default=None, allowNone=True, sendValue=False, **kwargs):
        self.name = None
        self.type = type
        self.allowNone = allowNone
        self.sendValue = sendValue
        self._default = default
        self._kwargs = kwargs
    
    def _init(self, cls, name, signal=None):
        """Initialize this attribute. *cls* is the class containing the attribute, *name* is the attribute's
        name. Keyword arguments stem from the constructor. Because *cls* and *name* are not available in
        the attribute's constructor, this method is invoked, when *cls* is instantiated for the first time.
        """
        self.name = name
        self._name = '_'+name
        del self._kwargs
        if signal is None:
            if hasattr(cls, name+'Changed'):
                self.signal = name + 'Changed'
            else:
                self.signal = None
        else:
            assert isinstance(signal, str)
            self.signal = signal

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._name)
        
    def _set(self, instance, value):
        setattr(instance, self._name, value)
        if self.signal:
            self.emitSignal(instance)
        
    def __set__(self, instance, value):
        if not ((self.allowNone and value is None) or isinstance(value, self.type)):
            raise TypeError("'{}' attribute must be of type '{}', not {}."
                            .format(self.name, self.type, value))
        currentValue = getattr(instance, self._name)
        if currentValue != value:
            instance.stack.push(Call(self._set, instance, value),
                                Call(self._set, instance, currentValue))
            
    def emitSignal(self, instance):
        if self.signal:
            signal = getattr(instance, self.signal)
            if self.sendValue:
                signal.emit(getattr(instance, self._name))
            else: signal.emit()
        
    def default(self, instance):
        """Return the default value that should be used to initialize this attribute in the given
        instance (of the class containing this attribute).
        """
        return self._default
            
         
class BoolAttribute(Attribute):
    def __init__(self, default=False, allowNone=False, **kwargs):
        super().__init__(bool, default=default, allowNone=allowNone, **kwargs)
           
    
class StringAttribute(Attribute):
    def __init__(self, default='', allowNone=False, **kwargs):
        super().__init__(str, default=default, allowNone=allowNone, **kwargs)
    

class IntAttribute(Attribute):
    """An attribute that stores an integer. The additional arguments *minimum* and *maximum* limit the
    possible range of attribute values (both may be None). When an application tries to set a value outside
    of these bounds, IntAttribute will either raise a ValueError (*strict*=True) or use the nearest possible
    value (*strict*=False).
    """
    def __init__(self, default=0, minimum=0, maximum=None, strict=True, allowNone=False, **kwargs):
        super().__init__(int, default=default, allowNone=allowNone, **kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.strict = strict
        
    def _set(self, instance, value):
        if self.minimum is not None and value < self.minimum:
            if self.strict:
                raise ValueError("{} is too small for attribute '{}'".format(value, self.name))
            else: value = self.minimum
        if self.maximum is not None and value > self.maximum:
            if self.strict:
                raise ValueError("{} is too big for attribute '{}'".format(value, self.name))
            else: value = self.maximum
        super()._set(instance, value)
    

class ListAttribute(Attribute):
    """An attribute that stores a list. Items in the list must be of type *itemType*.
    As additional feature, ListAttribute can provide undo/redo for some attributes of *itemType*. Specify
    these attributes as list of (attribute name, attribute type)-tuples in the argument *itemAttributes*.
    For example:
    
        class Party(AttributeObject):
            persons = ListAttribute(Person, itemAttributes=[('age', int)])
    
    Then 'persons' provides methods to change the value of item attributes undoably:
    
        >>> p = Party(stack)
        >>> p.persons = [Person('A'), Person('B')]
        >>> p.persons.setAge(p.persons[0], 20)
        >>> p.persons[0].age
        20
        >>> stack.undo()
        >>> p.persons[0].age
        0 
        
    Warning: Direct assignments to item attributes are not undoable (e.g. 'p.persons[0].age = 100').
    The reason is simple: Person is no AttributeObject and Person.age is no attribute.
    """
    def __init__(self, itemType, itemAttributes=tuple(), **kwargs):
        super().__init__(UndoList, **kwargs)
        self.itemType = itemType
        self.itemAttributes = itemAttributes
                
    def default(self, instance):
        return self._createList(instance, [])
    
    def _createList(self, instance, items):
        for item in items:
            if not isinstance(item, self.itemType):
                raise TypeError("All items of list attribute '{}' must be of type '{}', not {}."
                                .format(self.name, self.itemType, item))
        if self.signal is not None:
            signal = getattr(instance, self.signal)
        else: signal = None
        return UndoList(instance.stack, self.itemType, signal, items, itemAttributes=self.itemAttributes)
    
    def __set__(self, instance, value):
        if not isinstance(value, list):
            raise TypeError("'{}' attribute must be of type 'list', not {}."
                            .format(self.name, value))
        value = self._createList(instance, value)
        super().__set__(instance, value)

            
def setItemAttribute(instance, attr, type, item, value):
    """Helper: Set the value of an item attribute. *instance* is the corresponding Attribute, *attr* and
    *type* are name and type of the item attribute. *item* is the item that should be modified and *value*
    is the new value.
    """
    if value is not None and not isinstance(value, type):
        raise TypeError("'{}' item attribute must be of type '{}', not {}."
                        .format(attr, type, value))
    oldValue = getattr(item, attr)
    if value != oldValue:
        instance._stack.push(Call(instance._setAttr, item, attr, value),
                             Call(instance._setAttr, item, attr, oldValue))

# The following two methods are used if the actual attribute is a ListAttribute and defines and item
# attribute of type tuple.
def addItemAttributeItems(instance, attr, type, item, values):
    """Helper: For item attributes of type tuple, extend the item attribute's value by *values*."""
    values = tuple(values)
    old = getattr(item, attr)
    new = old + values
    instance._stack.push(Call(instance._setAttr, item, attr, new),
                         Call(instance._setAttr, item, attr, old))

def removeItemAttributeItems(instance, attr, type, item, values):
    """Helper: For item attributes of type tuple, remove every value from *values* from the
    item attribute's value."""
    if len(values) > 0:
        old = getattr(item, attr)
        new = tuple(o for o in old if o not in values)
        instance._stack.push(Call(instance._setAttr, item, attr, new),
                             Call(instance._setAttr, item, attr, old))


class UndoList(list):
    """This subclass of list is used by ListAttribute. When initialized it gets a pointer to the
    attribute's stack. Methods that modify the list (e.g. append, __setitem__, etc.) will then use the
    stack.
    For each (name, type)-tuple in *itemAttributes*, this object will contain a set<AttributeName>-method
    that can be used to modify this item attribute in a given item.
    """
    def __init__(self, stack, itemType, signal, items=tuple(), itemAttributes=[]):
        super().__init__(items)
        self._stack = stack
        self._itemType = itemType
        self._signal = signal
        
        for attr, type in itemAttributes:
            if type is list:
                type = tuple
            setterName = 'set' + attr[0].upper() + attr[1:]
            setattr(self, setterName, functools.partial(setItemAttribute, self, attr, type)) 
            
            if type is tuple:
                adderName = 'add' + attr[0].upper() + attr[1:]
                setattr(self, adderName, functools.partial(addItemAttributeItems, self, attr, type))
               
                removerName = 'remove' + attr[0].upper() + attr[1:]
                setattr(self, removerName, functools.partial(removeItemAttributeItems, self, attr, type))        
                    
    def _emitSignal(self):
        if self._signal is not None:
            self._signal.emit()
    
    def _setItem(self, index, item):
        super().__setitem__(index, item)
        self._emitSignal()
        
    def _insert(self, index, item):
        super().insert(index, item)
        self._emitSignal()
        
    def _delItem(self, index):
        super().__delitem__(index)
        self._emitSignal()
        
    def _setAttr(self, item, attr, value):
        if value != getattr(item, attr):
            setattr(item, attr, value)
            self._emitSignal()

    def __setitem__(self, index, item):
        if not isinstance(item, self._itemType):
            raise TypeError("All items of list attribute must be of type '{}', not {}."
                            .format(self._itemType, item))
        oldItem = self[index]
        self._stack.push(Call(self._setItem, index, item),
                         Call(self._setItem, index, oldItem))
    
    def __delitem__(self, index):
        item = self[index]
        self._stack.push(Call(self._delItem, index),
                         Call(self._insert, index, item))
        
    def append(self, item):
        if not isinstance(item, self._itemType):
            raise TypeError("All items of list attribute must be of type '{}', not {}."
                            .format(self._itemType, item))
        index = len(self)
        self._stack.push(Call(self._insert, index, item),
                         Call(self._delItem, index))
    
    def clear(self):
        if len(self) > 0:
            copy = self.copy()
            self._stack.push(Call(self._delItem, slice(0, len(self))),
                             Call(self._setItem, slice(0, len(self), copy)))
        
    def extend(self, items):
        items = list(items)
        for item in items:
            if not isinstance(item, self._itemType):
                raise TypeError("All items of list attribute must be of type '{}', not {}."
                                .format(self._itemType, item))
        if len(items) > 0:
            start = len(self)
            end = start + len(items)
            self._stack.push(Call(self._setItem, slice(start, end), items),
                             Call(self._delItem, slice(start, end), items))
        
    def insert(self, index, item):
        if not isinstance(item, self._itemType):
            raise TypeError("All items of list attribute must be of type '{}', not {}."
                            .format(self._itemType, item))
        self._stack.push(Call(self._insert, index, item),
                         Call(self._delItem, index))

    def pop(self, index=-1):
        item = self[index]
        self._stack.push(Call(self._delItem, index),
                         Call(self._insert, index, item))
        return item
    
    def remove(self, item):
        index = self.index(item)
        self._stack.push(Call(self._delItem, index),
                         Call(self._insert, index, item))
            
    def reverse(self):
        raise NotImplementedError()
