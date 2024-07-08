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


import io
import json
import os
import re
import socket
import sys
import time
import zipfile

from flask import Flask, Response, jsonify, render_template, request

import AMR_relations
import amrdoc
import amreditor
import gitinterface
import propbank_frames
import reification
import relations_constraints
from smatch_pm import Smatch

# TODO
# detect errors
#  * a1 :rel a1
# undo/redo unstable if sentence is changed and a redo is possible

# find an example in AMR data
# call an AMRserver for an (empty) sentence ? rather not

APIVERSION = "1.5.0"


class AMR_Edit_Server:
    def __init__(self, port, filename, pbframes, rels, concepts, constraints,
                 readonly, author=None, reifications=None,
                 do_git=True, compare=None):
        self.port = port
        self.filename = filename
        self.amrdoc = amrdoc.AMRdoc(filename)
        self.aps = {} # parsed and possibly modified PENMAN AMRs
        self.author = author
        self.reificator = None
        self.do_git = do_git

        #self.comparedoc = None
        #self.comparefilename = None
        #if compare is not None:
        #    self.comparefilename = compare
        #    readonly = True
        #    self.do_git = False
        self.readonly = readonly
        if compare is not None:
            self.readonly = True
            self.do_git = False
        else:
            if reifications:
                self.reificator = reification.getInstance(reifications)

        self.fileversion = "2"
        if not self.readonly and not gitinterface.is_git_controlled(filename):
            bak_filename = filename + "." + self.fileversion
            if os.path.exists(bak_filename):
                raise Exception("Edited file <%s> not under git version control. Backup file <%s> exists already.\nPlease rename Backup file first" % (filename, bak_filename))

        # initial version of PM
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

        self.otheramrdocs = [] # (doc,aps)
        if compare is not None:
            # interannotator mode
            for fn in compare:
                doc = amrdoc.AMRdoc(fn)
                aps = {}
                for sentnum, cursentence in enumerate(doc.sentences, start=1):
                    if sentnum % 10 == 0:
                        print("%d initialized" % sentnum, end="\r")
                        ap = amreditor.AMRProcessor()
                        aps[sentnum] = ap
                        ap.lastpm = cursentence.amr
                        ap.comments = cursentence.comments
                self.otheramrdocs.append((doc, aps))

        #elif compare is not None:
        #    self.comparedoc = amrdoc.AMRdoc(compare)
        #    self.compare_aps = {}
        #    for sentnum, cursentence in enumerate(self.comparedoc.sentences, start=1):
        #        if sentnum % 10 == 0:
        #            print("%d initialized" % sentnum, end="\r")
        #            ap = amreditor.AMRProcessor()
        #            self.compare_aps[sentnum] = ap
        #            ap.lastpm = cursentence.amr
        #            ap.comments = cursentence.comments

            print("all compare sentences initialized")

        # stack of last actions, used by undo/redo
        # save current ap **after** modifiying it
        # it is initalialized with a copy of all sentences
        self.undos = [] # (self.apps:sentnum, [lastpm])
        self.redos = []

        mydir = os.path.abspath(os.path.dirname(__file__))

        self.isInt = re.compile(r"^\d+$")
        self.isFloat = re.compile(r"^\d*\.?\d+$")

        # objects to validate an AMR graph
        # these classes must implement a validate(triples) method which return a list of error messages
        self.amr_rels = AMR_relations.Relations(rels)
        self.amr_concepts = AMR_relations.Relations(concepts, isconceptlist=True)
        self.pbframes = propbank_frames.PropBankFrames(pbframes)
        amreditor.AMRProcessor.pbframes = self.pbframes # to add some documentation from propbank to SVG
        self.constraints = relations_constraints.Constraints(constraints)

        app = Flask(__name__,
                    static_url_path='',
                    static_folder="%s/gui" % mydir,
                    template_folder="%s/gui" % mydir)
        app.config['TEMPLATES_AUTO_RELOAD'] = True # needed to reload index.html
        self.app = app

        @app.route('/', methods=["GET"])
        def index():
            # Displays the index page accessible at '/'
            #if self.comparedoc:
            #    return render_template('compare.html', toolname="AMR File Comparison")
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
            dico = {"cmdline": " ".join(sys.argv),
                    "pwd": os.getcwd(),
                    "hostname": socket.gethostname(),
                    "filename": filename, "numsent": len(self.amrdoc.sentences),
                    "propbank_frames": pbframes,
                    #"relations": sorted(self.amr_rels.relations),
                    #"concepts": sorted(self.amr_concepts.relations),
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
            #elif self.comparefilename:
            #    dico["filename2"] = self.comparefilename
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
                           "newtop"]
            self.findinvalidparameters(request, validparams)

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

            self.undos.append((sentnum, ap.lastpm))
            #print("AP: %s" % ap.lastpm)
            #print("UNDOS: %d" % (len(self.undos)))
            self.redos = []
            #print("REDOS: %d" % (len(self.redos)))
            #for n,pm in self.states:
            #    print("hhh   %s %s" % (n, " ## ".join(pm).replace("\n", "")))
            #    #print("hhh   %s %s" % (n, pm))

            ap.modified = True # set rather by ap.-functions ??
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
                #if rtc:
                #    rtc = " ".join(rtc)
                #else:
                #    rtc = None
            elif reify:
                #print(ap.lastpm)
                ap.reify(reify)
            elif dereify:
                rtc = ap.dereify(dereify)
            else:
                # creates an http status code 400
                raise ServerException("No edit valid operation given")

            pm, svg = ap.show()

            framedoc = None
            framedocs = self.pbframes.getdoc(ap.triples)
            if len(framedocs):
                framedoc = "\n".join(framedocs)

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
            dico = {"warning": warnings, "framedoc": framedoc, "readonly": self.readonly,
                    "penman": pm, "svg": svg.decode("utf8") if svg else "",
                    "filename": filename, "numsent": len(self.amrdoc.sentences),
                    "num": sentnum,
                    "text": cursentence.text,
                    "comments": "\n".join(cursentence.comments),
                    "sentid": cursentence.id,
                    "lastchanged": lastchanged,
                    "variables": sorted(list(set(ap.vars.keys()))),
                    "undos": len(self.undos),
                    "redos": len(self.redos)}
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        @app.route('/search', methods=["GET"])
        def search():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            what = self.checkParameter(request, 'what', 'string', isOptional=False, defaultValue=None)
            regex = self.checkParameter(request, 'regex', 'string', isOptional=False, defaultValue=None)
            #iscompare = self.checkParameter(request, 'compare', 'boolean', isOptional=True, defaultValue=False)
            compare = self.checkParameter(request, 'compare', 'string', isOptional=True, defaultValue=None)

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
                    okc = list(self.amrdoc.sentences[x].findcomment(regex))
                    if okc:
                        sentnum = x + 1
                        break
            elif what == "findamrnext":
                for x in range(sentnum + 1, len(self.amrdoc.sentences) + 1):
                    #oka = list(self.amrdoc.sentences[x].findamr(regex))
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
                for x in range(sentnum - 1, 0, -1):
                    oka = list(self.aps[x].findamr(regex))
                    #oka = list(self.amrdoc.sentences[x].findamr(regex))
                    if oka:
                        sentnum = x
                        break
            else:
                raise ServerException("invalid search parameter '%s'" % what)
            #print("OKA",oka)
            #print("OKT",okt)
            return prepare_newpage(sentnum, okt, oka, compare=compare) #, iscompare=iscompare)

        @app.route('/history', methods=["GET"])
        def history():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            history = self.checkParameter(request, 'history', 'string', isOptional=False, defaultValue=None)

            #print("hUNDOS: %d" % (len(self.undos)))
            #print("hREDOS: %d" % (len(self.redos)))

            #for n,pm in self.states:
            #    print("HHH   sentnum:%s pm:%s" % (n, " ## ".join(pm).replace("\n", "")))

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
                    ap.show()
                    print("AP", ap)

            #print("QQQ", sentnum, history)
            return prepare_newpage(sentnum)

        @app.route('/next', methods=["GET"])
        def next():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            direction = self.checkParameter(request, 'direction', 'string', isOptional=False, defaultValue=None)
            #iscompare = self.checkParameter(request, 'compare', 'boolean', isOptional=True, defaultValue=False)
            compare = self.checkParameter(request, 'compare', 'string', isOptional=True, defaultValue=None)

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

            return prepare_newpage(sentnum, compare=compare) #, iscompare=iscompare)

        @app.route('/read', methods=["GET"])
        def read():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=False, defaultValue=None)
            #iscompare = self.checkParameter(request, 'compare', 'boolean', isOptional=True, defaultValue=False)
            compare = self.checkParameter(request, 'compare', 'string', isOptional=True, defaultValue=None)
            #sentnum = int(sentnum)
            if sentnum < 1 or sentnum > len(self.amrdoc.sentences):
                dico = {"error": "invalid sentence number: must be between 1 and %d" % len(self.amrdoc.sentences)}
                return Response("%s\n" % json.dumps(dico),
                                400, mimetype="application/json")

            #for x in self.aps:
            #    print("AAAAAPPPP", x, self.aps[x].lastpm)
            return prepare_newpage(sentnum, compare=compare) #, iscompare=iscompare)

        @app.route('/graphs/<filename>', methods=["GET"])
        def downloadgraphs(filename: str):
            dataformat = self.checkParameter(request, 'format', 'string', isOptional=True, defaultValue="svg")
            pages = self.checkParameter(request, 'sentences', 'string', isOptional=True, defaultValue=None)

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
                for ix, x in enumerate(self.aps, 1):
                    if pages and ix not in pages:
                        continue
                    ap = self.aps[x]
                    if not ap.isparsed:
                        ap.readpenman(ap.lastpm)
                    pm, svg = ap.show(format=dataformat)
                    if svg:
                        zip_file.writestr("%d.%s" % (ix, dataformat), svg)
                    #print("FILE", ix, svg[:100] if svg else svg)

            return Response(zip_buffer.getvalue(), 200, mimetype="application/zip")

        @app.route('/save', methods=["GET"])
        def save():
            sentnum = self.checkParameter(request, 'num', 'integer', isOptional=True, defaultValue=1)
            #sentnum = int(sentnum)

            self.save()

            if sentnum < 1 or sentnum > len(self.amrdoc.sentences):
                dico = {"error": "invalid sentence number: must be between 1 and %d\n" % len(self.amrdoc.sentences)}
                return Response("%s\n" % json.dumps(dico),
                                400, mimetype="application/json")

            #for x in self.aps:
            #    print("AAAAAPPPP", x, self.aps[x].lastpm)
            return prepare_newpage(sentnum)

        @app.errorhandler(ServerException)
        def handle_invalid_usage(error):
            response = jsonify({"error": error.value}) #jsonify(error.to_dict())
            response.status_code = 400 #error.status_code
            return response

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
            dico = {"penman": pm, "svg": "",
                    "warning": warnings, "framedoc": "", "readonly": self.readonly,
                    "filename": filename, "numsent": len(self.amrdoc.sentences),
                    "num": sentnum,
                    "text": cursentence.text,
                    "comments": "\n".join(cursentence.comments),
                    "sentid": cursentence.id,
                    "undos": len(self.undos),
                    "redos": len(self.redos)
                    }
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        def prepare_newpage(sentnum, oktext=None, okamr=None, compare=None): #, iscompare=False):
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

            pm, svg = ap.show()
            if not ap.valid:
                return invalidamr(ap, pm, cursentence, sentnum)

            #iscompare = self.comparefilename is not None
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
                #print("aaaaaaaaaaaaae", oktext, list(oktext))
                for mo in reversed(list(oktext)):
                    sentencetext = sentencetext[:mo.start()] + '<span class="highlight">%s</span>' % sentencetext[mo.start():mo.end()] + sentencetext[mo.end():]

            warnings = ap.validate(valfuncs=[self.amr_rels.validate, self.pbframes.validate, self.constraints.validate])
            if len(warnings) < 1:
                warnings = None

            framedoc = None
            framedocs = self.pbframes.getdoc(ap.triples)
            if len(framedocs):
                framedoc = "\n".join(framedocs)

            lastchanged = cursentence.date
            if not lastchanged:
                lastchanged = cursentence.savedateorig

            dico = {"penman": pm, "svg": svg.decode("utf8"),
                    "warning": warnings, "framedoc": framedoc, "readonly": self.readonly,
                    "filename": filename, "numsent": len(self.amrdoc.sentences),
                    "num": sentnum,
                    "text": sentencetext, #cursentence.text,
                    "comments": "\n".join(cursentence.comments),
                    "sentid": cursentence.id,
                    "lastchanged": lastchanged,
                    "variables": sorted(list(set(ap.vars.keys()))),
                    "undos": len(self.undos),
                    "redos": len(self.redos)}
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
                sm = Smatch()
                best_match_num, test_triple_num, gold_triple_num, instances1OK, rel1OK, instances2OK, rel2OK = sm.get_amr_match(firstsent.amr.replace("\n", " "), secondsent.amr.replace("\n", " "))

                p, r, f1 = sm.compute_f(best_match_num, test_triple_num, gold_triple_num)
                if first_to_compare == -1:
                    # update display of first document
                    cpm, csvg = ap.show(highlightinstances=instances1OK, highlightrelations=rel1OK)
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
                        cpm, csvg = cap.show(highlightinstances=instances1OK, highlightrelations=rel1OK)
                    elif ix == second_to_compare:
                        cpm, csvg = cap.show(highlightinstances=instances2OK, highlightrelations=rel2OK)
                    else:
                        cpm, csvg = cap.show()

                    dico2 = {}
                    dico2["filename"] = doc.fn
                    dico2["svg"] = csvg.decode("utf8")
                    dico2["penman"] = cpm
                    dico2["comments"] = "\n".join(ccursentence.comments),
                    others.append(dico2)
                dico["others"] = others
                dico["smatch"] = "%.2f" % (f1 * 100)
                dico["bestmatch"] = best_match_num
                dico["left_triplenum"] = test_triple_num
                dico["right_triplenum"] = gold_triple_num

            #elif iscompare: #and self.comparedoc:
            #    ccursentence = self.comparedoc.sentences[sentnum - 1]
            #    if sentnum not in self.compare_aps:
            #        cap = amreditor.AMRProcessor()
            #        self.compare_aps[sentnum] = cap
            #        cap.readpenman(ccursentence.amr)
            #    else:
            #        cap = self.compare_aps[sentnum]
            #        if not cap.isparsed:
            #            cap.readpenman(ccursentence.amr)
            #    sm = Smatch()
            #    best_match_num, test_triple_num, gold_triple_num, instances1OK, rel1OK, instances2OK, rel2OK = sm.get_amr_match(pm.replace("\n", " "), ccursentence.amr.replace("\n", " "))
            #    #print("zzzz", best_match_num, test_triple_num, gold_triple_num, instances1OK, rel1OK, instances2OK, rel2OK, sep="\n>>>>")

            #    cpm, csvg = cap.show(highlightinstances=instances2OK, highlightrelations=rel2OK)

            #    # recreate SVG graph with highlights
            #    pm, svg = ap.show(highlightinstances=instances1OK, highlightrelations=rel1OK)

            #    p, r, f1 = sm.compute_f(best_match_num, test_triple_num, gold_triple_num)

            #    dico["filename2"] = self.comparefilename
            #    dico["smatch"] = "%.2f" % (f1 * 100)
            #    dico["bestmatch"] = best_match_num
            #    dico["left_triplenum"] = test_triple_num
            #    dico["right_triplenum"] = gold_triple_num
            #    dico["svg"] = svg.decode("utf8")
            #    dico["penman2"] = cpm
            #    dico["svg2"] = csvg.decode("utf8")
            #    dico["comments2"] = "\n".join(ccursentence.comments),

            #    if not cap.valid:
            #        return invalidamr(cap, pm, ccursentence, sentnum)

            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

    def start(self):
        self.app.run(host="0.0.0.0", port=self.port) #, threaded=False, processes=4)
        self.save()

    def save(self):
        if not self.readonly:
            print("saving", self.filename)
            self.savefile(self.filename, self.fileversion)
            # print("saved as %s.%s" % (self.filename, version))

    def findinvalidparameters(self, request, validlist):
        for k, v in request.values.items():
            #print("kkk", k,v)
            if k not in validlist:
                raise ServerException("invalid parameter '%s'" % k)

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
            #rtc = repo.git.status()
            try:
                #rtc = repo.git.diff(os.path.basename(fn))
                #if rtc:
                #    rtc = repo.git.add(os.path.basename(fn))
                rtc = repo.git.commit("-m", "metamorphosed AMR editor: %s of '%s' saved" % (", ".join(self.modified), fn), author=self.author)
                print("commited %s" % (fn), rtc)
                #else:
                #    print("nothing to commit for %s" % (fn), rtc)
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


