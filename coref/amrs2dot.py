#!/usr/bin/env python3

# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke
# SPDX-FileCopyrightText: Copyright (c) 2022-2023 Orange
# SPDX-License-Identifier: Mozilla Public License 2.0
#
# This software is distributed under the MPL-2.0 license.
# the text of which is available at https://www.mozilla.org/en-US/MPL/2.0/
# or see the "LICENSE" file for more details.

import collections
import colorsys
import graphviz
import logging
import penman
import random
import re
import readline
import sys

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
manyothercols = {}
#for a in [20,35,50,67]:
#    for b in [100,125,150,180]:
#        for c in [200,220,240,255]:
for a in [20,60,100,140]:
    for b in [75, 115, 155, 195]:
        for c in [130,170,210,250]:

            z = [a,b,c]
            random.shuffle(z)
            col = "#%02x%02x%02x" % tuple(z)
            
            #print(col, "black" if sum(z)/3 > 128 else "white")
            manyothercols[col] = col

orangebright.update(orangedark)
orangebright.update(orangecols)
orangebright.update(manyothercols)

orangebrightkeys = list(orangebright.keys())
#for i,c in enumerate(orangebrightkeys):
#    print(i, c, orangebright[c])

SVGDIMS = re.compile('(width|height)="(\d+)')

