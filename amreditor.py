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

# version 3.3.0 as of 11th July 2024

import re
import readline

import penman
from graphviz import Digraph

import graph
from reification import getInstance

VERSION = "3.3.0"

# terminology
# instance  a / ...
# concept .. /rise-01
# relation :ARG0
# literal -, "Mary", 12, 12.3


orangecolors = {
    ":ARG0": "#ff7900",
    ":ARG1": "#9164cd",
    ":ARG3": "#ffb4e6",
    ":ARG4": "#50be87",
    ":ARG2": "#4bb4e6",
    ":ARG5": "#ffdc00",
    "charteYellowBright": "#fff6b6",
    ":beneficiary": "#d9c2f0",
    "chartePinkBright": "#ffe8f7",
    ":snt1": "#b8ebd6",
    ":snt2": "#b8ebd6",
    ":snt3": "#b8ebd6",
    ":snt4": "#b8ebd6",
    "charteBlueBright": "#b5e8f7",
    ":ord": "#d6d6d6",
    ":mod": "#ffb400",
    ":name": "#492191",
    ":location": "#ff8ad4",
    ":destination": "#ff8ad4",
    ":manner": "#0a6e31",
    ":time": "#085ebd",
    ":day": "#085ebd",
    ":month": "#085ebd",
    ":dayperiod": "#085ebd",
    ":op1": "#595959",
    ":op2": "#595959",
    ":op3": "#595959",
    ":op4": "#595959",
    ":value": "#595959",
    "EN": "#ffe5cc",
    }

ONESPACE = re.compile("[ \n\t]+")


