#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2022-2025,  Orange
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

# version 5.0.0rc as of 22nd November 2025

import io
import re
import readline
import sys

import penman
from graphviz import Digraph

import metamorphosed.graph as graph
from metamorphosed.reification import getInstance
import metamorphosed.amr_comparison as amr_comparison


VERSION = "5.0.0rc"

# terminology
# instance  a / ...
# concept .. /rise-01
# relation :ARG0
# literal -, "Mary", 12, 12.3


orangecolors = {
    ":ARG0": "#ff7900",
    ":actor": "#ff7900",
    ":ARG1": "#9164cd",
    ":affectee": "#9164cd",
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
    ":place": "#ff8ad4",
    ":destination": "#ff8ad4",
    ":manner": "#0a6e31",
    ":aspect": "#0a6e31",
    ":time": "#085ebd",
    ":day": "#085ebd",
    ":month": "#085ebd",
    ":dayperiod": "#085ebd",
    ":op1": "#595959",
    ":op2": "#595959",
    ":op3": "#595959",
    ":op4": "#595959",
    ":value": "#595959",
    ":todo": "#ff1111",
    ":rel": "#ff1111",
    "EN": "#ffe5cc",
    }

colorlist = [
    "#ffe5cc", #    "charteOrangeBright"
    "#fff6b6", #    "charteYellowBright"
    "#d9c2f0", #    "charteVioletBright"
    "#ffe8f7", #    "chartePinkBright"
    "#b8ebd6", #    "charteGreenBright"
    "#b5e8f7", #    "charteBlueBright"
    "#d6d6d6", #    "charteGrayBright"
    ]

ONESPACE = re.compile("[ \n\t]+")


