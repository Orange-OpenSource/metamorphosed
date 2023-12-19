#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2022-2023,  Orange
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
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke
# SPDX-FileCopyrightText: Copyright (c) 2022-2023 Orange
# SPDX-License-Identifier: Mozilla Public License 2.0
# SPDX-License-Identifier: BSD-3-Clause

import collections
import colorsys
import logging
import random
import re

import graphviz
import penman

# import readline
# import sys

logger = logging.getLogger("amrcoref-editor")

orangecolors = {
    ":ARG0": "#ff7900",
    ":ARG1": "#9164cd",
    ":ARG3": "#ffb4e6",
    ":ARG4": "#50be87",
    ":ARG2": "#4bb4e6",
    ":ARG5": "#ffdc00",
    ":beneficiary": "#d9c2f0",
    ":snt1": "#b8ebd6",
    ":snt2": "#b8ebd6",
    ":snt3": "#b8ebd6",
    ":snt4": "#b8ebd6",
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


orangedark = collections.OrderedDict({
    "charteYellowDark": "#ffb400",
    "charteBlueDark": "#085ebd",
    "chartePinkDark": "#ff8ad4",
    "charteOrange": "#ff7900",
    "charteVioletDark": "#492191",
    "charteGreenDark": "#0a6e31",
    #"charteGrayDark": "#595959",
})
orangedarkkeys = list(orangedark.keys())

orangecols = collections.OrderedDict({
    "charteYellow": "#ffdc00",
    "charteBlue": "#4bb4e6",
    "chartePink": "#ffb4e6",
    #"charteOrange": "#ff7900",
    "charteViolet": "#9164cd",
    "charteGreen": "#50be87",
    #"charteGray": "#8f8f8f",
})
orangecolskeys = list(orangecols.keys())

orangebright = collections.OrderedDict({
    "charteYellowBright": "#fff6b6",
    "charteBlueBright": "#b5e8f7",
    "chartePinkBright": "#ffe8f7",
    "charteOrangeBright": "#ffeccc",
    "charteVioletBright": "#d9c2f0",
    "charteGreenBright": "#b8ebd6",
    #"charteGrayBright": "#d6d6d6",
})

# we need many colours since long texts have many coref chains
random.seed(2023) # we use random shuffle to put the colour in a random order, but the same random order every time ...
manyothercols = {}

#for a in [20,60,100,140]:
#    for b in [75, 115, 155, 195]:
#        for c in [130,170,210,250]:
#            z = [a,b,c]
#            random.shuffle(z)
#            col = "#%02x%02x%02x" % tuple(z)
#
#            #print(col, "black" if sum(z)/3 > 128 else "white")
#            manyothercols[col] = col

# maybe awkward, but the objective is to create many differnet colours which the human eye can distinguish well
for h in [0, 0.1666, 0.333, 0.666, 0.8333, 1]:
    for lum in [0.333, 0.666, 0.9]:
        for s in [0.333, 0.666, 0.9]:
            r, g, b = colorsys.hls_to_rgb(h, lum, s)
            col = "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

            #print(col, "black" if sum(z)/3 > 128 else "white")
            manyothercols[col] = col


orangebright.update(orangedark)
orangebright.update(orangecols)
orangebright.update(manyothercols)

orangebrightkeys = list(orangebright.keys())
#for i,c in enumerate(orangebrightkeys):
#    print(i, c, orangebright[c])

SVGDIMS = re.compile('(width|height)="(\\d+)')


class AMRs2dot:
    def __init__(self, amrs, corefs, implicitroles, scaling=1):
        self.scaling = 0.65 * scaling
        self.corefchains = corefs

        self.coreferenced = {} # sid: {var: corefchainid}
        for crid, cchain in enumerate(self.corefchains):
            for sid, var in cchain:
                if sid not in self.coreferenced:
                    self.coreferenced[sid] = {}
                self.coreferenced[sid][var] = crid

        self.implicitroles = implicitroles # sentpos: [chainid, parentvar, ARG]
        logger.debug(self.coreferenced)
        self.pgraphs = []
        for amr in amrs:
            pg = penman.decode(amr)
            #print(pg.metadata)
            self.pgraphs.append(pg)

        #self.dot(format)
        #ofp = open("g.pdf", "w")
        #print(self.dot(), file=ofp)
        #ofp.close()

    def chainid2col(self, cid):
        fillcol = orangebright.get(orangebrightkeys[cid % len(orangebrightkeys)])
        r = int(fillcol[1:3], 16)
        g = int(fillcol[3:5], 16)
        b = int(fillcol[5:], 16)
        hue, luminosity, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

        # print("BRIGTHNESS", s, o, fillcol,  "R", r,  "G",g, "B",b, ", H", hue,  "S", sat, "LUM", luminosity)
        fontcol = "black"
        if luminosity < 0.5:
            fontcol = "white"
        # print(  "FONTCOL", luminosity, fontcol)
        return fillcol, fontcol

    def multidot(self, svgs, showfrom=None, shownumber=None):
        # put each AMR graphs into a SVG graph and return a list of SVG
        graph_attr = {# 'rankdir':'LR',
            "bgcolor": "transparent"
            }
        font = "Lato"
        kwargs = {
            "fontname": font
            }

        svglist = collections.OrderedDict() # sentid: SVG
        # needed to scale the generated SVG (easier here than in the HTML/CSS/JS hell)

        def scale(x):
            return '%s="%s' % (x.group(1), int(x.group(2)) * self.scaling)

        #print("window", showfrom, shownumber)
        for ig, pg in enumerate(self.pgraphs):
            #print("ig", ig)
            if showfrom and ig + 1 < showfrom:
                #print("skip", ig)
                continue
            if shownumber and ig + 1 >= showfrom + shownumber:
                #print("break", ig)
                break
            title = "%s" % ig
            text = ""
            if pg.metadata:
                if "id" in pg.metadata:
                    title = "%s" % (pg.metadata["id"])
                    #sgraph.attr(label="%d: %s" % (ig, pg.metadata["id"]))
                if "snt" in pg.metadata:
                    text = pg.metadata["snt"]

            if ig in svgs:
                # only redo svgs if absent or modified (in this case they are absent)
                svglist[title] = {"svg": svgs[ig],
                                  "text": text}
                #print("SVG  OK", ig, title)
                continue

            #print("REDO SVG", ig, title)
            graph = graphviz.Digraph('amr_graph', format="svg", graph_attr=graph_attr)
            varset = set(pg.variables())
            varsetnew = set(["G_%d_%s" % (ig, x) for x in varset])

            # firstok = False

            sgraph = graph

            for s, p, o in pg.triples:
                #oorig = o
                sorig = s
                if s in varset:
                    s = "G_%d_%s" % (ig, s)
                if p != ":instance" and o in varset:
                    o = "G_%d_%s" % (ig, o)
                if p == ":instance":
                    kwargs2 = {"fontname": font,
                               "style": "filled",
                               "fillcolor": "white"
                               }
                    chainnum = "chain_none"
                    relid = ""
                    if ig in self.coreferenced and sorig in self.coreferenced[ig]:
                        chainid = self.coreferenced[ig][sorig]
                        chainnum = "chain_%s" % chainid
                        relid = "\nrel-%s" % chainid

                        fillcol, fontcol = self.chainid2col(chainid)
                        kwargs2 = {"style": "filled",
                                   "fontname": font,
                                   "fontcolor": fontcol,
                                   "fillcolor": fillcol}
                    sgraph.node("%s" % s, label="%s/%s%s" % (sorig, o, relid), shape="box",
                                id="node %s %s %s" % (s, o, chainnum),
                                #URL=branch[0],
                                **kwargs2)

                else:
                    onodeid = o
                    if o not in varsetnew:
                        oo = o.replace('"', 'DQUOTE').replace(':', 'COLON').replace('\\', 'BSLASH')
                        onodeid = "%s_%s" % (s, oo)
                        sgraph.node(onodeid, label="%s" % (o),
                                    id="literal %s %s %s" % (s, p, o),
                                    style="filled",
                                    #color=orangecolors.get("EN"),
                                    fillcolor="#e2e2e2", #orangecolors.get("EN"),
                                    #URL=branch[0],
                                    **kwargs)

                    sgraph.edge(s, onodeid, label=p,
                                id="edge#%s#%s#%s" % (s, o, p),
                                #color=orangecolors.get(p.replace("-of", ""), "black"),
                                #fontcolor=orangecolors.get(p.replace("-of", ""), "black"),
                                **kwargs)

            # self.implicitroles # sentpos: [chainid, parentvar, ARG]
            if ig in self.implicitroles:
                for cid, pv, arg in self.implicitroles[ig]:
                    ss = "G_%d_%s" % (ig, pv)
                    oo = "I_%d_%s_%d" % (ig, pv, cid)
                    fillcol, fontcol = self.chainid2col(cid)
                    kwargs2 = {"style": "rounded,filled",
                               "color": "gray",
                               "fontname": font,
                               "fontcolor": fontcol,
                               "fillcolor": fillcol}
                    sgraph.node(oo, #label="i%s/implicit\nrel-%d" % (pv, cid),
                                label="i%s rel-%d" % (pv, cid),
                                shape="diamond",
                                #id="node %s %s %s" % (s,o,chainnum),
                                **kwargs2
                                )
                    sgraph.edge(ss, oo, label=arg,
                                color="gray",
                                fontcolor="gray",
                                **kwargs)
                    #print("IIII", ss, oo, arg)

            #print("GV", graph, sep="\n", file=sys.stderr) # dot sources
            svgraw = graph.pipe().decode("utf8")
            svgraw = SVGDIMS.sub(scale, svgraw)
            svgs[ig] = svgraw
            svglist[title] = {"svg": svgraw, #graph.pipe().decode("utf8"),
                              "text": text}
        return svglist


if __name__ == "__main__":
    a0 = '''(b / bear-02
            :ARG1 (p / person
                     :name (n / name
                              :op1 "Naomie"
                              :op2 "Harris")
                     :wiki "Q156586")
            :location (c / city
                         :name (n2 / name
                                   :op1 "London")
                         :wiki "Q84"))'''
    a1 = '''(b / live-01
            :ARG0 (s / she)
            :location (c / city)
            :mod (s1 / still))
            '''
    a2 = '''(b / star-01
            :ARG0 (s / she)
            :location (f / film))
            '''
    a3 = '''(b / live-01
            :ARG0 (m / mother
               :poss ( h /her))
            :location  (c / city
                         :name (n2 / name
                                   :op1 "London")
                         :wiki "Q84"))'''
    a4 = '''(h / hails-01
               :ARG0 (s / she)
               :ARG1 ( c /country :name (n2 / name :op1 "Jamaica")))'''

    ad = AMRs2dot([a0, a1, a2, a3, a4],
                  [[(0, "p"), (1, "s"), (2, "s"), (3, "h")],  # coreference chain: (sentence, variable)
                   [(0, "c"), (1, "c"), (3, "c")],
                   [(3, "m"), (4, "s")]
                   ])
    # ad.dot(format="pdf")