class ServerException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--port", "-p", default=4567, type=int, help="port to use")
    parser.add_argument("--file", "-f", required=True, help="AMR file to edit")
    parser.add_argument("--compare", nargs="+", help="AMR file of additional annotators")
    #parser.add_argument("--compare", help="2nd AMR file to compare with first. Implies --readonly")
    parser.add_argument("--author", help="author (for git), use format 'Name <mail@example.com>', if absent current user+mail is used")
    parser.add_argument("--relations", "-R", default=None, help="list of valid AMR-relations (simple text file with list of all valid relations)")
    parser.add_argument("--concepts", "-C", default=None, help="list of valid AMR-concepts (simple text file with list of all valid concepts)")
    parser.add_argument("--pbframes", "-P", default=None, help="Propbank frameset documentation (directory with xml files)")
    parser.add_argument("--constraints", "-c", default=None, help="constraints for subjects and predicates (yaml file)")
    parser.add_argument("--readonly", "--ro", default=False, action="store_true", help='browse corpus only')
    parser.add_argument("--reifications", "-X", default=None, help="table for (de)reification")
    parser.add_argument("--nogit", dest="git", default=True, action="store_false", help='no git add/commit, even if file is git controlled (does nevertheless overwrite existing file)')

    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()
        try:
            aes = AMR_Edit_Server(args.port, args.file, args.pbframes,
                                  args.relations, args.concepts,
                                  args.constraints, args.readonly,
                                  author=args.author,
                                  reifications=args.reifications,
                                  do_git=args.git,
                                  compare=args.compare)
            aes.start()
        except Exception as e:
            print(e, file=sys.stderr)
