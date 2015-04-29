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

from PyQt5 import QtCore
 
# Image size is 550x529
ALTITUDE = 550/6 # Altitude of one of the six triangles forming a hex field. Equivalently: half of the width
SIDE = 529/5 # Length of one side of a hex field


class HexCoords:
    """An integer coordinate in a hexagonal grid. The x-axis points to the right, the y-axis to the topleft.
    This class provides methods to convert grid coordinates to usual pixel coordinates. It assumes that
    all hex-fields have a certain hardcoded size and corners at the top and bottom as well as edges at the
    left and right side. 
    """
    
    # This page is a great resource on hexagonal grids:
    # http://www.redblobgames.com/grids/hexagons/
    _corners = [QtCore.QPointF(0, -SIDE),
                QtCore.QPointF(ALTITUDE, -SIDE/2),
                QtCore.QPointF(ALTITUDE, SIDE/2),
                QtCore.QPointF(0, SIDE),
                QtCore.QPointF(-ALTITUDE, SIDE/2),
                QtCore.QPointF(-ALTITUDE, -SIDE/2)
               ]
    _neighbors = [(1, 1), (1, 0), (0, -1), (-1, -1), (-1, 0), (0, 1)]
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def __str__(self):
        return "({},{})".format(self.x, self.y)
    
    def __repr__(self):
        return "Hex({},{})".format(self.x, self.y)
    
    def __eq__(self, other):
        return isinstance(other, HexCoords) and self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not isinstance(other, HexCoords) or self.x != other.x or self.y != other.y
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def center(self):
        """Return the center of the hex in pixel coordinates.""" 
        return QtCore.QPointF((2*self.x-self.y) * ALTITUDE, -3/2*self.y * SIDE)

    def corner(self, index):
        """Return the pixel coordinates of a corner of this hex. *index* must be between 0 and 5. Corner 0
        is a the top of the hex, the remaining corners follow in clockwise order.
        """
        return self.center() + self._corners[index]
    
    def corners(self):
        """Return a list of pixel coordinates for all corners of this hex. The list starts at the top and
        continues in clockwise order."""
        center = self.center()
        return [center + corner for corner in self._corners]
    
    def neighbor(self, index):
        """Return the HexCoords for a neighboring hex. *index* must be between 0 and 5. Neighbor 0 is the
        top-right neighbor, the remaining neighbors follow in clockwise order.
        """
        n = self._neighbors[index]
        return HexCoords(self.x+n[0], self.y+n[1])
    
    def neighbors(self):
        """Return a list of HexCoords for all neighbors of this hex. Start at the top-right neighbor and
        continue in clockwise order."""
        return [self.neighbor(i) for i in range(6)]
    
    def isNeighborOf(self, other):
        """Return whether the given hex is a neighbor of this hex."""
        return self.distanceTo(other) == 1
    
    def distanceTo(self, other):
        """Return the (integer) distance between this hex and another one."""
        return (abs(self.x - other.x) + abs(self.y - other.y)
                 # note: our y-axis is reversed compared to redblobgames.com
                 + abs(self.x - self.y - other.x + other.y)) / 2

    def contains(self, point):
        """Return whether this hex contains the given pixel coordinates (QPoint or QPointF)."""
        point = point - self.center() # use local coordinates
        if not -ALTITUDE < point.x() < ALTITUDE:
            return False
        if not -SIDE < point.y() < SIDE:
            return False

        lastCorner = self._corners[-1]
        for corner in self._corners:
            side = corner - lastCorner
            vector = point - lastCorner
            if side.x()*vector.y() - side.y()*vector.x() < 0:
                return False
            lastCorner = corner
        return True
    
    @staticmethod
    def fromPixel(point):
        """Return the hex coordinates at the given pixel coordinates (QPoint or QPointF)."""
        x, y = _fractionalHex(point)
        guess = HexCoords(int(round(x)), int(round(y)))
        if guess.contains(point):
            return guess
        # Use the neighbor with the nearest center.
        # Do NOT search for a neighbor which 'contains' the point, because at the borders there might
        # exist points for which neighbor.contains is False for all neighbors.
        nearest = None
        minimalDistance = float("inf")
        neighbors = guess.neighbors()
        for i, neighbor in enumerate(neighbors):
            distance = QtCore.QLineF(neighbor.center(), point).length()
            if distance < minimalDistance:
                nearest = i
                minimalDistance = distance
        return neighbors[nearest]
    
    def __add__(self, other):
        return HexCoords(self.x+other.x, self.y+other.y)
    
    def __sub__(self, other):
        return HexCoords(self.x-other.x, self.y-other.y)


def _fractionalHex(point):
    """Return fractional hex coordinates for the given point."""
    # Invert the transformation that is used in HexCoord.center.
    return (point.x()/(2*ALTITUDE) - 1/(3*SIDE) * point.y(), -2/(3*SIDE) * point.y())
