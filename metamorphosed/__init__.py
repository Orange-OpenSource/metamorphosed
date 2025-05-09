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


import collections
import importlib
import io
import json
import os
import re
import socket
import sys
import time
import zipfile

from flask import Flask, Response, jsonify, render_template, request
import yaml

import metamorphosed.AMR_relations as AMR_relations
import metamorphosed.amrdoc as amrdoc
import metamorphosed.amreditor as amreditor
import metamorphosed.gitinterface as gitinterface
import metamorphosed.propbank_frames as propbank_frames
import metamorphosed.reification as reification
import metamorphosed.relations_constraints as relations_constraints
import metamorphosed.amr_comparison as amr_comparison
from metamorphosed.relations_doc import RelDoc
from metamorphosed.edge_predictor import Basic_EdgePredictor as EdgePredictor
from metamorphosed.exception import ServerException
from metamorphosed.findsubgraph import SubGraphRDF
import metamorphosed.joingraphs as joingraphs
from metamorphosed.preferred_graph import PreferredGraphs

import metamorphosed.installJQ as iJQ

# TODO
# detect errors
#  * a1 :rel a1
# undo/redo unstable if sentence is changed and a redo is possible

# find an example in AMR data
# call an AMRserver for an (empty) sentence ? rather not

APIVERSION = "1.9.0"


