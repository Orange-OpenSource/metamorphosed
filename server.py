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
# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke


import sys
import os
import re
import json
import time
import socket

from flask import Flask, escape, request, Response, redirect, render_template, jsonify
import git

import amreditor
import amrdoc
import AMR_relations
import propbank_frames
import relations_constraints
import reification
import gitinterface

# TODO
# detect errors
#  * a1 :rel a1
# undo/redo unstable if sentence is changed and a redo is possible

# find an example in AMR data
# call an AMRserver for an (empty) sentence ? rather not

APIVERSION="1.3.0"

class AMR_Edit_Server:
    def __init__(self, port, filename, pbframes, rels, concepts, constraints, readonly, author=None, reifications=None, do_git=True):
        self.port = port
        self.filename= filename
        self.amrdoc = amrdoc.AMRdoc(filename)
        self.aps = {} # parsed and possibly modified PENMAN AMRs
        self.author = author
        self.reificator = None
        self.do_git = do_git
        if reifications:
            self.reificator = reification.getInstance(reifications)

        self.fileversion = "2"
        if not gitinterface.is_git_controlled(filename):
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
            #ap.readpenman(cursentence.amr)
            #ap.show() # to create penman format with penman library (may differ from from PENMAN found in file: indenting etc)
            self.initstates.append(ap.lastpm)

        print("all sentences initialized")
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
        self.constraints = relations_constraints.Constraints(constraints)

        app = Flask(__name__,
                    static_url_path='',
                    static_folder="%s/gui" % mydir,
                    template_folder="%s/gui" % mydir)
        app.config['TEMPLATES_AUTO_RELOAD'] = True # needed to reload index.html
        self.app = app

        @app.route('/',methods=["GET"])
        def index():
            # Displays the index page accessible at '/'
            return render_template('index.html', toolname="AMR Editor")

        @app.route('/version',methods=["GET"])
        def version():
            dico = {"name": "AMR Editor",
                    "version": amreditor.VERSION,
                    "apiversion": APIVERSION}
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        @app.route('/info',methods=["GET"])
        def info():
            withdata = self.checkParameter(request, 'withdata' , 'boolean', isOptional=True, defaultValue=False)
            dico = {"cmdline": " ".join(sys.argv),
                    "pwd": os.getcwd(),
                    "hostname": socket.gethostname(),
                    "filename": filename, "numsent": len(self.amrdoc.sentences),
                    "propbank_frames": pbframes,
                    #"relations": sorted(self.amr_rels.relations),
                    #"concepts": sorted(self.amr_concepts.relations),
                    "readonly": readonly,
                    "version": amreditor.VERSION,
                    "apiversion": APIVERSION
                    }
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
            sentnum = self.checkParameter(request, 'num' , 'integer', isOptional=False)
            cmd = self.checkParameter(request, 'cmd' , 'string', isOptional=True, defaultValue=None)
            addconcept = self.checkParameter(request, 'addconcept' , 'string', isOptional=True, defaultValue=None)
            addname = self.checkParameter(request, 'addname' , 'string', isOptional=True, defaultValue=None)
            nameof = self.checkParameter(request, 'nameof' , 'string', isOptional=True, defaultValue=None)

            start = self.checkParameter(request, 'start' , 'string', isOptional=True, defaultValue=None)
            end = self.checkParameter(request, 'end' , 'string', isOptional=True, defaultValue=None)
            label = self.checkParameter(request, 'label' , 'string', isOptional=True, defaultValue=None)

            modconcept = self.checkParameter(request, 'modconcept' , 'string', isOptional=True, defaultValue=None)
            newconcept = self.checkParameter(request, 'newconcept' , 'string', isOptional=True, defaultValue=None)


            newtop = self.checkParameter(request, 'newtop' , 'string', isOptional=True, defaultValue=None)

            delinstance = self.checkParameter(request, 'delinstance' , 'string', isOptional=True, defaultValue=None)

            modedge_start = self.checkParameter(request, 'modedge_start' , 'string', isOptional=True, defaultValue=None)
            modedge_end = self.checkParameter(request, 'modedge_end' , 'string', isOptional=True, defaultValue=None)
            newedge = self.checkParameter(request, 'newedge' , 'string', isOptional=True, defaultValue=None)
            moveedge_newstart = self.checkParameter(request, 'modedge_newstart' , 'string', isOptional=True, defaultValue=None)

            deledge_start = self.checkParameter(request, 'deledge_start' , 'string', isOptional=True, defaultValue=None)
            deledge_end = self.checkParameter(request, 'deledge_end' , 'string', isOptional=True, defaultValue=None)
            deledge = self.checkParameter(request, 'deledge' , 'string', isOptional=True, defaultValue=None)

            literalid = self.checkParameter(request, 'literalid' , 'string', isOptional=True, defaultValue=None)
            literaledge = self.checkParameter(request, 'literaledge' , 'string', isOptional=True, defaultValue=None)
            newliteral = self.checkParameter(request, 'newliteral' , 'string', isOptional=True, defaultValue=None)
            delliteral = self.checkParameter(request, 'delliteral' , 'string', isOptional=True, defaultValue=None)

            literalof = self.checkParameter(request, 'literalof' , 'string', isOptional=True, defaultValue=None)
            relationforliteral = self.checkParameter(request, 'relationforliteral' , 'string', isOptional=True, defaultValue=None)
            newliteral = self.checkParameter(request, 'newliteral' , 'string', isOptional=True, defaultValue=None)

            modpenman = self.checkParameter(request, 'modpenman' , 'string', isOptional=True, defaultValue=None)
            modcomment = self.checkParameter(request, 'modcomment' , 'string', isOptional=True, defaultValue=None)
            reify = self.checkParameter(request, 'reify' , 'string', isOptional=True, defaultValue=None)
            dereify = self.checkParameter(request, 'dereify' , 'string', isOptional=True, defaultValue=None)



            print("COMMAND:", end=" ")
            for v in ["cmd",
                      "addconcept",
                      "addname", "nameof",
                      "start", "label", "end",
                      "modconcept", "newconcept",
                      "modedge_start", "modedge_end", "newedge", "moveedge_newstart",
                      "delinstance",
                      "deledge_start", "deledge_end", "deledge",
                      "literalid", "literaledge", "newliteral", "delliteral",
                      "literalof", "relationforliteral", "newliteral",
                      "modpenman",
                      "modcomment",
                      "reify", "dereify",
                      "newtop"]:
                if eval(v) != None:
                    print('%s: "%s"' % (v, eval(v)), end=" ")
            print()

            ap = self.aps.get(int(sentnum))

            if not ap.isparsed:
                ap.readpenman(ap.lastpm)
                ap.show()

            cursentence = self.amrdoc.sentences[sentnum-1]
            if not ap.valid and modpenman == None:
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
                for i,w in enumerate(words):
                    ap.addedge(var, '"%s"' % w, ":op%d" % (i+1))
                ap.addedge(nameof, var, "name")
            elif start and end and label:
                rtc = ap.addedge(start, end, label)
            elif modconcept and newconcept:
                ap.modconcept(modconcept, newconcept)
            elif modedge_start and modedge_end and newedge:
                if moveedge_newstart:
                    rtc = ap.moveedge(modedge_start, modedge_end, newedge, moveedge_newstart)
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
                                      self.amrdoc.sentences[sentnum-1],
                                      sentnum)
                else:
                    newap.show() # to create penman
                    self.aps[sentnum] = newap
                    ap = newap
                    ap.modified = True # set rather by ap.-functions ??
            elif modcomment != None:
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
            pm,svg = ap.show()

            framedoc = None
            framedocs = self.pbframes.getdoc(ap.triples)
            if len(framedocs):
                framedoc = "\n".join(framedocs)


            warnings = []
            if isinstance(rtc, list):
                warnings.extend(rtc)
            elif isinstance(rtc, str):
                warnings.append(rtc)
            warnings += ap.validate(valfuncs = [self.amr_rels.validate, self.amr_concepts.validate, self.pbframes.validate, self.constraints.validate])
            if len(warnings) < 1:
                warnings = None
            cursentence = self.amrdoc.sentences[sentnum-1]
            lastchanged = cursentence.date
            if not lastchanged:
                lastchanged = cursentence.savedateorig
            dico = { "warning": warnings, "framedoc": framedoc, "readonly": readonly,
                     "penman": pm, "svg": svg.decode("utf8") if svg else "",
                     "filename": filename, "numsent": len(self.amrdoc.sentences),
                     "num": sentnum,
                     "text": cursentence.text,
                     "comments": "\n".join(cursentence.comments),
                     "sentid": cursentence.id,
                     "lastchanged": lastchanged,
                     "variables": sorted(list(set(ap.vars.keys()))),
                     "undos": len(self.undos),
                     "redos": len(self.redos) }
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")


        @app.route('/search', methods=["GET"])
        def search():
            sentnum = self.checkParameter(request, 'num' , 'integer', isOptional=False, defaultValue=None)
            what = self.checkParameter(request, 'what' , 'string', isOptional=False, defaultValue=None)
            regex = self.checkParameter(request, 'regex' , 'string', isOptional=False, defaultValue=None)

            okt = None
            oka = None
            if what == "findtextnext":
                for x in range(sentnum, len(self.amrdoc.sentences)):
                    okt = list(self.amrdoc.sentences[x].findtext(regex))
                    if okt:
                        sentnum = x+1
                        break
            elif what == "findidnext":
                for x in range(sentnum, len(self.amrdoc.sentences)):
                    ok = self.amrdoc.sentences[x].findid(regex)
                    if ok:
                        sentnum = x+1
                        break
            elif what == "findamrnext":
                for x in range(sentnum+1, len(self.amrdoc.sentences)+1):
                    #oka = list(self.amrdoc.sentences[x].findamr(regex))
                    oka = list(self.aps[x].findamr(regex))
                    if oka:
                        sentnum = x
                        break
            elif what == "findtextprec":
                for x in range(sentnum-2, -1, -1):
                    okt = list(self.amrdoc.sentences[x].findtext(regex))
                    if okt:
                        sentnum = x+1
                        break
            elif what == "findidprec":
                for x in range(sentnum-2, -1, -1):
                    ok = self.amrdoc.sentences[x].findid(regex)
                    if ok:
                        sentnum = x+1
                        break
            elif what == "findamrprec":
                for x in range(sentnum-1, 0, -1):
                    oka = list(self.aps[x].findamr(regex))
                    #oka = list(self.amrdoc.sentences[x].findamr(regex))
                    if oka:
                        sentnum = x
                        break
            #print("OKA",oka)
            #print("OKT",okt)
            return prepare_newpage(sentnum, okt, oka)

        @app.route('/history', methods=["GET"])
        def history():
            sentnum = self.checkParameter(request, 'num' , 'integer', isOptional=False, defaultValue=None)
            history = self.checkParameter(request, 'history' , 'string', isOptional=False, defaultValue=None)

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
            sentnum = self.checkParameter(request, 'num' , 'integer', isOptional=False, defaultValue=None)
            direction = self.checkParameter(request, 'direction' , 'string', isOptional=False, defaultValue=None)

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

            return prepare_newpage(sentnum)


        @app.route('/read', methods=["GET"])
        def read():
            sentnum = self.checkParameter(request, 'num' , 'integer', isOptional=False, defaultValue=None)
            #sentnum = int(sentnum)
            if sentnum < 1 or sentnum > len(self.amrdoc.sentences):
                dico = {"error": "invalid sentence number: must be between 1 and %d\n" % len(self.amrdoc.sentences)}
                return Response("%s\n" % json.dumps(dico),
                                400, mimetype="application/json")

            #for x in self.aps:
            #    print("AAAAAPPPP", x, self.aps[x].lastpm)
            return prepare_newpage(sentnum)

        @app.route('/save', methods=["GET"])
        def save():
            sentnum = self.checkParameter(request, 'num' , 'integer', isOptional=True, defaultValue=1)
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
                                                                    text[pos:pos+endpos],
                                                                    text[pos+endpos:]
                                                                    )
            warnings = ["format error: %s in line %s:%s « %s », please correct file in a text editor first" %
                        (ap.parsererror["message"],
                         ap.parsererror["lineno"],
                         ap.parsererror["offset"],
                         text)
                        ]
            dico = { "penman": pm, "svg": "",
                     "warning": warnings, "framedoc": "", "readonly": readonly,
                     "filename": filename, "numsent": len(self.amrdoc.sentences),
                     "num": sentnum,
                     "text": cursentence.text,
                     "comments": "\n".join(cursentence.comments),
                     "sentid": cursentence.id,
                     "undos": len(self.undos),
                     "redos": len(self.redos)
                     }
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        def prepare_newpage(sentnum, oktext=None, okamr=None):
            # sentnum uses 1 ... length
            # self.amrdoc.sentences is a list: 0 length-1
            cursentence = self.amrdoc.sentences[sentnum-1]
            if not sentnum in self.aps:
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

            if okamr:
                # rerun search, because ap has reformated the original penman (possibly different indentation)
                # so to highlight the search result correctly we apply the search in the (now reformatted) penman
                okamr = list(ap.findamr(okamr[0].re.pattern))
                for mo in reversed(list(okamr)):
                    pm = pm[:mo.start()] + '<span class="highlight">%s</span>' % pm[mo.start():mo.end()] + pm[mo.end():]


            sentencetext = cursentence.text
            if sentencetext:
                sentencetext = sentencetext.replace("<", "&lt;").replace(">", "&gt;");
            if oktext:
                #print("aaaaaaaaaaaaae", oktext, list(oktext))
                for mo in reversed(list(oktext)):
                    sentencetext = sentencetext[:mo.start()] + '<span class="highlight">%s</span>' % sentencetext[mo.start():mo.end()] + sentencetext[mo.end():]



            warnings = ap.validate(valfuncs = [self.amr_rels.validate, self.pbframes.validate, self.constraints.validate])
            if len(warnings) < 1:
                warnings = None

            framedoc = None
            framedocs = self.pbframes.getdoc(ap.triples)
            if len(framedocs):
                framedoc = "\n".join(framedocs)

            lastchanged = cursentence.date
            if not lastchanged:
                lastchanged = cursentence.savedateorig

            dico = { "penman": pm, "svg": svg.decode("utf8"),
                     "warning": warnings, "framedoc": framedoc, "readonly": readonly,
                     "filename": filename, "numsent": len(self.amrdoc.sentences),
                     "num": sentnum,
                     "text": sentencetext, #cursentence.text,
                     "comments": "\n".join(cursentence.comments),
                     "sentid": cursentence.id,
                     "lastchanged": lastchanged,
                     "variables": sorted(list(set(ap.vars.keys()))),
                     "undos": len(self.undos),
                     "redos": len(self.redos) }
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")



    def start(self):
        self.app.run(host="0.0.0.0", port=self.port) #, threaded=False, processes=4)
        self.save()

    def save(self):
        print("saving", self.filename)
        self.savefile(self.filename, self.fileversion)
        #print("saved as %s.%s" % (self.filename, version))



    def checkParameter(self, request, paramName, paramType, isOptional=False, defaultValue=None):
        # needed for curl -F txt=@file.txt
        if paramName in request.files:
            bstr = request.files[paramName].read()
            return bstr.decode("UTF-8")



        #for k,v in request.values.items():
        #    print("kkk", k,v)
        if not(paramName in request.values):
            if not isOptional:
                #raise apifactory_errors.Error(27)
                raise ServerException("missing mandatory parameter '%s'" % paramName)

            else:
                return defaultValue

        value=request.values[paramName].strip()
        #print("nnnn", paramType, value)
        if paramType == "string":
            if len(value) == 0 and not isOptional:
                raise ServerException("Parameter '%s' must not be empty." % paramName)
            else:
                return str(value)
        if paramType == "boolean":
            if not( str(value).lower() in ("true", "1", "false", "0")):
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
                                                warnings, messages, do_add = self.do_git)

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
            if i+1 in self.aps:
                if self.aps[i+1].modified:
                    self.modified.append(str(i+1))
                    sent.date = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
                sent.write(ofp, onlyheader=True)
                #print("SENT", i+1, self.aps[i+1].modified, sent.id, sent.text, self.aps[i+1].triples)
                self.aps[i+1].write(ofp)
            else:
                sent.write(ofp)




