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

"""Element code checking"""


from itertools import zip_longest
import math

from psi.loadcase import LoadCase, LoadComb
from psi import units


def element_codecheck(points, loadcase, element, S):
    """Perform element code checking based on the assigned code for primary
    load cases and load combinations.
    """
    ndof = 6
    idxi = points.index(element.from_point)
    idxj = points.index(element.to_point)

    # node and corresponding dof (start, finish)
    niqi, niqj = idxi*ndof, idxi*ndof + ndof
    njqi, njqj = idxj*ndof, idxj*ndof + ndof

    with units.Units(user_units="code_english"):
        # Note: units are changed to code_english for the moments
        # to have units of inch*lbf per code requirement
        # code equations are units specific, i.e. imperial or si

        if isinstance(loadcase, LoadCase):
            fori = loadcase.forces.results[niqi:niqj, 0]
            forj = loadcase.forces.results[njqi:njqj, 0]

            # code stresses per element node i and j for each loadcase
            shoop = element.code.shoop(element, loadcase)

            # pressure stress is same at both nodes
            slp = element.code.slp(element, loadcase)

            saxi = element.code.sax(element, fori)
            saxj = element.code.sax(element, forj)

            stori = element.code.stor(element, fori)
            storj = element.code.stor(element, forj)

            slbi = element.code.slb(element, element.from_point, fori)
            slbj = element.code.slb(element, element.to_point, forj)

            # total code stress
            sli = element.code.sl(element, loadcase, element.from_point, fori)
            slj = element.code.sl(element, loadcase, element.to_point, forj)

            # fitting and nodal sifs, sum together, take max or average?
            sifi = element.code.sifi(element, element.from_point)
            sifo = element.code.sifo(element, element.to_point)

            sallowi = element.code.sallow(element, loadcase, fori)
            sallowj = element.code.sallow(element, loadcase, forj)

            try:
                sratioi = sli / sallowi     # code ratio at node i
                sratioj = slj / sallowj     # code ratio at node j
            except ZeroDivisionError:
                sratioi = 0
                sratioj = 0

        elif isinstance(loadcase, LoadComb):
            # fitting and nodal sifs, sum together, take max or average?
            sifi = element.code.sifi(element)
            sifo = element.code.sifo(element)

            loadcomb = loadcase
            shoop_list, slp_list = [], []
            saxi_list, stori_list, slbi_list, sli_list = [], [], [], []
            saxj_list, storj_list, slbj_list, slj_list = [], [], [], []
            for factor, loadcase in zip_longest(loadcomb.factors,
                                                loadcomb.loadcases,
                                                fillvalue=1):
                fori = loadcase.forces.results[niqi:niqj, 0]
                forj = loadcase.forces.results[njqi:njqj, 0]

                shoop_list.append(factor * element.code.shoop(element, loadcase))
                slp_list.append(factor * element.code.slp(element, loadcase))

                saxi_list.append(factor * element.code.sax(element, fori))
                saxj_list.append(factor * element.code.sax(element, forj))

                stori_list.append(factor * element.code.stor(element, fori))
                storj_list.append(factor * element.code.stor(element, forj))

                slbi_list.append(factor * element.code.slb(element,
                                 element.from_point, fori))
                slbj_list.append(factor * element.code.slb(element,
                                 element.to_point, forj))

                # total code stress
                sli_list.append(element.code.sl(element, loadcase,
                                element.from_point, fori))
                slj_list.append(element.code.sl(element, loadcase,
                                element.to_point, forj))

            if loadcomb.method == "scaler":
                shoop = sum(shoop_list)
                slp = sum(slp_list)

                saxi = sum(saxi_list)
                saxj = sum(saxj_list)

                stori = sum(stori_list)
                storj = sum(storj_list)

                slbi = sum(slbi_list)
                slbj = sum(slbj_list)

                sli = sum(sli_list)
                slj = sum(slj_list)

            elif loadcomb.method == "algebraic":
                # stress per algebraic combination of forces
                fori = loadcomb.forces.results[niqi:niqj, 0]
                forj = loadcomb.forces.results[njqi:njqj, 0]

                shoop = sum(shoop_list)
                slp = sum(slp_list)

                saxi = element.code.sax(element, fori)
                saxj = element.code.sax(element, forj)

                stori = element.code.stor(element, fori)
                storj = element.code.stor(element, forj)

                slbi = element.code.slb(element, element.from_point, fori)
                slbj = element.code.slb(element, element.to_point, forj)

                # total code stress
                sli = element.code.sl(element, loadcase,
                                      element.from_point, fori)
                slj = element.code.sl(element, loadcase,
                                      element.to_point, forj)

            elif loadcomb.method == "srss":
                # note: sign of factor has no effect, always positive
                shoop = sum([s**2 for s in shoop_list])
                slp = sum([s**2 for s in slp_list])

                saxi = sum([s**2 for s in saxi_list])
                saxj = sum([s**2 for s in saxj_list])

                stori = sum([s**2 for s in stori_list])
                storj = sum([s**2 for s in storj_list])

                slbi = sum([s**2 for s in slbi_list])
                slbj = sum([s**2 for s in slbj_list])

                sli = sum([s**2 for s in sli_list])
                slj = sum([s**2 for s in slj_list])

            elif loadcomb.method == "abs":
                shoop = sum([abs(s) for s in shoop_list])
                slp = sum([abs(s) for s in slp_list])

                saxi = sum([abs(s) for s in saxi_list])
                saxj = sum([abs(s) for s in saxj_list])

                stori = sum([abs(s) for s in stori_list])
                storj = sum([abs(s) for s in storj_list])

                slbi = sum([abs(s) for s in slbi_list])
                slbj = sum([abs(s) for s in slbj_list])

                sli = sum([abs(s) for s in sli_list])
                slj = sum([abs(s) for s in slj_list])

            elif loadcomb.method == "signmax":
                shoop = max(shoop_list)
                slp = max(slp_list)

                saxi = max(saxi_list)
                saxj = max(saxj_list)

                stori = max(stori_list)
                storj = max(storj_list)

                slbi = max(slbi_list)
                slbj = max(slbj_list)

                sli = max(sli_list)
                slj = max(slj_list)

            elif loadcomb.method == "signmin":
                shoop = min(shoop_list)
                slp = min(slp_list)

                saxi = min(saxi_list)
                saxj = min(saxj_list)

                stori = min(stori_list)
                storj = min(storj_list)

                slbi = min(slbi_list)
                slbj = min(slbj_list)

                sli = min(sli_list)
                slj = min(slj_list)

            # take the sqrt last
            if loadcomb.method == "srss":
                shoop = math.sqrt(shoop)
                slp = math.sqrt(slp)

                saxi = math.sqrt(saxi)
                saxj = math.sqrt(saxj)

                stori = math.sqrt(stori)
                storj = math.sqrt(storj)

                slbi = math.sqrt(slbi)
                slbj = math.sqrt(slbj)

                sli = math.sqrt(sli)
                slj = math.sqrt(slj)

            # allowable loadcomb stress
            sallowi_list = []
            sallowj_list = []
            # determine the loadcomb code stress allowable
            for loadcase in loadcomb.loadcases:
                stype = loadcase.stype              # save type
                loadcase.stype = loadcomb.stype     # change to loadcomb type

                fori = loadcase.forces.results[niqi:niqj, 0]
                forj = loadcase.forces.results[njqi:njqj, 0]

                # calculate loadcomb allowable
                sallowi = element.code.sallow(element, loadcase, fori)
                sallowi_list.append(sallowi)

                sallowj = element.code.sallow(element, loadcase, forj)
                sallowj_list.append(sallowj)

                # revert to loadcase stype
                loadcase.stype = stype
            sallowi = min(sallowi_list)
            sallowj = min(sallowj_list)

            try:
                sratioi = sli / sallowi     # code ratio at node i
                sratioj = slj / sallowj     # code ratio at node j
            except ZeroDivisionError:
                sratioi = 0
                sratioj = 0

        # hoop, sax, stor, slp, slb, sl, sifi, sifj, sallow, ir
        # take the worst code stress at node
        if sratioi > S[idxi, -1]:
            S[idxi, :10] = (shoop, saxi, stori, slp, slbi, sli,
                            sifi, sifo, sallowi, sratioi)

        if sratioj > S[idxj, -1]:
            S[idxj, :10] = (shoop, saxj, storj, slp, slbj, slj,
                            sifi, sifo, sallowj, sratioj)

        # TODO : Implement Ma, Mb and Mc calculation loads
        # for each loadcase where Ma is for sustained, Mb is
        # for occasional and Mc is for expansion type loads
        # This applies to code stress calculations only