class AMRs2dot:
    def __init__(self, amrs, corefs, implicitroles, scaling=1):
        self.scaling = 0.65*scaling
        self.corefchains = corefs

        self.coreferenced = {} # sid: {var: corefchainid}
        for crid,cchain in enumerate(self.corefchains):
            for sid,var in cchain:
                if not sid in self.coreferenced:
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
    

    def dot(self, format="svg"):
        # put all AMR graphs into a single SVG graph
        graph_attr={#'rankdir':'LR'
            }
        font = "Lato"
        kwargs = {
            "fontname": font
            }
        graph = graphviz.Digraph('amr_graph', format=format, graph_attr=graph_attr)
        firstnodes = [] # first note of each AMR graph (needed to keep clusters in correct order
        for ig,pg in enumerate(self.pgraphs):
            # for all penman graphs
            varset = set(pg.variables())
            varsetnew = set(["G_%d_%s" % (ig,x) for x in varset])

            #print(varset)
            #sgraph = graph.subgraph(name="cluster_%d" % ig)

            firstok = False
            with graph.subgraph(name="cluster_%d" % ig) as sgraph:
                if pg.metadata and "id" in pg.metadata:
                    sgraph.attr(label="%d: %s" % (ig, pg.metadata["id"]))
                else:
                    sgraph.attr(label="%s" % ig)
                sgraph.attr(fontname=font)
                for s,p,o in pg.triples:
                    oorig = o
                    sorig = s
                    if s in varset:
                        s = "G_%d_%s" % (ig, s)
                    if p != ":instance" and o in varset:
                        o = "G_%d_%s" % (ig, o)
                    if p == ":instance":
                        if not firstok:
                            firstnodes.append(s)
                            firstok = True
                        kwargs2 = {"fontname": font}
                        if ig in self.coreferenced and sorig in self.coreferenced[ig]:
                            col = self.coreferenced[ig][sorig]
                            fillcol = orangebright.get(orangebrightkeys[col % len(orangebrightkeys)])
                            r = int(fillcol[1:3], 16)
                            g = int(fillcol[3:5], 16)
                            b = int(fillcol[5:], 16)
                            brightness = (r+g+b)/3
                            #print("BRIGTHNESS", fillcol, r,g,b, brightness)
                            fontcol = "black"
                            if brightness < 100:
                                fontcol = "white"
                                #print(fillcol, brightness, fontcol)
                            kwargs2 = {"style": "filled",
                                       "fontname": font,
                                       "fontcolor": fontcol,
                                       "fillcolor": fillcol} #orangebright.get(orangebrightkeys[col % len(orangebrightkeys)])}
                        sgraph.node("%s" % s, label="%s/%s" % (sorig,o), shape="box",
                                    id="node %s %s" % (s,o),
                                    #URL=branch[0],
                                    **kwargs2)

                    else:
                        onodeid = o
                        if o not in varsetnew:
                            oo = o.replace('"', 'DQUOTE').replace(':', 'COLON').replace('\\', 'BSLASH')
                            onodeid = "%s_%s" % (s,oo)
                            sgraph.node(onodeid, label="%s" % (o),
                                       id="literal %s %s %s" % (s,p,o),
                                       style="filled",
                                       #color=orangecolors.get("EN"),
                                       fillcolor="#e2e2e2", #orangecolors.get("EN"),
                                       #URL=branch[0],
                                       **kwargs)

                        sgraph.edge(s, onodeid, label=p,
                                   id="edge#%s#%s#%s" % (s,o,p),
                                   #color=orangecolors.get(p.replace("-of", ""), "black"),
                                   #fontcolor=orangecolors.get(p.replace("-of", ""), "black"),
                                   **kwargs)
        #for ix in range(1, len(firstnodes)):
        #    # should keep the order of clusters, but does not
        #    graph.edge(firstnodes[ix-1],
        #               firstnodes[ix],
        #               constraint="false")

        
        for crid, corefchain in enumerate(self.corefchains):
            # does influence the order of clusters
            # so we quit here und rely on colours only !!!
            break
            logger.debug("Coref chain %s" % corefchain)
            for pos in range(1, len(corefchain)):
                graph.edge("G_%d_%s" % (corefchain[pos-1][0], corefchain[pos-1][1]),
                           "G_%d_%s" % (corefchain[pos][0], corefchain[pos][1]),
                           #label="coref",
                           color=orangedark.get(orangedarkkeys[crid % len(orangedarkkeys)]),
                           penwidth="3",
                           dir="none",
                           constraint="false"
                           )
        #print("GV", graph, sep="\n", file=sys.stderr) # dot sources
        if format == "pdf":
            graph.render(outfile="g.pdf")
        elif format == "svg":
            return graph.pipe()

    def chainid2col(self, cid):
        fillcol = orangebright.get(orangebrightkeys[cid % len(orangebrightkeys)])
        r = int(fillcol[1:3], 16)
        g = int(fillcol[3:5], 16)
        b = int(fillcol[5:], 16)
        hue,luminosity,sat = colorsys.rgb_to_hls(r/255, g/255, g/255)

        # print("BRIGTHNESS", s, o, fillcol,  "R", r,  "G",g, "B",b, ", H", hue,  "S", sat, "LUM", luminosity)
        fontcol = "black"
        if luminosity < 0.5:
            fontcol = "white"
        # print(  "FONTCOL", luminosity, fontcol)
        return fillcol, fontcol

    
    def multidot(self, svgs, showfrom=None, shownumber=None):
        # put each AMR graphs into a SVG graph and return a list of SVG
        graph_attr={# 'rankdir':'LR',
            "bgcolor": "transparent"
            }
        font = "Lato"
        kwargs = {
            "fontname": font
            }

        svglist = collections.OrderedDict() # sentid: SVG
        # needed to scale the generated SVG (easier here than in the HTML/CSS/JS hell)
        def scale(x):
            return '%s="%s' % (x.group(1), int(x.group(2))*self.scaling)


        #print("window", showfrom, shownumber)
        for ig,pg in enumerate(self.pgraphs):
            #print("ig", ig)
            if showfrom and ig+1 < showfrom:
                #print("skip", ig)
                continue
            if shownumber and ig+1 >= showfrom+shownumber:
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
                svglist[title] = { "svg": svgs[ig],
                                   "text": text }
                #print("SVG  OK", ig, title)
                continue

            #print("REDO SVG", ig, title)
            graph = graphviz.Digraph('amr_graph', format="svg", graph_attr=graph_attr)
            varset = set(pg.variables())
            varsetnew = set(["G_%d_%s" % (ig,x) for x in varset])

            firstok = False

            sgraph = graph

            for s,p,o in pg.triples:
                oorig = o
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
                        
                        fillcol,fontcol = self.chainid2col(chainid)
                        kwargs2 = {"style": "filled",
                                   "fontname": font,
                                   "fontcolor": fontcol,
                                   "fillcolor": fillcol} #orangebright.get(orangebrightkeys[col % len(orangebrightkeys)])}
                    sgraph.node("%s" % s, label="%s/%s%s" % (sorig,o,relid), shape="box",
                                id="node %s %s %s" % (s,o,chainnum),
                                #URL=branch[0],
                                **kwargs2)

                else:
                    onodeid = o
                    if o not in varsetnew:
                        oo = o.replace('"', 'DQUOTE').replace(':', 'COLON').replace('\\', 'BSLASH')
                        onodeid = "%s_%s" % (s,oo)
                        sgraph.node(onodeid, label="%s" % (o),
                                   id="literal %s %s %s" % (s,p,o),
                                   style="filled",
                                   #color=orangecolors.get("EN"),
                                   fillcolor="#e2e2e2", #orangecolors.get("EN"),
                                   #URL=branch[0],
                                   **kwargs)

                    sgraph.edge(s, onodeid, label=p,
                               id="edge#%s#%s#%s" % (s,o,p),
                               #color=orangecolors.get(p.replace("-of", ""), "black"),
                               #fontcolor=orangecolors.get(p.replace("-of", ""), "black"),
                               **kwargs)


            # self.implicitroles # sentpos: [chainid, parentvar, ARG]
            if ig in self.implicitroles:
                for cid,pv,arg in self.implicitroles[ig]:
                    ss = "G_%d_%s" % (ig, pv)
                    oo = "I_%d_%s_%d" % (ig, pv, cid)
                    fillcol,fontcol = self.chainid2col(cid)
                    kwargs2 = {"style": "rounded,filled",
                               "color": "gray",
                               "fontname": font,
                               "fontcolor": fontcol,
                               "fillcolor": fillcol}
                    sgraph.node(oo, label="i%s/implicit\nrel-%d" % (pv, cid), shape="diamond",
            #                    #id="node %s %s %s" % (s,o,chainnum),
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
            svglist[title] = { "svg": svgraw, #graph.pipe().decode("utf8"),
                              "text": text }
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
                     

    ad = AMRs2dot([a0,a1,a2,a3,a4],
                  [[(0, "p"), (1, "s"), (2, "s"), (3, "h")], # coreference chain: (sentence, variable)
                   [(0, "c"), (1, "c"), (3, "c")],
                   [(3, "m"),(4, "s")]
                   ])
    ad.dot(format="pdf")
