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

import os

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt 


def getPixmap(path, size=None):
    """Return a QPixmap from a path within the images-folder, e.g. 'tiles/tile-1.png'. If *size* is given,
    the pixmap will be scaled to fit into *size* (keeping aspect ratio)."""
    pixmap = QtGui.QPixmap(os.path.join("images", *path.split('/'))) # use platform-specific separators
    if size is None:
        return pixmap
    else: return scalePixmap(pixmap, size)


def html(pixmap, attributes=''):
    """Return an <img>-tag that contains the pixmap embedded into HTML using a data-URI
    (https://en.wikipedia.org/wiki/Data_URI_scheme). Use this to include pixmaps that are not stored in a
    file into HTML-code. *attributes* is inserted into the tag and may contain arbitrary HTML-attributes.
    """ 
    buffer = QtCore.QBuffer()
    pixmap.save(buffer, "PNG")
    string = bytes(buffer.buffer().toBase64()).decode('ascii')
    return '<img {} src="data:image/png;base64,{}" />'.format(attributes, string)


def scalePixmap(pixmap, sizeOrX, y=None):
    """Scale the given pixmap. The remaining parameters can be either a QSize or a tuple (width, height)."""
    if isinstance(sizeOrX, QtCore.QSize):
        size = sizeOrX
    else: size = QtCore.QSize(sizeOrX, y)
    return pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)