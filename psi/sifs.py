# Pipe Stress Infinity (PSI) - The pipe stress analysis and design software.
# Copyright (c) 2021 Denis Gomes <denisgomes@consultant.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Implementation of code based stress intensification factors."""


from __future__ import division

from psi.entity import Entity, EntityContainer
from psi import units


class SIF(Entity):
    """A tee type intersection or a welding connection"""

    def __init__(self, element, point):
        super(SIF, self).__init__()
        self.element = element
        self.point = point

    @property
    def parent(self):
        """Returns the SIFContainer instance."""
        return self.app.sifs

    def apply(self, elements=None):
        """Apply the sif to the elements.

        Parameters
        ----------
        elements : list
            A list of elements. If elements is None, sif is applied to the
            active elements.
        """
        self.parent.apply([self], elements)

    def is_intersection(self):
        """A tee type intersection"""
        return self.point.vertex.edges == 3

    def is_connection(self):
        """A welding connection"""
        return self.point.vertex.edges == 2


class Intersection(SIF):
    """A tee type intersection"""

    def __init__(self, element, point):
        super(Intersection, self).__init__(element, point)

        assert self.intersection(), "invalid intersection point"

    def header(self):
        """Header element of intersection"""
        pass

    def branch(self):
        """Branch element of intersection"""
        pass


class Connection(SIF):
    """A joint between two pipe spools"""

    def __init__(self, element, point):
        super(Connection, self).__init__(element, point)

        assert self.connection(), "invalid connection point"


@units.define(do="length", tn="length", dob="length", rx="length", tc="length")
class Welding(Intersection):
    """Welding tees per ASME B16.9."""

    def __init__(self, element, point, do, tn, dob, rx, tc):
        """
        Parameters
        ----------
        code : str
            The code used to calculate the parameters

        do : float
            Outer diameter of run (i.e. header) pipe

        tn : float
            Nomimal thickness of run (i.e. header) pipe

        dob : float
            Outer diameter of branch pipe

        rx : float
            External crotch radius of welding tees

        tc : float
            Crotch thickness
        """
        super(Welding, self).__init__(element, point)
        self.do = do
        self.tn = tn
        self.dob = dob
        self.rx = rx
        self.tc = tc


@units.define(do="length", tn="length")
class Unreinforced(Intersection):
    """Unreinforced fabricated tee."""

    def __init__(self, element, point, do, tn):
        """
        Parameters
        ----------
        code : str
            The code used to calculate the parameters

        do : float
            Outer diameter of run (i.e. header) pipe

        tn : float
            Nomimal thickness of run (i.e. header) pipe
        """
        super(Unreinforced, self).__init__(element, point)
        self.do = do
        self.tn = tn


@units.define(do="length", tn="length", tr="length")
class Reinforced(Intersection):
    """Reinforced fabricated tee."""

    def __init__(self, element, point, do, tn, tr):
        """
        Parameters
        ----------
        code : str
            The code used to calculate the parameters

        do : float
            Outer diameter of run (i.e. header) pipe

        tn : float
            Nomimal thickness of run (i.e. header) pipe

        tr : float
            Pad thickness
        """
        super(Reinforced, self).__init__(element, point)
        self.do = do
        self.tn = tn
        self.tr = tr


@units.define(do="length", tn="length")
class Weldolet(Intersection):
    """Olet fitting with welded outlet branch."""

    def __init__(self, element, point, do, tn):
        """
        Parameters
        ----------
        code : str
            The code used to calculate the parameters

        do : float
            Outer diameter of run (i.e. header) pipe

        tn : float
            Nomimal thickness of run (i.e. header) pipe
        """
        super(Weldolet, self).__init__(element, point)
        self.do = do
        self.tn = tn


@units.define(do="length", tn="length")
class Sockolet(Intersection):
    """Olet fitting with socket welded outlet branch.

    A sockolet is similar to a weldolet with the exception that the branch
    pipe goes into a socket type connection and is welded. A sockolet can be
    modeled by defining a weldolot 'intersection' sif at the header pipe and
    a socket 'connection' sif at the branch connection.

    Note that ASME codes do not describe any way to combine sifs and so in
    this method is way to get around that. Others just stick with the higher
    of the two sifs when their is no other choice since adding them together
    is too conservative.
    """

    def __init__(self, element, point, do, tn):
        """
        Parameters
        ----------
        code : str
            The code used to calculate the parameters

        do : float
            Outer diameter of run (i.e. header) pipe

        tn : float
            Nomimal thickness of run (i.e. header) pipe
        """
        super(Sockolet, self).__init__(element, point)
        self.do = do
        self.tn = tn


@units.define(do="length", tn="length", dob="length", rx="length", tc="length")
class Sweepolet(Intersection):
    """Contoured integrally reinforced insert with butt-welded branch"""

    def __init__(self, element, point, do, tn, dob, rx, tc):
        """
        Parameters
        ----------
        code : str
            The code used to calculate the parameters

        do : float
            Outer diameter of run (i.e. header) pipe

        tn : float
            Nomimal thickness of run (i.e. header) pipe

        dob : float
            Outer diameter of branch pipe

        rx : float
            External crotch radius of welded-in contour insert

        tc : float
            Crotch thickness
        """
        super(Sweepolet, self).__init__(element, point)
        self.do = do
        self.tn = tn
        self.dob = dob
        self.rx = rx
        self.tc = tc


class ButtWeld(Connection):
    """Buttwelded piping connections"""

    def __init__(self, element, point):
        super(Welding, self).__init__(element, point)


class SIFContainer(EntityContainer):

    def __init__(self):
        super(SIFContainer, self).__init__()
        self.Welding = Welding
        self.Unreinforced = Unreinforced
        self.Reinforced = Reinforced
        self.Weldolet = Weldolet
        self.Sockolet = Sockolet
        self.Sweepolet = Sweepolet
        self.Weldolet = Weldolet
        self.ButtWeld = ButtWeld

    def apply(self, sifs=[], elements=None):
        """Apply sifs to elements.

        A reference for each sif is assigned to each element.

        .. note::
            One pipe element can be assigned multiple sifs.

        Parameters
        ----------
        sifs : list
            A list of sifs

        elements : list
            A list of elements. If elements is None, sifs are applied to all
            active elements.
        """
        if elements is None:
            elements = []

            for element in self.app.elements.active_objects:
                elements.append(element)

        for element in elements:
            element.sifs.update(sifs)