#    def oosavefile(self, fn, version="2"):
#        gitok = False
#        try:
#            repo = git.Repo(os.path.dirname(fn))
#            gitok = True
#            # file versioned under git, we overwrite the input file
#            ofp = open(fn, "w")
#        except:
#            # file not versioned, we write a new file
#            ofp = open(fn + "." + version, "w")
#
#        modified = []
#        for i, sent in enumerate(self.amrdoc.sentences):
#            if i+1 in self.aps:
#                if self.aps[i+1].modified:
#                    modified.append(str(i+1))
#                    sent.date = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
#                sent.write(ofp, onlyheader=True)
#                #print("SENT", i+1, self.aps[i+1].modified, sent.id, sent.text, self.aps[i+1].triples)
#                self.aps[i+1].write(ofp)
#            else:
#                sent.write(ofp)
#        print("written %s" % ofp.name)
#        ofp.close()
#
#        if gitok:
#            #rtc = repo.git.status()
#            try:
#                rtc = repo.git.diff(os.path.basename(fn))
#                if rtc:
#                    rtc = repo.git.add(os.path.basename(fn))
#                    rtc = repo.git.commit("-m", "metamorphosed AMR editor: %s of '%s' saved" % (", ".join(modified), fn), author=self.author)
#                    print("commited %s" % (fn), rtc)
#                else:
#                    print("nothing to commit for %s" % (fn), rtc)
#            except Exception as e:
#                print("COMMIT Error <%s> <%s> <%s>" % (e, fn, rtc))
#                pass

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
                                  do_git=args.git)
            aes.start()
        except Exception as e:
            print(e, file=sys.stderr)
