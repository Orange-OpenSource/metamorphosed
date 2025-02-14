#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2022-2024,  Orange
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of Orange nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL ORANGE BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke


# utilities to compare AMR graphes using either Smatch or SmatchPP

from smatchpp import Smatchpp, solvers, data_helpers

from metamorphosed.smatch_pm import Smatch


class CompResult:
    def __init__(self):
        self.p = 0
        self.r = 0
        self.f1 = 0
        self.number_of_diffs = 0
        self.best_match_num = 0
        self.gold_triple_num = 0
        self.test_triple_num = 0
        self.instances1OK = set()
        self.rel1OK = set()
        self.instances2OK = set()
        self.rel2OK = set()

    def __repr__(self):
        return "F:%.2f goldtriples: %d testtriples: %d matchettriples: %d" % (self.f1, self.gold_triple_num, self.test_triple_num, self.best_match_num)


def compare(s1, s2, runs=1, use_smatchpp=False, align=False):
    compres = CompResult()

    sm = Smatch()
    if not use_smatchpp:
        best_match_num = 0
        for r in range(runs):
            best_match_num_2, compres.test_triple_num, compres.gold_triple_num, compres.instances1OK, compres.rel1OK, compres.instances2OK, compres.rel2OK = sm.get_amr_match(s1.replace("\n", " "), s2.replace("\n", " "))
            compres.best_match_num = max(best_match_num_2, compres.best_match_num)
    else:
        graph_reader = data_helpers.GoodmamiPenmanReader()
        ilp = solvers.ILP()
        measure = Smatchpp(graph_reader=graph_reader, alignmentsolver=ilp)
        match, optimization_status, alignment = measure.process_pair(s1.replace("\n", " "), s2.replace("\n", " "))
        #print("alignment", alignment)
        compres.test_triple_num = match["main"][2]
        compres.gold_triple_num = match["main"][3]
        compres.best_match_num = match["main"][1]

        if align:
            #measure = Smatchpp(graph_reader=graph_reader, alignmentsolver=None)
            g1 = measure.graph_reader.string2graph(s1)
            g1a = measure.graph_standardizer.standardize(g1)
            g2 = measure.graph_reader.string2graph(s2)
            g2a = measure.graph_standardizer.standardize(g2)
            g1b, g2b, v1, v2 = measure.graph_pair_preparer.prepare_get_vars(g1a, g2a)
            alignment, var_index, _ = measure.graph_aligner.align(g1b, g2b, v1, v2)
            var_map = measure.graph_aligner._get_var_map(alignment, var_index)
            interpretable_mapping = measure.graph_aligner._interpretable_mapping(var_map, g1b, g2b)
            # print("Mapping", interpretable_mapping)

            # calculate the lists of matching instances and matching relations as does Smatch
            matching_instances = {} # variable g1: variable g2
            for inst1, inst2 in interpretable_mapping:
                if inst1.startswith("None_") or inst2.startswith("None_"):
                    continue
                elems1 = inst1.split("_", 2)
                elems2 = inst2.split("_", 2)
                if elems1[2] == elems2[2]:
                    compres.instances1OK.add(elems1[1])
                    compres.instances2OK.add(elems2[1])
                matching_instances[elems1[1]] = elems2[1]

            g2 = set(g2)
            for s1, p1, o1 in g1:
                # find triples of g1 in g2, if so the relation is matched and OK
                if p1 == ":instance":
                    continue

                s2 = matching_instances.get(s1)
                if not s2:
                    continue

                # objects can be literals, in this case we take them as is
                # TODO: complete
                if o1[0] in '"0123456789+-' or o1 in ["imperative", "polite"]:
                    o2 = o1
                else:
                    o2 = matching_instances.get(o1)
                if not o2:
                    continue

                if (s2, p1, o2) in g2:
                    compres.rel1OK.add((s1, p1, o1))
                    compres.rel1OK.add((o1, p1 + "-of", s1))
                    compres.rel2OK.add((s2, p1, o2))
                    compres.rel2OK.add((o2, p1 + "-of", s2))

    compres.number_of_diffs = int(max(compres.test_triple_num, compres.gold_triple_num) - compres.best_match_num)
    compres.p, compres.r, compres.f1 = sm.compute_f(compres.best_match_num, compres.test_triple_num, compres.gold_triple_num)

    return compres