class AMR_Edit_Server:
    def __init__(self, port, filename, pbframes, rels, concepts, constraints,
                 readonly, author=None, reifications=None, relationsdoc=None,
                 predictor=None,
                 do_git=True, compare=None, smatchpp=False,
                 preferred=None, # filename where to read/write the preferred graph in comparison mode
                 ):
        self.port = port
        self.filename = filename
        self.amrdoc = amrdoc.AMRdoc(filename)
        self.aps = {} # parsed and possibly modified PENMAN AMRs
        self.author = author
        self.reificator = None
        self.do_git = do_git
        self.smatchpp = smatchpp
        self.preferred = None

        self.readonly = readonly
        self.otheramrdocs = [] # (doc,aps)

        if compare is not None:
            self.readonly = True
            self.do_git = False

            filedict = collections.OrderedDict({filename: self.amrdoc})
            # inter-annotator mode
            for fn in compare:
                doc = amrdoc.AMRdoc(fn)
                filedict[fn] = doc # filename: amrdoc object
                aps = {}
                for sentnum, cursentence in enumerate(doc.sentences, start=1):
                    if sentnum % 10 == 0:
                        print("%d initialized" % sentnum, end="\r")
                        ap = amreditor.AMRProcessor()
                        aps[sentnum] = ap
                        ap.lastpm = cursentence.amr
                        ap.comments = cursentence.comments
                self.otheramrdocs.append((doc, aps))
            print("all compare sentences initialized")

            if preferred is not None:
                self.preferred = PreferredGraphs(filedict, preferred)

        else:
            if reifications:
                self.reificator = reification.getInstance(reifications)

        self.fileversion = "2"
        if not self.readonly and not gitinterface.is_git_controlled(filename):
            bak_filename = filename + "." + self.fileversion
            if os.path.exists(bak_filename):
                raise Exception("Edited file <%s> not under git version control. Backup file <%s> exists already.\nPlease rename Backup file first" % (filename, bak_filename))

        self.relationsdoc = None
        if relationsdoc:
            self.relationsdoc = RelDoc(relationsdoc)

        # initial version of Penman graph
        self.initstates = []
        print("initializing...")
        for sentnum, cursentence in enumerate(self.amrdoc.sentences, start=1):
            if sentnum % 10 == 0:
                print("%d initialized" % sentnum, end="\r")
            ap = amreditor.AMRProcessor()
            self.aps[sentnum] = ap
            ap.lastpm = cursentence.amr
            ap.comments = cursentence.comments
            self.initstates.append(ap.lastpm)

        print("all sentences initialized")

        # stack of last actions, used by undo/redo
        # save current ap **after** modifiying it
        # it is initalialized with a copy of all sentences
        self.undos = [] # (self.apps:sentnum, [lastpm])
        self.redos = []

        mydir = os.path.abspath(os.path.dirname(__file__))

        installOK = iJQ.checkLibraries()
        if not installOK:
            print("*** Javascript libraries missing. Run %s/installJQ.py or install manually as described in README.ld" % mydir, file=sys.stderr)
            sys.exit(1)

        self.isInt = re.compile(r"^\d+$")
        self.isFloat = re.compile(r"^\d*\.?\d+$")

        # objects to validate an AMR graph
        # these classes must implement a validate(triples) method which return a list of error messages
        self.amr_rels = AMR_relations.Relations(rels)
        self.amr_concepts = AMR_relations.Relations(concepts, isconceptlist=True)
        self.pbframes = propbank_frames.PropBankFrames(pbframes)
        amreditor.AMRProcessor.pbframes = self.pbframes # to add some documentation from propbank to SVG
        self.constraints = relations_constraints.Constraints(constraints)

        self.edge_predictor = None
        if predictor:
            self.create_edge_predictor(yamlfile=predictor)

        if not self.edge_predictor:
            self.edge_predictor = EdgePredictor()

        app = Flask(__name__,
                    static_url_path='',
                    static_folder="%s/gui" % mydir,
                    template_folder="%s/gui" % mydir)
        app.config['TEMPLATES_AUTO_RELOAD'] = True # needed to reload index.html
        self.app = app

        @app.route('/', methods=["GET"])
        def index():
            # Displays the index page accessible at '/'
            if self.otheramrdocs:
                return render_template('compare.html', toolname="AMR File Comparison")
            else:
                return render_template('index.html', toolname="AMR Editor")

        @app.route('/version', methods=["GET"])
        def version():
            dico = {"name": "AMR Editor",
                    "version": amreditor.VERSION,
                    "apiversion": APIVERSION}
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        @app.route('/info', methods=["GET"])
        def info():
            withdata = self.checkParameter(request, 'withdata', 'boolean', isOptional=True, defaultValue=False)
            self.validParameters(request, ["withdata"])

            dico = {"cmdline": " ".join(sys.argv),
                    "pwd": os.getcwd(),
                    "hostname": socket.gethostname(),
                    "filename": filename, "numsent": len(self.amrdoc.sentences),
                    "propbank_frames": pbframes,
                    "readonly": self.readonly,
                    "version": amreditor.VERSION,
                    "apiversion": APIVERSION
                    }

            if self.otheramrdocs:
                dico["otherfilenames"] = [doc.fn for doc, aps in self.otheramrdocs]
                possible_comparisons = []
                for a in range(len(self.otheramrdocs) + 1):
                    for b in range(a + 1, len(self.otheramrdocs) + 1):
                        possible_comparisons.append([a + 1, b + 1])
                dico["comparisons"] = possible_comparisons
                if self.preferred:
                    dico["preferred_file"] = self.preferred.preferredfile

            if withdata:
                dico["relations"] = sorted(self.amr_rels.relations)
                dico["concepts"] = sorted(self.amr_concepts.relations)
                dico["sentences"] = self.amrdoc.getsentencelist()

            if self.reificator:
                reifs = self.reificator.getquivalences()
                dico["reifications"] = reifs
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        @app.route('/edit', methods=["GET", "POST"])
        def modify():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False)
            prevmod = self.checkParameter(request, 'prevmod', 'integer', isOptional=True, defaultValue=0)
            cmd = self.checkParameter(request, 'cmd', 'string', isOptional=True, defaultValue=None)
            addconcept = self.checkParameter(request, 'addconcept', 'string', isOptional=True, defaultValue=None)
            addname = self.checkParameter(request, 'addname', 'string', isOptional=True, defaultValue=None)
            nameof = self.checkParameter(request, 'nameof', 'string', isOptional=True, defaultValue=None)

            start = self.checkParameter(request, 'start', 'string', isOptional=True, defaultValue=None)
            end = self.checkParameter(request, 'end', 'string', isOptional=True, defaultValue=None)
            label = self.checkParameter(request, 'label', 'string', isOptional=True, defaultValue=None)

            modconcept = self.checkParameter(request, 'modconcept', 'string', isOptional=True, defaultValue=None)
            newconcept = self.checkParameter(request, 'newconcept', 'string', isOptional=True, defaultValue=None)

            newtop = self.checkParameter(request, 'newtop', 'string', isOptional=True, defaultValue=None)

            delinstance = self.checkParameter(request, 'delinstance', 'string', isOptional=True, defaultValue=None)

            modedge_start = self.checkParameter(request, 'modedge_start', 'string', isOptional=True, defaultValue=None)
            modedge_end = self.checkParameter(request, 'modedge_end', 'string', isOptional=True, defaultValue=None)
            newedge = self.checkParameter(request, 'newedge', 'string', isOptional=True, defaultValue=None)
            modedge_newstart = self.checkParameter(request, 'modedge_newstart', 'string', isOptional=True, defaultValue=None)

            deledge_start = self.checkParameter(request, 'deledge_start', 'string', isOptional=True, defaultValue=None)
            deledge_end = self.checkParameter(request, 'deledge_end', 'string', isOptional=True, defaultValue=None)
            deledge = self.checkParameter(request, 'deledge', 'string', isOptional=True, defaultValue=None)

            literalid = self.checkParameter(request, 'literalid', 'string', isOptional=True, defaultValue=None)
            literaledge = self.checkParameter(request, 'literaledge', 'string', isOptional=True, defaultValue=None)
            newliteral = self.checkParameter(request, 'newliteral', 'string', isOptional=True, defaultValue=None)
            delliteral = self.checkParameter(request, 'delliteral', 'string', isOptional=True, defaultValue=None)

            literalof = self.checkParameter(request, 'literalof', 'string', isOptional=True, defaultValue=None)
            relationforliteral = self.checkParameter(request, 'relationforliteral', 'string', isOptional=True, defaultValue=None)
            newliteral = self.checkParameter(request, 'newliteral', 'string', isOptional=True, defaultValue=None)

            modpenman = self.checkParameter(request, 'modpenman', 'string', isOptional=True, defaultValue=None)
            modcomment = self.checkParameter(request, 'modcomment', 'string', isOptional=True, defaultValue=None)
            reify = self.checkParameter(request, 'reify', 'string', isOptional=True, defaultValue=None)
            dereify = self.checkParameter(request, 'dereify', 'string', isOptional=True, defaultValue=None)
            addgraph = self.checkParameter(request, 'addgraph', 'string', isOptional=True, defaultValue=None)
            mappings = self.checkParameter(request, 'mappings', 'string', isOptional=True, defaultValue=None)

            oldvarname = self.checkParameter(request, 'oldvarname', 'string', isOptional=True, defaultValue=None)
            newvarname = self.checkParameter(request, 'newvarname', 'string', isOptional=True, defaultValue=None)

            if sentnum < 1 or sentnum > len(self.amrdoc.sentences):
                # creates an http status code 400
                raise ServerException("invalid sentence number: must be between 1 and %d" % len(self.amrdoc.sentences))
                #dico = {"error": "invalid sentence number: must be between 1 and %d\n" % len(self.amrdoc.sentences)}
                #return Response("%s\n" % json.dumps(dico),
                #                400, mimetype="application/json")

            validparams = ["num", "cmd",
                           "addconcept",
                           "addname", "nameof",
                           "start", "label", "end",
                           "modconcept", "newconcept",
                           "modedge_start", "modedge_end", "newedge", "modedge_newstart",
                           "delinstance",
                           "deledge_start", "deledge_end", "deledge",
                           "literalid", "literaledge", "newliteral", "delliteral",
                           "literalof", "relationforliteral", "newliteral",
                           "modpenman",
                           "modcomment",
                           "reify", "dereify",
                           "newtop",
                           "prevmod",
                           "addgraph", "mappings",
                           "newvarname", "oldvarname"]

            #self.findinvalidparameters(request, validparams)
            self.validParameters(request, set(validparams))
            print("COMMAND:", end=" ")
            for v in validparams:
                if v != "num" and eval(v) is not None:
                    print('%s: "%s"' % (v, eval(v)), end=" ")
            print()
            ap = self.aps.get(int(sentnum))

            if not ap.isparsed:
                ap.readpenman(ap.lastpm)
                ap.show()

            cursentence = self.amrdoc.sentences[sentnum - 1]
            if not ap.valid and modpenman is None:
                # an invalid PENMAN can only be corrected using modpenman
                return invalidamr(ap, ap.lastpm, cursentence, sentnum)

            #print("ZZZZ", self.aps, ap, sentnum)
            rtc = None
            print("AP PREVMOD:", ap.previous_modification, "CLIENT:", prevmod, "TOO LATE", ap.previous_modification > prevmod)
            if ap.previous_modification > prevmod:
                raise ServerException("The sentence has been edit by another user. Please reload sentence")

            self.undos.append((sentnum, ap.lastpm))
            #print("AP: %s" % ap.lastpm)
            #print("UNDOS: %d" % (len(self.undos)))
            self.redos = []
            #print("REDOS: %d" % (len(self.redos)))
            #for n,pm in self.states:
            #    print("hhh   %s %s" % (n, " ## ".join(pm).replace("\n", "")))
            #    #print("hhh   %s %s" % (n, pm))

            ap.modified = True # TODO: set rather by ap.-functions ??
            cursentence.date = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))

            if cmd:
                ap.process(cmd)
            elif addconcept:
                ap.process(addconcept)
            elif addname and nameof:
                var = ap.addconcept("name")
                words = addname.split()
                for i, w in enumerate(words):
                    ap.addedge(var, '"%s"' % w, ":op%d" % (i + 1))
                ap.addedge(nameof, var, "name")
            elif start and end and label:
                # add new edge between to nodes
                if label == "todo":
                    # print("label", label, end=" ")

                    label = self.edge_predictor.predict(ap.vars.get(start), ap.vars.get(end))
                    # print("->", label)
                rtc = ap.addedge(start, end, label)
            elif modconcept and newconcept:
                ap.modconcept(modconcept, newconcept)
            elif modedge_start and modedge_end and newedge:
                if modedge_newstart:
                    rtc = ap.moveedge(modedge_start, modedge_end, newedge, modedge_newstart)
                else:
                    ap.modedge(modedge_start, modedge_end, newedge)
            elif delinstance:
                ap.delinstance(delinstance)
            elif deledge_start and deledge_end and deledge:
                ap.deledge(deledge_start, deledge_end, deledge)
            elif literalid and literaledge and newliteral:
                ap.modliteral(literalid, literaledge, newliteral)
            elif literalid and literaledge and delliteral:
                rtc = ap.delliteral(literalid, literaledge, delliteral)
            elif literalof and relationforliteral and newliteral:
                rtc = ap.addliteral(literalof, relationforliteral, newliteral)
            elif modpenman:
                newap = amreditor.AMRProcessor()
                newap.readpenman(modpenman)
                newap.previous_modification = ap.previous_modification
                if not newap.valid:
                    return invalidamr(newap,
                                      modpenman,
                                      self.amrdoc.sentences[sentnum - 1],
                                      sentnum)
                else:
                    newap.show() # to create penman
                    self.aps[sentnum] = newap
                    ap = newap
                    ap.modified = True # set rather by ap.-functions ??
            elif modcomment is not None:
                # comments are not processed in AMRProcessor
                cursentence.modcomment(modcomment)
            elif newtop:
                rtc = ap.settop(newtop)
            elif reify:
                #print(ap.lastpm)
                ap.reify(reify)
            elif dereify:
                rtc = ap.dereify(dereify)
            elif oldvarname and newvarname:
                rtc = ap.renamevar(oldvarname, newvarname)
            elif addgraph:
                if not mappings or not mappings.strip():
                    raise ServerException("Missing variable mappings. use 'v1/v2 ...'")
                corefs = []
                if mappings:
                    for elems in mappings.split():
                        mapping = elems.split("/")
                        if len(mapping) != 2:
                            raise ServerException("Bad format for mappings. use 'a/b ...': %s" % elems)
                        corefs.append((mapping[0], mapping[1]))

                newap = amreditor.AMRProcessor()
                try:
                    pm = joingraphs.joingraphs(ap.lastpm, addgraph, corefs, top=None)
                    newap.readpenman(pm)
                    newap.previous_modification = ap.previous_modification
                except Exception as e:
                    raise ServerException("Cannot join graphs: %s" % e)
                if not newap.valid:
                    return invalidamr(newap,
                                      modpenman,
                                      self.amrdoc.sentences[sentnum - 1],
                                      sentnum)
                else:
                    newap.show() # to create penman
                    self.aps[sentnum] = newap
                    ap = newap
                    ap.modified = True # set rather by ap.-functions ??

            else:
                # creates an http status code 400
                raise ServerException("No edit valid operation given")

            pm, svg, svg_canon = ap.show()

            framedoc = None
            framedocs = self.pbframes.getdoc(ap.triples)
            if len(framedocs):
                framedoc = "\n".join(framedocs)

            reldoc = None
            if self.relationsdoc:
                docs = self.relationsdoc.getdoc(ap.triples)
                if len(docs):
                    reldoc = docs

            warnings = []
            if isinstance(rtc, list):
                warnings.extend(rtc)
            elif isinstance(rtc, str):
                warnings.append(rtc)
            warnings += ap.validate(valfuncs=[self.amr_rels.validate, self.amr_concepts.validate, self.pbframes.validate, self.constraints.validate])
            if len(warnings) < 1:
                warnings = None
            cursentence = self.amrdoc.sentences[sentnum - 1]
            lastchanged = cursentence.date
            if not lastchanged:
                lastchanged = cursentence.savedateorig
            ap.previous_modification += 1
            print("AUGMENT", cursentence.id, ap.previous_modification)
            dico = {"warning": warnings,
                    "framedoc": framedoc,
                    "reldoc": reldoc,
                    "readonly": self.readonly,
                    "penman": pm,
                    "svg": svg.decode("utf8") if svg else "",
                    "svg_canon": svg_canon.decode("utf8") if svg_canon else "",
                    "filename": filename, "numsent": len(self.amrdoc.sentences),
                    "num": sentnum,
                    "text": cursentence.text,
                    "comments": "\n".join(cursentence.comments),
                    "sentid": cursentence.id,
                    "lastchanged": lastchanged,
                    "variables": sorted(list(set(ap.vars.keys()))),
                    "undos": len(self.undos),
                    "redos": len(self.redos),
                    "prevmod": ap.previous_modification}
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        @app.route('/search', methods=["GET"])
        def search():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            what = self.checkParameter(request, 'what', 'string', isOptional=False, defaultValue=None)
            regex = self.checkParameter(request, 'regex', 'string', isOptional=False, defaultValue=None)
            compare = self.checkParameter(request, 'compare', 'string', isOptional=True, defaultValue=None)

            validparams = ["num", "what", "regex", "compare"]
            self.validParameters(request, set(validparams))

            okt = None
            oka = None

            if what == "findtextnext":
                for x in range(sentnum, len(self.amrdoc.sentences)):
                    okt = list(self.amrdoc.sentences[x].findtext(regex))
                    if okt:
                        sentnum = x + 1
                        break
            elif what == "findidnext":
                for x in range(sentnum, len(self.amrdoc.sentences)):
                    ok = self.amrdoc.sentences[x].findid(regex)
                    if ok:
                        sentnum = x + 1
                        break
            elif what == "findcommentnext":
                for x in range(sentnum + 1, len(self.amrdoc.sentences)):
                    okc = self.amrdoc.sentences[x].findcomment(regex)
                    if okc:
                        sentnum = x + 1
                        break
            elif what == "findamrnext":
                try:
                    sg_rdf = SubGraphRDF(regex)
                except Exception as e:
                    # no valid PENMAN, take subgraph as a regex...
                    # print("AMR Search error: %s" % e, file=sys.stderr)
                    sg_rdf = None

                for x in range(sentnum + 1, len(self.amrdoc.sentences) + 1):
                    if sg_rdf:
                        # oka = list(self.aps[x].findamr(regex))
                        # oka = list(self.aps[x].findsubgraph(regex, smatchpp=self.smatchpp))
                        oka = list(self.aps[x].findsubgraph(sg_rdf))
                        # print("OKA", oka)
                    else:
                        oka = list(self.aps[x].findamr(regex))
                    if oka:
                        sentnum = x
                        break
            elif what == "findtextprec":
                for x in range(sentnum - 2, -1, -1):
                    okt = list(self.amrdoc.sentences[x].findtext(regex))
                    if okt:
                        sentnum = x + 1
                        break
            elif what == "findidprec":
                for x in range(sentnum - 2, -1, -1):
                    ok = self.amrdoc.sentences[x].findid(regex)
                    if ok:
                        sentnum = x + 1
                        break
            elif what == "findcommentprec":
                for x in range(sentnum - 2, -1, -1):
                    ok = self.amrdoc.sentences[x].findcomment(regex)
                    if ok:
                        sentnum = x + 1
                        break

            elif what == "findamrprec":
                try:
                    sg_rdf = SubGraphRDF(regex)
                except Exception as e:
                    # no valid PENMAN, take subgraph as a regex...
                    # print("AMR Search error: %s" % e, file=sys.stderr)
                    sg_rdf = None

                for x in range(sentnum - 1, 0, -1):
                    if sg_rdf:
                        oka = list(self.aps[x].findsubgraph(sg_rdf))
                        # print("OKA", oka)
                    else:
                        oka = list(self.aps[x].findamr(regex))
                    if oka:
                        sentnum = x
                        break
            else:
                raise ServerException("invalid search parameter '%s'" % what)
            #print("OKA",oka)
            #print("OKT",okt)
            #print("Sentnum", sentnum)
            return prepare_newpage(sentnum, okt, oka, compare=compare) #, iscompare=iscompare)

        @app.route('/history', methods=["GET"])
        def history():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            history = self.checkParameter(request, 'history', 'string', isOptional=False, defaultValue=None)
            prevmod = self.checkParameter(request, 'prevmod', 'integer', isOptional=True, defaultValue=0)

            validparams = ["num", "history", "prevmod"]
            self.validParameters(request, set(validparams))

            #print("hUNDOS: %d" % (len(self.undos)))
            #print("hREDOS: %d" % (len(self.redos)))

            #for n,pm in self.states:
            #    print("HHH   sentnum:%s pm:%s" % (n, " ## ".join(pm).replace("\n", "")))

            # TODO
            apcurrent = self.aps[sentnum]
            print("AP PREVMOD:", apcurrent.previous_modification, "CLIENT:", prevmod, "TOO LATE", apcurrent.previous_modification > prevmod)
            if apcurrent.previous_modification > prevmod:
                raise ServerException("The sentence has been edit by another user. Please reload sentence")

            if history == "undo":
                if len(self.undos) > 0:
                    # put current on redo
                    ap = self.aps[sentnum]
                    ap.show()
                    #print("FOR REDO", sentnum, ap.lastpm)
                    self.redos.append((sentnum, ap.lastpm))

                    # get latest undo
                    (sentnum, pm) = self.undos.pop()
                    #print("UNDO", sentnum, pm)
                    ap = amreditor.AMRProcessor()
                    self.aps[sentnum] = ap
                    ap.readpenman(pm)
                    ap.previous_modification = apcurrent.previous_modification
                    ap.show()
                    print("AP", ap)

            elif history == "redo":
                if len(self.redos) > 0:
                    # put current on undo
                    ap = self.aps[sentnum]
                    ap.show()
                    print("FOR UNDO", sentnum, ap.lastpm)
                    self.undos.append((sentnum, ap.lastpm))

                    # get latest undo
                    (sentnum, pm) = self.redos.pop()
                    print("REDO", sentnum, type(pm), pm)
                    ap = amreditor.AMRProcessor()
                    self.aps[sentnum] = ap
                    ap.readpenman(pm)
                    ap.previous_modification = apcurrent.previous_modification
                    ap.show()
                    print("AP", ap)

            #print("QQQ", sentnum, history)
            return prepare_newpage(sentnum)

        @app.route('/next', methods=["GET"])
        def next():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            direction = self.checkParameter(request, 'direction', 'string', isOptional=False, defaultValue=None)
            compare = self.checkParameter(request, 'compare', 'string', isOptional=True, defaultValue=None)

            validparams = ["num", "direction", "compare"]
            self.validParameters(request, set(validparams))

            if direction == "preceding":
                if sentnum > 1:
                    sentnum -= 1
            elif direction == "next":
                if sentnum < len(self.amrdoc.sentences):
                    sentnum += 1
            elif direction == "first":
                sentnum = 1
            elif direction == "last":
                sentnum = len(self.amrdoc.sentences)

            return prepare_newpage(sentnum, compare=compare)

        @app.route('/read', methods=["GET"])
        def read():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            compare = self.checkParameter(request, 'compare', 'string', isOptional=True, defaultValue=None)

            validparams = ["num", "compare"]
            self.validParameters(request, set(validparams))

            if sentnum < 1 or sentnum > len(self.amrdoc.sentences):
                dico = {"error": "invalid sentence number: must be between 1 and %d" % len(self.amrdoc.sentences)}
                return Response("%s\n" % json.dumps(dico),
                                400, mimetype="application/json")

            return prepare_newpage(sentnum, compare=compare)

        @app.route('/graphs/<filename>', methods=["GET"])
        def downloadgraphs(filename: str):
            # filename necessary in GUI, but we always use the same. Check whether it does not contain strange stuff
            dataformat = self.checkParameter(request, 'format', 'string', isOptional=True, defaultValue="svg")
            highlight_concepts = self.checkParameter(request, 'concepts', 'string', isOptional=True, defaultValue=None)
            pages = self.checkParameter(request, 'sentences', 'string', isOptional=True, defaultValue=None)

            if not re.match(r"^[A-Za-z0-9_]+\.zip$", filename):
                dico = {"error": "invalid export filename. Must end in .zip: <%s>" % filename}
                return Response("%s\n" % json.dumps(dico),
                                400, mimetype="application/json")

            validargs = set(["format", "sentences", "concepts"])
            self.validParameters(request, validargs)

            if highlight_concepts:
                highlight_concepts = [x.strip() for x in highlight_concepts.split(",")]

            #if validargs != validargs.union(request.values.keys()):
            #    dico = {"error": "invalid parameters: <%s>" % request.values.keys()}
            #    return Response("%s\n" % json.dumps(dico),
            #                    400, mimetype="application/json")

            def parse_pages(page_string):
                page_string2 = re.sub("[^0-9, -]", "", page_string)
                pages = []
                ranges = page_string2.split(',')
                for r in ranges:
                    r = r.strip()
                    if not r:
                        # empty string between two commas
                        continue
                    if r.count("-") > 1:
                        # too many hyphens
                        continue
                    if '-' in r:
                        if r[-1] == "-":
                            # no number *after* the hyphen given
                            r += "0"
                        start, end = map(int, r.split('-'))
                        pages.extend(range(start, end + 1))
                    else:
                        pages.append(int(r))
                return pages

            if pages:
                pages = parse_pages(pages)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED, False) as zip_file:
                metadata = []
                for ix, x in enumerate(self.aps, 1):
                    if pages and ix not in pages:
                        continue
                    ap = self.aps[x]
                    if not ap.isparsed:
                        ap.readpenman(ap.lastpm)
                    pm, svg, svg_canon = ap.show(format=dataformat, highlightconcepts=highlight_concepts)
                    if svg:
                        zip_file.writestr("%d.%s" % (ix, dataformat), svg)
                    sent = self.amrdoc.sentences[ix - 1]
                    metadata.append({"sentence": sent.text, "id": sent.id, "filename": "%d.%s" % (ix, dataformat), "sourcefilename": self.amrdoc.fn})
                    #print("FILE", ix, svg[:100] if svg else svg)
                zip_file.writestr("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))

            return Response(zip_buffer.getvalue(), 200, mimetype="application/zip")

        @app.route('/setpreferred', methods=["GET"])
        def setpreferred():
            # only used with --compare and --preferred
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=True, defaultValue=1)
            preferred = self.checkParameter(request, 'preferred', 'string', isOptional=True, defaultValue=-1)
            compare = self.checkParameter(request, 'compare', 'string', isOptional=True, defaultValue=None)

            if self.preferred is not None:
                sent = self.amrdoc.sentences[sentnum - 1]
                #self.preferred[str(sentnum)] = {"sid": sent.id, "source": preferred}
                self.preferred.set(sentnum, sent, preferred)

            return prepare_newpage(sentnum, compare=compare)

        @app.route('/save', methods=["GET"])
        def save():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=True, defaultValue=1)

            validargs = set(["num"])
            self.validParameters(request, validargs)

            self.save()

            if sentnum < 1 or sentnum > len(self.amrdoc.sentences):
                dico = {"error": "invalid sentence number: must be between 1 and %d\n" % len(self.amrdoc.sentences)}
                return Response("%s\n" % json.dumps(dico),
                                400, mimetype="application/json")

            return prepare_newpage(sentnum)

        @app.errorhandler(ServerException)
        def handle_invalid_usage(error):
            response = jsonify({"error": error.value}) #jsonify(error.to_dict())
            response.status_code = 400 #error.status_code
            return response

        #@app.errorhandler(Exception)
        #def handle_other_error(error):
        #    response = jsonify({"error": str(error)})
        #    response.status_code = 404
        #    return response

        def invalidamr(ap, pm, cursentence, sentnum):
            # format error in file
            text = ap.parsererror["text"]
            if ap.parsererror["lineno"] == 1:
                pos = ap.parsererror["offset"]
                endpos = text.find(" ", pos)
                if endpos != -1:
                    endpos = endpos - pos
                else:
                    endpos = 1
                text = '%s<span class="syntaxerror">%s</span>%s' % (text[:pos],
                                                                    text[pos:pos + endpos],
                                                                    text[pos + endpos:]
                                                                    )
            warnings = ["format error: %s in line %s:%s « %s », please correct file in a text editor first" %
                        (ap.parsererror["message"],
                         ap.parsererror["lineno"],
                         ap.parsererror["offset"],
                         text)
                        ]
            dico = {"penman": pm,
                    "svg": "",
                    "svg_canon": "",
                    "warning": warnings,
                    "framedoc": "",
                    "readonly": self.readonly,
                    "filename": filename,
                    "numsent": len(self.amrdoc.sentences),
                    "num": sentnum,
                    "text": cursentence.text,
                    "comments": "\n".join(cursentence.comments),
                    "sentid": cursentence.id,
                    "undos": len(self.undos),
                    "redos": len(self.redos)
                    }
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        def prepare_newpage(sentnum, oktext=None, okamr=None, compare=None):
            # sentnum uses 1 ... length
            # self.amrdoc.sentences is a list: 0 length-1
            cursentence = self.amrdoc.sentences[sentnum - 1]
            if sentnum not in self.aps:
                ap = amreditor.AMRProcessor()
                self.aps[sentnum] = ap
                ap.readpenman(cursentence.amr)
            else:
                ap = self.aps[sentnum]
                if not ap.isparsed:
                    ap.readpenman(cursentence.amr)

            pm, svg, svg_canon = ap.show()
            if not ap.valid:
                return invalidamr(ap, pm, cursentence, sentnum)

            iscompare = compare is not None
            if okamr and not iscompare:
                # rerun search, because ap has reformated the original penman (possibly different indentation)
                # so to highlight the search result correctly we apply the search in the (now reformatted) penman
                # do not higlight in penman when iscompare is truen since the penaman becomes unparsable
                okamr = list(ap.findamr(okamr[0].re.pattern))
                for mo in reversed(list(okamr)):
                    pm = pm[:mo.start()] + '<span class="highlight">%s</span>' % pm[mo.start():mo.end()] + pm[mo.end():]

            sentencetext = cursentence.text
            if sentencetext:
                sentencetext = sentencetext.replace("<", "&lt;").replace(">", "&gt;")

            if oktext:
                for mo in reversed(list(oktext)):
                    sentencetext = sentencetext[:mo.start()] + '<span class="highlight">%s</span>' % sentencetext[mo.start():mo.end()] + sentencetext[mo.end():]

            warnings = ap.validate(valfuncs=[self.amr_rels.validate, self.pbframes.validate, self.constraints.validate])
            if len(warnings) < 1:
                warnings = None

            framedoc = None
            framedocs = self.pbframes.getdoc(ap.triples)
            if len(framedocs):
                framedoc = "\n".join(framedocs)

            reldoc = None
            if self.relationsdoc:
                docs = self.relationsdoc.getdoc(ap.triples)
                if len(docs):
                    reldoc = docs

            lastchanged = cursentence.date
            if not lastchanged:
                lastchanged = cursentence.savedateorig

            dico = {"penman": pm,
                    "svg": svg.decode("utf8"),
                    "svg_canon": svg_canon.decode("utf8"),
                    "warning": warnings,
                    "framedoc": framedoc,
                    "reldoc": reldoc,
                    "readonly": self.readonly,
                    "filename": filename,
                    "numsent": len(self.amrdoc.sentences),
                    "num": sentnum,
                    "text": sentencetext, #cursentence.text,
                    "comments": "\n".join(cursentence.comments),
                    "sentid": cursentence.id,
                    "lastchanged": lastchanged,
                    "variables": sorted(list(set(ap.vars.keys()))),
                    "undos": len(self.undos),
                    "redos": len(self.redos),
                    "prevmod": ap.previous_modification}

            if self.otheramrdocs:
                others = []
                first_to_compare, second_to_compare = compare.split(",")
                first_to_compare = int(first_to_compare) - 2
                second_to_compare = int(second_to_compare) - 2

                # get graphs from dos to compare
                if first_to_compare == -1:
                    firstsent = cursentence
                else:
                    firstdoc, firstaps = self.otheramrdocs[first_to_compare]
                    firstsent = firstdoc.sentences[sentnum - 1]
                seconddoc, secondaps = self.otheramrdocs[second_to_compare]
                secondsent = seconddoc.sentences[sentnum - 1]

                compres = amr_comparison.compare(firstsent.amr, secondsent.amr, use_smatchpp=self.smatchpp, align=True)

                # compare all with all
                variations = [cursentence]
                filenames = [filename]
                for doc, _ in self.otheramrdocs:
                    variations.append(doc.sentences[sentnum - 1])
                    filenames.append(doc.fn)

                comparisons = []
                for first in range(len(variations) - 1):
                    for second in range(first + 1, len(variations)):
                        compres2 = amr_comparison.compare(variations[first].amr, variations[second].amr, use_smatchpp=self.smatchpp, align=True)
                        #comparisons.append(("%s_%s" % (first + 1, second + 1), filenames[first], filenames[second], "%.2f" % (compres2.f1 * 100), compres2.gold_triple_num, compres2.test_triple_num, compres2.best_match_num))
                        comparisons.append({"index": "%s_%s" % (first + 1, second + 1), # needed to highlight the correct line in comparison results
                                            "fn1": filenames[first],
                                            "fn2": filenames[second],
                                            "F1": "%.2f" % (compres2.f1 * 100),
                                            "gold_triples": compres2.gold_triple_num,
                                            "sys_triples": compres2.test_triple_num,
                                            "best_match_triples": compres2.best_match_num})

                if first_to_compare == -1:
                    # update display of first document
                    # highlight instances and relations NOT in highlightinstances and highlightrelations
                    cpm, csvg, csvg_canon = ap.show(highlightinstances=compres.instances1OK, highlightrelations=compres.rel1OK)
                    dico["svg"] = csvg.decode("utf8")

                for ix, (doc, aps) in enumerate(self.otheramrdocs):
                    ccursentence = doc.sentences[sentnum - 1]
                    if sentnum not in aps:
                        cap = amreditor.AMRProcessor()
                        aps[sentnum] = cap
                        cap.readpenman(ccursentence.amr)
                    else:
                        cap = aps[sentnum]
                        if not cap.isparsed:
                            cap.readpenman(ccursentence.amr)

                    # show differences of chosen pair
                    if ix == first_to_compare:
                        cpm, csvg, csvg_canon = cap.show(highlightinstances=compres.instances1OK, highlightrelations=compres.rel1OK)
                    elif ix == second_to_compare:
                        cpm, csvg, csvg_canon = cap.show(highlightinstances=compres.instances2OK, highlightrelations=compres.rel2OK)
                    else:
                        cpm, csvg, csvg_canon = cap.show()

                    dico2 = {}
                    dico2["filename"] = doc.fn
                    dico2["svg"] = csvg.decode("utf8")
                    dico2["penman"] = cpm
                    dico2["comments"] = "\n".join(ccursentence.comments),
                    others.append(dico2)
                dico["others"] = others
                dico["smatch"] = "%.2f" % (compres.f1 * 100)
                dico["bestmatch"] = compres.best_match_num
                dico["left_triplenum"] = compres.test_triple_num
                dico["right_triplenum"] = compres.gold_triple_num
                dico["comp_results"] = comparisons

                if self.preferred:
                    dico["preferred"] = self.preferred.get(sentnum)
                else:
                    dico["preferred"] = None

            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

    def start(self):
        self.app.run(host="0.0.0.0", port=self.port) #, threaded=False, processes=4)
        self.save()

    def save(self):
        if not self.readonly:
            print("saving", self.filename)
            self.savefile(self.filename, self.fileversion)

        if self.preferred is not None:
            self.preferred.save()

