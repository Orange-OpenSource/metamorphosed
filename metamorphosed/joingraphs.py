#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2024,  Orange
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

# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke


import penman
import metamorphosed.amreditor as amreditor
import metamorphosed.amrdoc as amrdoc
from metamorphosed.exception import ServerException


# join two graphs into one, and merge instances indicated in corefs
def joingraphs(graph1, graph2, corefs, top=None):
    #print("G1", graph1)
    #print("G2", graph2)

    if isinstance(graph1, str):
        graph1 = penman.decode(graph1)
    if isinstance(graph2, str):
        graph2 = penman.decode(graph2)

    # un dict with variables and concepts of graphs
    g1_concepts = {} # var: concept
    for s, p, o in graph1.instances():
        g1_concepts[s] = o

    g2_concepts = {} # var: concept
    for s, p, o in graph2.instances():
        g2_concepts[s] = o

    v2match = {} # v2: v1
    for v1, v2 in corefs:
        #v1 = "a" + v1
        #v2 = "b" + v2
        if v1 not in g1_concepts:
            #print("%s not in graph1" % v1)
            raise ServerException("Graph1 does not have an instance: %s" % v1)
            # raise Exception
            continue
        if v2 not in g2_concepts:
            #print("%s not in graph2" % v2)
            raise ServerException("Graph2 does not have an instance: %s" % v2)
            # raise Exception
            continue
        if g1_concepts[v1] != g2_concepts[v2]:
            print("instances not maching: %s:%s != %s/%s" % (v1, g1_concepts[v1],
                                                             v2, g2_concepts[v2]))
        v2match["b" + v2] = "a" + v1

    # rename variables of second graph to avoid usage of the same variable differently
    g1_vars = graph1.variables()

    finaltriples = []
    finaltriples_no_duplicates = set()
    # take the entire first graph
    for s, p, o in graph1.triples:
        if o in g1_concepts:
            o = "a" + o
        #print("ZZZZ", ("a" + s, p, o))
        finaltriples.append(("a" + s, p, o))
        finaltriples_no_duplicates.add(("a" + s, p, o))

    oldnew = {} #var-gr2: newvar-gr2  # variables of graphe2 which must be renamed
    for s, p, o in graph2.triples:
        s = "b" + s
        if o in g2_concepts:
            o = "b" + o

        # ignore the instances mentioned in coref
        if p == ":instance" and s in v2match:
            continue
        if s in v2match:
            s = v2match[s]
        elif s in oldnew:
            s = oldnew[s]

        if o in v2match:
            o = v2match[o]
        elif o in oldnew:
            o = oldnew[o]

        if (s, p, o) not in finaltriples_no_duplicates:
            finaltriples.append((s, p, o))
            finaltriples_no_duplicates.add((s, p, o))

    #for i,tr in enumerate(finaltriples, 1):
    #    print(i,tr)
    ngr = penman.Graph(finaltriples, top=top)
    ntree = penman.configure(ngr)
    ntree.reset_variables(fmt="{prefix}{j}")
    npm = penman.format(ntree)
    #print("\n1:\n", npm)

    #npm = penman.encode(penman.Graph(finaltriples, top=top))
    #print("\n2:\n", npm)
    return str(npm)


def testfile(filename):
    doc = amrdoc.AMRdoc(filename)

    lastsent = None
    for sent in doc.sentences:
        if not lastsent:
            lastsent = sent.amr
            continue
        corefs = []
        top = None
        for c in sent.comments:
            if c.startswith("::coref"):
                elems = c.split()
                for coref in elems[1:]:
                    corefs.append(coref.split(","))
            elif c.startswith("::top"):
                top = c.split()[-1]
        jg = joingraphs(lastsent, sent.amr, corefs, top)
        print(jg)
        show(jg)
        lastsent = jg


def show(pm):
    ae = amreditor.AMRProcessor(inserver=False)
    ae.readpenman(pm)
    #ae.reinitvars()
    pdf = ae.dot(format="svg")
    #print(ae.varletters)
    #for i,tr in enumerate(ae.triples, 1):
    #    print("   ", i, tr)
    ofp = open("jg.svg", "w")
    print(pdf.decode("utf8"), file=ofp)
    ofp.close()
    input("hit <ENTER> ")


def test():
    g1 = """(x1 / rate-entity-91
        :ARG1 (x2 / income)
        :ARG2 (x3 / person))
        """

    g2 = """(p / propose-01
        :ARG1 (c / cause-01
            :ARG0 (ii / income
                :ARG1-of (l / low-04))
            :ARG1 (g / grieve-01))
        :ARG0-of (p2 / prompt-01
            :ARG1 (r / rebel-01
                :instrument (a / arm))))
                """
    c = [("x2", "ii")]
    jg = joingraphs(g1, g2, c)
    show(jg)

    gb1 = """(a / and
        :op1 (d / defeat-01)
        :op2 (c / control-01))
        """

    gb2 = """(d / defeat-01
      :ARG0 (h / he)
        :ARG1 (p / person
            :ARG0-of (h2 / have-rel-role-91
                :ARG1 h
                :ARG2 (e / enemy)))
        :location (c / country
            :name (n / name
                :op1 "Thessaly")))
                """
    cb = [("d", "d")]

    jg = joingraphs(gb1, gb2, cb)
    show(jg)

    gc1 = """(c / control-01
        :ARG0 (h / he)
        :ARG1 (r / region
            :mod (t / this))
        :ARG1-of (f / firm-03)
        :time (b / by
            :op1 (d / date-entity
                :year 352)))"""

    cb = [("c", "c"), ("h", "h")]

    jg = joingraphs(jg, gc1, cb)
    show(jg)

    gd1 = """(l / live-01
    :ARG0 (f / family
        :quant (a / around
            :op1 40)
        :mod (o / only))
    :location (t / there)
    :time (t2 / time
        :mod (t3 / this)))
        """

    gd2 = """
    (f / family
        :accompanier (a / and
            :op1 (l / land
                :purpose (f2 / farm-01)
                :ARG1-of (g / good-02)
                :quant (p / plenty))
            :op2 (g2 / graze-01
                :purpose (c / cattle))))
    """
    cd = [("f", "f")]
    jg = joingraphs(gd1, gd2, cd)
    show(jg)


def main():
    import os
    import sys

    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]):
            testfile(sys.argv[1])
        else:
            test()
    else:
        # simple interactive test
        g1 = []
        print("GRAPH 1")
        while True:
            line = input()
            if line:
                g1.append(line.strip())
            else:
                break

        g2 = []
        print("GRAPH 2")
        while True:
            line = input()
            if line:
                g2.append(line.strip())
            else:
                break

        cref = []
        print("COREFS")
        while True:
            line = input()
            if line:
                elems = line.split()
                cref.append((elems[0], elems[1]))
            else:
                break
        print("TOP")
        top = input()
        if not top:
            top = None
        print("top <%s> <%s> <%s> <%s>" % (g1, g2, cref, top))
        jg = joingraphs("\n".join(g1), "\n".join(g2), cref, top)
        #print(jg)
        #ae = amreditor.AMRProcessor(inserver=False)
        #ae.readpenman(jg)
        #ae.reinitvars()
        #pdf = ae.dot(format="svg")
        ##print(ae.varletters)
        #ofp = open("jg.svg", "w")
        #print(pdf.decode("utf8"), file=ofp)
        #ofp.close()
        show(jg)