class AMRProcessor:
    pbframes = None

    def __init__(self, inserver=True):
        self.triples = []
        self.top = None
        self.vars = {} # var: concept
        self.varletters = {} # first letter: set()
        self.inserver = inserver # we are in an server instance
        self.isDisconnected = False
        self.isNumber = re.compile(r"^[+-]?\d*\.?\d+$")
        self.lastpm = None
        self.valid = True
        self.isparsed = False
        self.modified = False

    def __str__(self):
        return self.lastpm

    def write(self, ofp):
        if not self.valid or not self.isparsed:
            print(self.lastpm, file=ofp)
        elif self.isDisconnected:
            #print("# TODO\n", file=ofp)
            #print(self.lastpm.replace("\n\n", "\n"), file=ofp)
            # get tops of all partial penmans and create a pseudo head
            #print("LAST",self.lastpm.split("\n\n"))
            #print("TRS", self.triples)
            pms = self.lastpm.split("\n\n")
            # find top for all
            tops = []
            alltriples = []
            for pm in pms:
                g = penman.decode(pm)
                #print("hhhh", g, dir(g))
                alltriples += g.triples
                tops.append(g.top)
            alltriples.insert(0, ("mmmm", ":instance", "multigraph"))
            for i, t in enumerate(tops, start=1):
                alltriples.append(("mmmm", ":snt%d" % i, t))
            pm = penman.encode(penman.Graph(alltriples, top="mmmm"))
            #print("eeeee", alltriples)
            print(pm, file=ofp)

        else:
            #print("AAA", self.lastpm)
            #print("BBB", self.triples)
            #print("CCC", self.top)
            pm = penman.encode(penman.Graph(self.triples, top=self.top))
            print(pm, file=ofp)
        print(file=ofp)
        self.modified = False

    def findamr(self, regex):
        if self.lastpm:
            rtc = re.finditer(regex, self.lastpm)
            if rtc:
                return rtc
        return []

    def readpenman(self, amr):
        # amr is in penman format
        self.triples = []
        self.valid = True
        self.isparsed = True
        amr = ONESPACE.sub(" ", amr)
        #amr = amr.replace("\n", "")
        amrs = amr.replace(") (", ")\n(").split("\n")
        self.varletters = {}
        try:
            usedvariables = set()
            defined_instances = set()
            for i, amr in enumerate(amrs, start=1):
                # if the graph turns out to be disconnected we must be sure
                # that each variable is only used in a single graph
                tree = penman.parse(amr)
                self.top = None

                for branch in tree.nodes():
                    #print("==used", usedvariables)
                    #print("==vars", self.varletters)
                    s = branch[0]
                    if not self.top:
                        self.top = s
                    #print(s)
                    if s in usedvariables:
                        s = "%s_new%d" % (s, i)

                    for po in branch[1]:
                        #print("   ", po)
                        p = po[0]
                        o = po[1]

                        if p == "/":
                            p = ":instance"
                            self.vars[s] = o
                            if not s[0] in self.varletters:
                                self.varletters[s[0]] = set([s])
                            else:
                                self.varletters[s[0]].add(s)
                        if not isinstance(o, str):
                            o = o[0]

                        if o in usedvariables:
                            o = "%s_new%d" % (o, i)
                        #print("TR", s,p,o)
                        if p == ":instance":
                            # duplicated "v :instance concept" create errors in penman.encode(triples)
                            if s in defined_instances:
                                continue
                            defined_instances.add(s)
                        self.triples.append((s, p, o))

                #usedvariables.update(self.varletters.keys())
                for varnames in self.varletters.values():
                    usedvariables.update(varnames)

        except penman.exceptions.DecodeError as e:
            self.lastpm = amr
            self.valid = False
            self.parsererror = {"lineno": e.lineno,
                                "offset": e.offset,
                                "message": e.message,
                                "text": e.text}
        except Exception as e:
            self.lastpm = amr
            self.valid = False
            self.parsererror = {"lineno": "?",
                                "offset": "?",
                                "message": e,
                                "text": e}

    def newvar(self, concept):
        #return "v%d" % len(self.vars)
        letter = concept[0]
        if letter not in self.varletters:
            self.varletters[letter] = set([letter])
            return letter
        else:
            i = 1
            while "%c%d" % (letter, i) in self.varletters[letter]:
                i += 1
            var = "%c%d" % (letter, i)
            self.varletters[letter].add(var)
            return var

    def getvars(self, concept):
        # find all instances of a given concept
        insts = []
        for k, v in self.vars.items():
            if concept == v:
                insts.append(k)
        return insts

    def dot(self, highlightinstances=None, highlightrelations=None, format="svg"):
        # highlight instances and relations NOT in highlightinstances and highlightrelations
        graph_attr = {#'rankdir':'LR'
        }
        kwargsinit = {
            "fontname": "Lato",
            "style": "filled",
            "fillcolor": "white"
            }

        graph = Digraph('amr_graph', format=format, graph_attr=graph_attr)
        for s, p, o in self.triples:
            kwargs = kwargsinit.copy()

            if p == ":instance":
                ibg = "white"
                if highlightinstances and s not in highlightinstances:
                    kwargs = {"fontname": "Lato",  #"Lato Black",
                              "style": "filled",
                              "fillcolor": "#ff7900"} #orangecolors.get(":snt1")}

                if AMRProcessor.pbframes:
                    argdoc = AMRProcessor.pbframes.getargdoc(o)
                    lines = []
                    if argdoc:
                        lines.append("%s: %s" % (o, argdoc["descr"]))
                        for r in sorted(argdoc["roles"], key=lambda x: x["n"]):
                            vn = ""
                            if r["vn"]:
                                vn = " (%s)" % ", ".join(r["vn"])
                            lines.append(" - %s %s%s" % (r["n"], r["descr"], vn))

                    # this adds a tooltip, but changes the SVG drastically
                    kwargs["tooltip"] = "\n".join(lines)

                graph.node("%s" % s, label="%s/%s" % (s, o), shape="box",
                           id="node %s %s" % (s, o),
                           #URL=branch[0],
                           #fillcolor=ibg,
                           #style="filled",
                           **kwargs
                           )
            else:
                onodeid = o
                pp = p
                kwargs["fontcolor"] = orangecolors.get(p.replace("-of", ""), "black")
                if highlightrelations and (s, p, o) not in highlightrelations:
                    kwargs["fontname"] = "Lato" # "Lato Black" }
                    kwargs["fontcolor"] = "black"
                    pp = '< <table border="0"> <tr><td bgcolor="%s">%s</td></tr></table> >' % ("#ff7900", #orangecolors.get(":snt1"),
                                                                                               p)

                if o not in self.vars:
                    oo = o.replace('"', 'DQUOTE').replace(':', 'COLON').replace('\\', 'BSLASH')
                    onodeid = "%s_%s" % (s, oo)
                    kwargs["fillcolor"] = orangecolors.get("EN")
                    kwargs["style"] = "filled"
                    #kwargs["tooltip"] = "qsqqs\n<b>f</b>illed"

                    graph.node(onodeid, label="%s" % (o),
                               id="literal %s %s %s" % (s, p, o),
                               #style="filled",
                               color=orangecolors.get("EN"),
                               #fillcolor=orangecolors.get("EN"),
                               #URL=branch[0],
                               **kwargs)
                #print("ZZZZ", s,p,o)

                kwargs["fillcolor"] = orangecolors.get(p.replace("-of", ""), "black")

                graph.edge(s, onodeid, label=pp,
                           id="edge#%s#%s#%s" % (s, o, p),
                           color=orangecolors.get(p.replace("-of", ""), "black"),
                           #fontcolor=orangecolors.get(p.replace("-of", ""), "black"),
                           **kwargs)
        #print("RRRRR", graph) # dot sources
        return graph.pipe()

    def show(self, highlightinstances=None, highlightrelations=None, format="svg"):
        if self.inserver:
            #print(self.triples, self.vars)
            #for tr in self.triples:
            #    print("SHOWTR", tr)
            #print(self.vars)

            if not self.valid:
                return self.lastpm, None

            try:
                pm = penman.encode(penman.Graph(self.triples, top=self.top))
                self.lastpm = pm
                #a = amr2dot.AMR2DOT(format="svg", font="Lato", instances=False, lr=False, bw=False)
                #a.build(pm)
                #self.lastsvg = a.graph.pipe()
                self.readpenman(pm)
                self.lastsvg = self.dot(highlightinstances, highlightrelations, format=format)
                self.isDisconnected = False
            except penman.exceptions.LayoutError:
                #a = amr2dot.AMR2DOT(format="svg", font="Lato", instances=False, lr=False, bw=False)
                #a.buildtriples(self.triples)
                #self.lastsvg = a.graph.pipe()
                self.lastsvg = self.dot(format=format)

                noninst = []
                for tr in self.triples:
                    noninst.append(tr)
                    #if tr[1] != ":instance":
                    #    noninst.append(tr)
                    #else:
                    #    noninst.append((tr[0], "/", tr[2]))
                sgs = graph.findsubgraphs(noninst)

                pms = []
                for sg in sgs:
                    triples = []
                    #cset = set(sg)

                    for tr in self.triples:
                        if tr[0] in sg or (tr[2] in sg and tr[1] != ":instance"):
                            triples.append(tr)
                    pm = penman.encode(penman.Graph(triples))
                    pms.append(pm)
                    #print("DISCONNECTED", pm)

                self.lastpm = "\n\n".join(pms)
                if len(sgs) > 1:
                    self.isDisconnected = True
                else:
                    self.isDisconnected = False

            return "%s" % self.lastpm, self.lastsvg
        else:
            try:
                pm = penman.encode(penman.Graph(self.triples, top=self.top))
                print(pm)
                for i, t in enumerate(self.triples):
                    print("%d" % (i + 1), t)
            except penman.exceptions.LayoutError:
                print("not yet correct")
                print(self.triples)

    def validate(self, valfuncs=[]):
        rtc = []
        for valfunc in valfuncs:
            rtc += valfunc(self.triples)
        edges = set() # (s,o)
        outedges = set() # (s,p)

        sntNN = {} # startvar, num
        opNN = {} # startvar, num
        for s, p, o in self.triples:
            # find multiple edges between same nodes
            if p == ":instance":
                continue
            if (s, o) in edges:
                rtc.append("more than one relation between « %s » and « %s » (%s)" % (s, o, p))
            if (o, s) in edges:
                rtc.append("more than one relation between « %s » and « %s » (inverted) (%s)" % (s, o, p))
            edges.add((s, o))

            # find missing :sntNN or :opNN
            if p.startswith(":snt"):
                if s not in sntNN:
                    sntNN[s] = [p[4:]]
                else:
                    sntNN[s].append(p[4:])
            if p.startswith(":op"):
                if s not in opNN:
                    opNN[s] = [p[3:]]
                else:
                    opNN[s].append(p[3:])
            # find identical edges starting from same node
            if (s, p) in outedges:
                rtc.append("more than one relation label « %s » start at instance « %s »" % (p, s))
            if not p.endswith("-of") and p not in [":mod", ":time"]:
                outedges.add((s, p))

        for var in sntNN:
            for i, num in enumerate(sntNN[var], start=1):
                if str(i) != num:
                    rtc.append("incoherent :sntNN numbering for instance « %s »: %s" % (var, ", ".join(sntNN[var])))
        for var in opNN:
            for i, num in enumerate(opNN[var], start=1):
                if str(i) != num:
                    rtc.append("incoherent :opNN numbering for instance « %s »: %s" % (var, ", ".join(opNN[var])))
        if self.isDisconnected:
            rtc.append("the graph is disconnected (invalid)")
        return rtc

    def settop(self, topvar):
        if topvar in self.vars:
            self.top = topvar

            for tr in self.triples:
                if self.top == tr[2] and tr[1].endswith("-of"):
                    self.triples.index(tr)
                    self.triples.remove(tr)
                    self.triples.insert(0, (tr[2], tr[1][:-3], tr[0]))
        else:
            return "invalid instance variable %s" % topvar
        #self.show()

    def reify(self, reify):
        reificator = getInstance()
        if reificator:
            npm = reificator.reify(self.lastpm, only=reify)
            self.readpenman(npm)

    def dereify(self, dereify):
        reificator = getInstance()
        if reificator:
            #print("zzzz", self.lastpm)
            npm, msgs = reificator.dereify(self.lastpm, only=dereify)
            #triples, msgs = reificator.dereify(self.lastpm, returntriples=True, only=dereify)
            if not msgs:
                self.readpenman(npm)

        return msgs

    def addconcept(self, concept):
        var = self.newvar(concept)
        if not self.top:
            self.top = var
        if var in self.vars:
            # should never happen
            print("VAR exists", self.vars[var])
            return 0
        else:
            self.vars[var] = concept
            self.triples.append((var, ":instance", concept))
        #self.show()
        return var