#    def findinvalidparameters(self, request, validlist):
#        for k, v in request.values.items():
#            #print("kkk", k,v)
#            if k not in validlist:
#                raise ServerException("invalid parameter '%s'" % k)

    def validParameters(self, request, validparams):
        for paramName in request.files:
            if paramName not in validparams:
                raise ServerException("invalid file parameter '%s'" % paramName)
        for paramName in request.values:
            if paramName not in validparams:
                raise ServerException("invalid parameter '%s'" % paramName)

    def checkParameter(self, request, paramName, paramType, isOptional=False, defaultValue=None):
        # needed for curl -F txt=@file.txt
        if paramName in request.files:
            bstr = request.files[paramName].read()
            return bstr.decode("UTF-8")

        #for k,v in request.values.items():
        #    print("kkk", k,v)
        if paramName not in request.values:
            if not isOptional:
                #raise apifactory_errors.Error(27)
                raise ServerException("missing mandatory parameter '%s'" % paramName)

            else:
                return defaultValue

        value = request.values[paramName].strip()
        #print("nnnn", paramType, value)
        if paramType == "string":
            if len(value) == 0 and not isOptional:
                raise ServerException("Parameter '%s' must not be empty." % paramName)
            else:
                return str(value)
        if paramType == "boolean":
            if not (str(value).lower() in ("true", "1", "false", "0")):
                raise ServerException("Parameter '%s' should be a boolean (i.e. one of 'true', 'false', '0', '1')." % paramName)
            else:
                return (value.lower() in ("true", "1"))
        if paramType == "integer":
            if not self.isInt.match(value):
                raise ServerException("Parameter '%s' must be an integer." % paramName)
            else:
                return int(value)
        if paramType == "float":
            if not self.isFloat.match(value):
                raise ServerException("Parameter '%s' must be a float." % paramName)
            else:
                return float(value)

        raise ServerException("Another stupid error occurred. Invalid paramtype? %s %s" % (paramName, paramType))

    def savefile(self, fn, version="2"):
        messages = []
        warnings = []
        self.modified = []
        repo, saveok, gitok = gitinterface.save(fn, version,
                                                self.writedoc,
                                                #sg.xml(),
                                                warnings, messages, do_add=self.do_git)

        if gitok and self.do_git:
            try:
                rtc = repo.git.commit("-m", "metamorphosed AMR editor: %s of '%s' saved" % (", ".join(self.modified), fn), author=self.author)
                print("commited %s" % (fn), rtc)
            except Exception as e:
                print("COMMIT Error <%s> <%s> <%s>" % (e, fn, rtc))
                pass

    def writedoc(self, ofp):
        for i, sent in enumerate(self.amrdoc.sentences):
            if i + 1 in self.aps:
                if self.aps[i + 1].modified:
                    self.modified.append(str(i + 1))
                    sent.date = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
                sent.write(ofp, onlyheader=True)
                #print("SENT", i+1, self.aps[i+1].modified, sent.id, sent.text, self.aps[i+1].triples)
                self.aps[i + 1].write(ofp)
            else:
                sent.write(ofp)

    def create_edge_predictor(self, yamlfile):
        self.edge_predictor = None
        with open(yamlfile) as ifp:
            yamldir = os.path.dirname(yamlfile)
            conf = yaml.safe_load(ifp)
            print(conf)
            if "filename" not in conf:
                print("Missing filename in %s" % yamlfile, file=sys.stderr)
                return None
            if "classname" not in conf:
                print("Missing classname in %s" % yamlfile, file=sys.stderr)
                return None

            # cutting final .py
            filename = conf["filename"][:-3].replace("__localpath__", yamldir)
            # get dirname
            dirname = os.path.dirname(filename)
            modname = os.path.basename(filename)

            print("dir", dirname)
            print("mod", modname)
            args = None
            if "args" in conf:
                args = [x.replace("__localpath__", yamldir) for x in conf["args"]]
            print("args", args)
            # append PYTHONPATH
            sys.path.append(dirname)

            # load module
            mymodule = importlib.import_module(modname)

            EdgePredictor = getattr(mymodule, conf["classname"])
            self.edge_predictor = EdgePredictor(args)