class AMRProcessor:
    pbframes = None

    def __init__(self, inserver=True):
        self.triples = []
        self.umr_varprefix = None # if not None, we deal with UMR graphs which have the sentence number as variable prefix
        self.top = None
        self.vars = {} # var: concept
        self.varletters = {} # first letter (after umr-prefix): set()
        self.inserver = inserver # we are in an server instance
        self.isDisconnected = False
        self.isNumber = re.compile(r"^[+-]?\d*\.?\d+$")
        self.isValidVar = re.compile(r"^[a-z][A-Za-z0-9_]*$")
        self.lastpm = None
        self.valid = True
        self.isparsed = False
        self.modified = False
        self.comments = []
        self.previous_modification = 0 # sent to client and must be still the same when client answers. If not another client was faster. In this cas we refuse the anwser of the first client who came to late

    def __str__(self):
        return self.lastpm

    def write(self):
        ofp = io.StringIO()
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
                alltriples += g.triples
                tops.append(g.top)
            alltriples.insert(0, ("mmmm", ":instance", "multigraph"))
            for i, t in enumerate(tops, start=1):
                alltriples.append(("mmmm", ":snt%d" % i, t))
            pm = penman.encode(penman.Graph(alltriples, top="mmmm"))
            # print("All triples", alltriples)
            print(pm, file=ofp)

        else:
            # print("LAST PM", self.lastpm)
            # print("TRIPLES", self.triples)
            # print("TOP    ", self.top)
            pm = penman.encode(penman.Graph(self.triples, top=self.top))
            print(pm, file=ofp)
        print(file=ofp)
        self.modified = False
        return ofp.getvalue()

    def findamr(self, regex):
        if self.lastpm:
            rtc = re.finditer(regex, self.lastpm)
            if rtc:
                return rtc
        return []

    def findsubgraph(self, sg_rdf):
        bindinglist = sg_rdf.cmp(self.lastpm)
        if not bindinglist:
            return []
        inst2concept = {}
        for s, _, o in sg_rdf.instances:
            inst2concept[s] = o

        concepts = []
        for bindings in bindinglist:
            #print("ZZZZ", bindings)
            for _, graphvar in bindings.items():
                gvar = graphvar.split("/")[-1]
                concepts.append(inst2concept.get(gvar, "null"))

        rtc = re.finditer("|".join(concepts), self.lastpm)
        return rtc

    def ooofindsubgraph(self, subgraph, smatchpp=False):
        # returns True if the subgraph is part of graph
        try:
            res = amr_comparison.compare(self.lastpm, subgraph, runs=1, use_smatchpp=smatchpp, align=True)
            psg = penman.decode(subgraph)
            subgraph_variables = psg.variables()
            #print("====", self.lastpm)
            #print(res.instances1OK)
            #print(res.instances2OK)
            #print(res.rel1OK)
            #print(res.rel2OK)
            #print(psg.edges())
            #print(psg.attributes())

            if subgraph_variables == res.instances2OK:
                # all variables of the subgraph are matched
                # now check whether literals also match: all edges and attributes of subgraph musst be in
                for s, p, o in psg.edges():
                    if (s, p, o) not in res.rel2OK:
                        #print("edge", s,p,o, "missing")
                        return []
                for s, p, o in psg.attributes():
                    if (s, p, o) not in res.rel2OK:
                        #print("attr", s,p,o, "missing")
                        return []

                # find first concept of subgraph in graph (for highlighting)
                firstinstance = psg.instances()[0]
                firstconcept = firstinstance[2]
                rtc = re.finditer(firstconcept, self.lastpm)
                return rtc
        except Exception as e:
            # no valid PENMAN, take subgraph as a regex...
            print("AMR Search error: %s" % e)
            return self.findamr(subgraph)

        return []

    def readpenman(self, amr):
        # AMR is in PENMAN format
        self.triples = []
        self.valid = True
        self.isparsed = True
        amr = ONESPACE.sub(" ", amr)
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
                    s = branch[0]
                    if not self.top:
                        self.top = s
                    # print(s)
                    if s in usedvariables:
                        s = "%s_new%d" % (s, i)
                    for po in branch[1]:
                        # print("   ", po)
                        p = po[0]
                        o = po[1]

                        if p == "/":
                            p = ":instance"
                            self.vars[s] = o
                            if self.umr_varprefix and s.startswith(self.umr_varprefix):
                                letter = s[len(self.umr_varprefix)]
                            else:
                                letter = s[0]

                            if letter not in self.varletters:
                                self.varletters[letter] = set([s])
                            else:
                                self.varletters[letter].add(s)
                        if not isinstance(o, str):
                            o = o[0]

                        if o in usedvariables:
                            o = "%s_new%d" % (o, i)
                        # print("TR", s,p,o)
                        if p == ":instance":
                            # duplicated "v :instance concept" create errors in penman.encode(triples)
                            if s in defined_instances:
                                continue
                            defined_instances.add(s)
                        self.triples.append((s, p, o))

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
        #print(self.varletters)
        #print(self.vars)
        #self.reinitvars()

    def newvar(self, concept):
        #return "v%d" % len(self.vars)
        letter = concept[0]

        pref = ""
        if self.umr_varprefix:
            # letter = self.umr_varprefix + concept[0]
            pref = self.umr_varprefix
        if letter not in self.varletters:
            self.varletters[letter] = set([pref + letter])
            return pref + letter
        else:
            i = 1
            while "%s%c%d" % (pref, letter, i) in self.varletters[letter]:
                i += 1
            var = "%s%c%d" % (pref, letter, i)
            self.varletters[letter].add(var)
            return var

    def NOTYETreinitvars(self):
        self.varletters = {} # variable: {concepts}
        self.vars = {} # var: concept
        self.oldvars = set()
        oldnew = {} # oldvar: newvar

        for s, p, o in self.triples:
            # get all instances to sse al variables
            if p == ":instance":
                self.oldvars.add(s)
                newletter = o[0]
                if newletter == "i":
                    # avoir an instance "i" (can be confused with concept "I")
                    newletter = "ii"

                if newletter not in self.varletters:
                    # first variable starting with this letter
                    self.varletters[newletter] = set([newletter])
                    self.vars[newletter] = o
                    oldnew[s] = newletter
                else:
                    # we have seen this letter
                    newvar = newletter + str(len(self.varletters[newletter]) + 1)
                    self.varletters[newletter].add(newvar)
                    oldnew[s] = newvar
                    self.vars[newvar] = o

        # update variables in triples
        newtriples = []
        for s, p, o in self.triples:
            #if s in self.oldvars:
            #    s = oldnew.get(s)
            #if o in self.oldvars:
            #    o = oldnew.get(o)
            s = oldnew.get(s, s)
            o = oldnew.get(o, o)
            newtriples.append((s, p, o))
        self.triples = newtriples

    def getvars(self, concept):
        # find all instances of a given concept
        insts = []
        for k, v in self.vars.items():
            if concept == v:
                insts.append(k)
        return insts

    def dot(self, highlightinstances=None, highlightrelations=None, highlightconcepts=None, format="svg", inverse_of=False):
        # highlight instances and relations NOT in highlightinstances and highlightrelations
        #global orangecolors
        if highlightconcepts:
            #orangecolors = {highlightconcepts: "#ff7900"}
            localorangecolors = {}
            for ix, c in enumerate(highlightconcepts):
                localorangecolors[c] = colorlist[ix % len(colorlist)]
        else:
            localorangecolors = orangecolors

        graph_attr = {#'rankdir':'LR'
        }
        kwargsinit = {
            "fontname": "Lato",
            "style": "filled",
            "fillcolor": "white"
            }

        graph = Digraph('amr_graph', format=format, graph_attr=graph_attr)
        firstseen = False
        ct_literal = 0
        for s, p, o in self.triples:
            if inverse_of and p.endswith("-of") and not p.startswith(":consist"):
                tmp = o
                o = s
                s = tmp
                p = p[:-3]
            kwargs = kwargsinit.copy()

            if p == ":instance":
                ibg = "white"
                if highlightinstances and s not in highlightinstances:
                    kwargs = {"fontname": "Lato",  #"Lato Black",
                              "style": "filled",
                              "fillcolor": "#ff7900"} #localorangecolors.get(":snt1")}
                elif highlightconcepts and o in highlightconcepts:
                    kwargs = {"fontname": "Lato",  #"Lato Black",
                              "style": "filled",
                              "fillcolor": localorangecolors.get(o, "white")}
                if not firstseen:
                    # mark the topnode
                    kwargs["fontname"] = "Lato Black"
                    firstseen = True

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
                           id="node#%s#%s" % (s, o),
                           #URL=branch[0],
                           #fillcolor=ibg,
                           #style="filled",
                           **kwargs
                           )
            else:
                onodeid = o
                pp = p
                kwargs["fontcolor"] = localorangecolors.get(p.replace("-of", ""), "black")
                if highlightrelations and (s, p, o) not in highlightrelations:
                    kwargs["fontname"] = "Lato" # "Lato Black" }
                    kwargs["fontcolor"] = "black"
                    pp = '< <table border="0"> <tr><td bgcolor="%s">%s</td></tr></table> >' % ("#ff7900",
                                                                                               p)

                if o not in self.vars:
                    oo = o.replace('"', 'DQUOTE').replace(':', 'COLON').replace('\\', 'BSLASH')
                    onodeid = "%s_%s_%s" % (s, ct_literal, oo)
                    ct_literal += 1
                    kwargs["fillcolor"] = localorangecolors.get("EN", "#dddddd")
                    kwargs["style"] = "filled"

                    graph.node(onodeid, label="%s" % (o),
                               id="literal#%s#%s#%s" % (s, p, o),
                               #style="filled",
                               color=localorangecolors.get("EN", "#dddddd"),
                               #fillcolor=orangecolors.get("EN"),
                               #URL=branch[0],
                               **kwargs)
                #print("ZZZZ", s,p,o)

                # color of arrow head
                kwargs["fillcolor"] = localorangecolors.get(p.replace("-of", ""), "black")

                col = localorangecolors.get(p.replace("-of", ""), "black")
                graph.edge(s, onodeid, label=pp,
                           id="edge#%s#%s#%s" % (s, o, p),
                           color=col,
                           # fontcolor=orangecolors.get(p.replace("-of", ""), "black"),
                           **kwargs)
        # print("DOT source", graph)
        return graph.pipe()

    def show(self, highlightinstances=None, highlightrelations=None, highlightconcepts=None, format="svg"):
        if self.inserver:
            if not self.valid:
                return self.lastpm, None, None

            try:
                pm = penman.encode(penman.Graph(self.triples, top=self.top))
                self.lastpm = pm
                #a = amr2dot.AMR2DOT(format="svg", font="Lato", instances=False, lr=False, bw=False)
                #a.build(pm)
                #self.lastsvg = a.graph.pipe()
                self.readpenman(pm)
                self.lastsvg = self.dot(highlightinstances, highlightrelations, highlightconcepts=highlightconcepts, format=format)
                self.lastsvg_canonised = self.dot(highlightinstances, highlightrelations, highlightconcepts=highlightconcepts, format=format, inverse_of=True)
                self.isDisconnected = False
            except penman.exceptions.LayoutError:
                #a = amr2dot.AMR2DOT(format="svg", font="Lato", instances=False, lr=False, bw=False)
                #a.buildtriples(self.triples)
                #self.lastsvg = a.graph.pipe()
                self.lastsvg = self.dot(format=format)
                self.lastsvg_canonised = self.dot(format=format, inverse_of=True)
                noninst = []
                for tr in self.triples:
                    noninst.append(tr)
                sgs = graph.findsubgraphs(noninst)

                pms = []
                for sg in sgs:
                    triples = []

                    for tr in self.triples:
                        if tr[0] in sg or (tr[2] in sg and tr[1] != ":instance"):
                            triples.append(tr)
                    pm = penman.encode(penman.Graph(triples))
                    pms.append(pm)
                    # print("DISCONNECTED", pm)

                self.lastpm = "\n\n".join(pms)
                if len(sgs) > 1:
                    self.isDisconnected = True
                else:
                    self.isDisconnected = False

            return "%s" % self.lastpm, self.lastsvg, self.lastsvg_canonised
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
            if o in self.vars:
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
            npm, msgs = reificator.dereify(self.lastpm, only=dereify)
            if not msgs:
                self.readpenman(npm)

        return msgs

    def renamevar(self, oldname, newname):
        if newname in self.vars:
            return ["variable '%s' already used in graph" % newname]
        if ord(newname[0]) < 97 or ord(newname[0]) > 122:
            return ["new variable '%s' must start with a...z" % newname]
        mo = self.isValidVar.match(newname)
        if not mo:
            return ["new variable '%s' invalid. Must match '%s'" % (newname, self.isValidVar.pattern)]
        if oldname not in self.vars:
            return ["variable '%s' notin graph" % oldname]

        newvars = {}
        for k, v in self.vars.items():
            if k == oldname:
                k = newname
            newvars[k] = v
        self.vars = newvars

        newtriples = []
        for s, p, o in self.triples:
            if s == oldname:
                s = newname
            if p != ":instance":
                if o == oldname:
                    o = newname
            newtriples.append((s, p, o))
        self.triples = newtriples

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
        # change label of edge
        for tr in self.triples:
            #print("MOD-EDGE", tr, modedge_start, modedge_end, newedge)
            if tr[0] == modedge_start and tr[2] == modedge_end:
                pos = self.triples.index(tr)
                self.triples.remove(tr)
                self.triples.insert(pos, (tr[0], newedge, tr[2]))
                break
            elif tr[2] == modedge_start and tr[0] == modedge_end:
                pos = self.triples.index(tr)
                self.triples.remove(tr)
                self.triples.insert(pos, (tr[2], newedge, tr[0]))
                break

    def moveedge(self, modedge_start, modedge_end, newedge, newstart):
        # change start point of edge
        if newstart not in self.vars:
            return "new source instance « %s » does not exist" % newstart

        for tr in self.triples:
            #print("MOVE-EDGE", tr, modedge_start, modedge_end, newedge, newstart)
            if tr[0] == modedge_start and tr[2] == modedge_end:
                pos = self.triples.index(tr)
                self.triples.remove(tr)
                self.triples.insert(pos, (newstart, newedge, tr[2]))
                break
            if tr[2] == modedge_start and tr[0] == modedge_end:
                # can create confusion.
                #if tr[1].endswith("-of"):
                #    return 'deactivate  « reverse "-of" » to modify the head this relation'
                pos = self.triples.index(tr)
                self.triples.remove(tr)
                self.triples.insert(pos, (newstart, tr[1], tr[0]))
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
    aa.readpenman("(c / cat)")
    aa.show()

    line = input(">> ")
    while line:
        aa.process(line)
        aa.show()
        line = input(">> ")

    aa = AMRProcessor(inserver=False)
    aa.readpenman("(c / contrast-01   :ARG1 (p / possible-01      :polarity -   :ARG1 (t / think-01  :ARG0 (i / i))))")
    aa.show()