#    # TODO: we can have more than once a node with the same number
#    def addnumber(self, number):
#        if number in self.vars:
#            print("VAR exists", self.vars[number])
#            return 0
#        else:
#            self.vars[number] = number
#        self.show()

    def modconcept(self, var, newconcept):
        if var in self.vars:
            for tr in self.triples:
                if tr[0] == var and tr[1] == ":instance":
                    pos = self.triples.index(tr)
                    self.triples.remove(tr)
                    self.triples.insert(pos, (tr[0], ":instance", newconcept))
                    break
            self.vars[var] = newconcept

    def modedge(self, modedge_start, modedge_end, newedge):
        for tr in self.triples:
            if tr[0] == modedge_start and tr[2] == modedge_end:
                pos = self.triples.index(tr)
                self.triples.remove(tr)
                self.triples.insert(pos, (tr[0], newedge, tr[2]))
                break

    def moveedge(self, modedge_start, modedge_end, newedge, newstart):
        if newstart not in self.vars:
            return "new source instance « %s » does not exist" % newstart

        for tr in self.triples:
            if tr[0] == modedge_start and tr[2] == modedge_end:
                pos = self.triples.index(tr)
                self.triples.remove(tr)
                self.triples.insert(pos, (newstart, newedge, tr[2]))
                break
        return None

    def delliteral(self, litid, litedge, dellit):
        for tr in self.triples:
            if tr[0] == litid and tr[1] == litedge and (tr[2] == '"%s"' % dellit or tr[2] == dellit):
                self.triples.remove(tr)
                return None
        return "literal and relation <%s %s %s> do not exist" % (litid, litedge, dellit)

    def modliteral(self, litid, litedge, newlit):
        for tr in self.triples:
            #print("llll", tr, litid, litedge)
            if tr[0] == litid and tr[1] == litedge:
                pos = self.triples.index(tr)
                self.triples.remove(tr)
                if not self.isNumber.match(newlit) and newlit not in "-+":
                    newlit = '"%s"' % newlit.replace('"', '')
                self.triples.insert(pos, (tr[0], tr[1], newlit))
                break

    def addliteral(self, literalof, relationforliteral, newlit):
        if literalof not in self.vars:
            return "new source instance « %s » does not exist" % literalof
        else:
            if not self.isNumber.match(newlit) and newlit not in "-+":
                newlit = '"%s"' % newlit.replace('"', '')
            self.triples.append((literalof, relationforliteral, newlit))

    def addedge(self, start, end, label):
        # TODO check no second edge with same label from given node
        if label == ":instance": # or not in validlabels():
            return "cannot add an :instance edge"

        if start.startswith("//"):
            # find instance of given concept, or create new concept first
            insts = self.getvars(start[2:])
            if insts:
                start = insts[0]
            else:
                start = self.addconcept(start[2:])
        elif start[0] == "/":
            # create new concept first
            start = self.addconcept(start[1:])

        if end.startswith("//"):
            # find instance of given concept, or create new concept first
            insts = self.getvars(end[2:])
            if insts:
                end = insts[0]
            else:
                end = self.addconcept(end[2:])
        elif end[0] == "/":
            # create new concept first
            end = self.addconcept(end[1:])

        if start not in self.vars:
            #print("Missing startvar « %s »" % (start))
            return "Cannot add relation: start instance « %s » not defined" % (start)

        if not self.isNumber.match(end) and end[0] != '"' and end not in "-+" and end not in self.vars:
            #print("Missing endvar « %s »" % (end))
            return "Cannot add relation: end instance « %s » not defined" % (start)
        else:

            if label[0] != ":":
                label = ":" + label

            self.triples.append((start, label, end))
        #self.show()
        return None

    def deledge(self, start, end, label):
        todelete = []
        for ix, tr in enumerate(self.triples):
            #print("tttt", ix,tr, start, label, end)
            if tr[0] == start and tr[2] == end or end.startswith("stringnode"):
                if tr[1] == label:
                    todelete.append(tr)
                elif tr[1] + "-of" == label:
                    todelete.append(tr)
        for tr in todelete:
            self.triples.remove(tr)
        #for ix,tr in enumerate(self.triples):
        #    print("uuuu", ix, tr)

        #self.show()

    def delinstance(self, var):
        if var in self.vars:
            todelete = []
            for tr in self.triples:
                if tr[0] == var or tr[2] == var:
                    todelete.append(tr)
            del self.vars[var]
            for tr in todelete:
                self.triples.remove(tr)
            if self.top == var:
                self.top = None
        #self.show()

    def process(self, line):
        # concept
        # top var
        # var1 edge var2
        # - start edge
        elems = line.split()
        if len(elems) == 2:
            if elems[0] == "top":
                self.settop(elems[1])
        elif len(elems) == 1:
            self.addconcept(elems[0])
        else:
            if elems[0] == "-":
                self.deledge(elems[1], elems[2])
            else:
                self.addedge(elems[0], elems[2], elems[1])


if __name__ == "__main__":
    aa = AMRProcessor(inserver=False)
    #for l in tr:
    #    aa.process(l)
    aa.readpenman("(c / cat)")
    aa.show()

    line = input(">> ")
    while line:
        aa.process(line)
        aa.show()
        line = input(">> ")
