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
import json
import os
import re
import socket
from flask import Flask, escape, request, Response, redirect, render_template, jsonify
import git

import corefeditor
import pathlib
parent = pathlib.Path(os.path.abspath(__file__)).parent.parent
sys.path.append(str(parent))
import gitinterface

APIVERSION=1.0

class CorefServer:
    def __init__(self, port, xmlfiles, amrfiles, author=None, do_git=True):
        self.port = port
        self.author = author
        self.editor = corefeditor.CorefEditor(xmlfiles, amrfiles)
        self.modifiedfiles = set()
        self.do_git = do_git
        mydir = os.path.abspath(os.path.dirname(__file__))
        app = Flask(__name__,
                    static_url_path='',
                    static_folder="%s/../gui" % mydir,
                    template_folder="%s/../gui" % mydir)
        app.config['TEMPLATES_AUTO_RELOAD'] = True # needed to reload index.html
        self.app = app

        self.isInt = re.compile(r"^\d+$")
        self.isFloat = re.compile(r"^\d*\.?\d+$")


        @app.route('/',methods=["GET"])
        def index():
            # Displays the index page accessible at '/'
            return render_template('coref.html', toolname="AMR Coreference Editor")

        @app.route('/version',methods=["GET"])
        def version():
            dico = {"name": "AMR Coreference Editor",
                    "version": corefeditor.VERSION,
                    "apiversion": APIVERSION}
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        @app.route('/info',methods=["GET"])
        def info():
            dico = {"cmdline": " ".join(sys.argv),
                    "pwd": os.getcwd(),
                    "hostname": socket.gethostname(),
                    #"filename": filename, "numsent": len(self.amrdoc.sentences),
                    #"propbank_frames": pbframes,
                    #"amr_relations": rels,
                    #"readonly": readonly,
                    "version": corefeditor.VERSION,
                    "apiversion": APIVERSION
                    }
            return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

        @app.route('/read', methods=["GET"])
        def read():
            sentgroupnum = self.checkParameter(request, 'num' , 'integer', isOptional=False, defaultValue=None)
            showfrom = self.checkParameter(request, 'showfrom' , 'integer', isOptional=True, defaultValue=0)
            shownumber = self.checkParameter(request, 'shownumber' , 'integer', isOptional=True, defaultValue=0)
            scaling = self.checkParameter(request, 'scaling' , 'float', isOptional=True, defaultValue=1)

            if sentgroupnum < 1 or sentgroupnum > len(self.editor.sentencegroups):
                dico = {"error": "invalid sentence number: must be between 1 and %d\n" % len(self.editor.sentencegroups)}
                return Response("%s\n" % json.dumps(dico),  400, mimetype="application/json")

            return self.prepare_newpage(sentgroupnum, showfrom, shownumber, scaling)


        @app.route('/next', methods=["GET"])
        def next():
            sentgroupnum = self.checkParameter(request, 'num' , 'integer', isOptional=False, defaultValue=None)
            direction = self.checkParameter(request, 'direction' , 'string', isOptional=False, defaultValue=None)
            showfrom = self.checkParameter(request, 'showfrom' , 'integer', isOptional=True, defaultValue=0)
            shownumber = self.checkParameter(request, 'shownumber' , 'integer', isOptional=True, defaultValue=0)
            scaling = self.checkParameter(request, 'scaling' , 'float', isOptional=True, defaultValue=1)

            if direction == "preceding":
                if sentgroupnum > 1:
                    sentgroupnum -= 1
            elif direction == "next":
                if sentgroupnum < len(self.editor.sentencegroups):
                    sentgroupnum += 1
            elif direction == "first":
                sentgroupnum = 1
            elif direction == "last":
                sentgroupnum = len(self.editor.sentencegroups)

            return self.prepare_newpage(sentgroupnum, showfrom, shownumber, scaling)

        @app.route('/addtochain', methods=["GET"])
        def addto():
            sentgroupnum = self.checkParameter(request, 'num' , 'integer', isOptional=False)
            takechainfrom = self.checkParameter(request, 'from' , 'string', isOptional=False)
            jointochain = self.checkParameter(request, 'to' , 'string', isOptional=False)
            showfrom = self.checkParameter(request, 'showfrom' , 'integer', isOptional=True, defaultValue=0)
            shownumber = self.checkParameter(request, 'shownumber' , 'integer', isOptional=True, defaultValue=0)
            scaling = self.checkParameter(request, 'scaling' , 'float', isOptional=True, defaultValue=1)

            #print("ATC", sentgroupnum, takechainfrom, jointochain)
            #sg = self.editor.sentencegroups[sid]
            key = list(self.editor.sentencegroups.keys())[sentgroupnum-1]
            sg = self.editor.sentencegroups[key]

            modified = sg.addtochain(takechainfrom, jointochain)
            if modified:
                self.modifiedfiles.add(sg)
            return self.prepare_newpage(sentgroupnum, showfrom, shownumber, scaling)
            


        @app.route('/modifycomment', methods=["GET"])
        def modcomment():
            sentgroupnum = self.checkParameter(request, 'num' , 'integer', isOptional=False)
            showfrom = self.checkParameter(request, 'showfrom' , 'integer', isOptional=True, defaultValue=0)
            shownumber = self.checkParameter(request, 'shownumber' , 'integer', isOptional=True, defaultValue=0)
            scaling = self.checkParameter(request, 'scaling' , 'float', isOptional=True, defaultValue=1)
            comment = self.checkParameter(request, 'comment' , 'string', isOptional=True, defaultValue="")

            key = list(self.editor.sentencegroups.keys())[sentgroupnum-1]
            sg = self.editor.sentencegroups[key]

            if sg.comment != comment:
                sg.comment = comment
                self.modifiedfiles.add(sg)
            return self.prepare_newpage(sentgroupnum, showfrom, shownumber, scaling)


        @app.route('/save', methods=["GET"])
        def save():
            sentgroupnum = self.checkParameter(request, 'num' , 'integer', isOptional=True, defaultValue=1)
            showfrom = self.checkParameter(request, 'showfrom' , 'integer', isOptional=True, defaultValue=0)
            shownumber = self.checkParameter(request, 'shownumber' , 'integer', isOptional=True, defaultValue=0)
            scaling = self.checkParameter(request, 'scaling' , 'float', isOptional=True, defaultValue=1)

            #key = list(self.editor.sentencegroups.keys())[sentgroupnum-1]
            #sg = self.editor.sentencegroups[key]
            #print("saving", sentgroupnum, sg.xmlfile)
            version = "2"
            messages, warnings = self.savefiles(version)

            return self.prepare_newpage(sentgroupnum, showfrom, shownumber, scaling, warnings, messages)

        @app.errorhandler(ServerException)
        def handle_invalid_usage(error):
            response = jsonify({"error": error.value}) #jsonify(error.to_dict())
            response.status_code = 400 #error.status_code
            return response

    def prepare_newpage(self, num, showfrom, shownumber, scaling, warnings=None, messages=None):
        #print("eeee", showfrom, shownumber)
        #if showfrom.strip() != "":
        #    showfrom = int(showfrom)
        #else:
        #    showfrom = None
        #if shownumber.strip() != "":
        #    shownumber = int(shownumber)
        #else:
        #    shownumber = None

        
        #print("NNN", showfrom, shownumber)
        key = list(self.editor.sentencegroups.keys())[num-1]
        sg = self.editor.sentencegroups[key]
        svgs, chaintable = sg.multiformat("svg", showfrom, shownumber, scaling)
        dico = { #"svg": sg.format(),
            "svgdict": svgs,
            "chaintable": chaintable,
            "comment": sg.comment,
            "warnings": warnings, "messages": messages,
            "filename": sg.xmlfile,
            "numsent": len(self.editor.sentencegroups),
            "num": num,
                 #"comments": "\n".join(cursentence.comments),
                 #"sentid": cursentence.id,
                 #"lastchanged": lastchanged,
                 #    "variables": sorted(list(set(ap.vars.keys()))),
                 #    "undos": len(self.undos),
                 #    "redos": len(self.redos)
            }
        
        return Response("%s\n" % json.dumps(dico), 200, mimetype="application/json")

    def savefiles(self, sgs, version="2"):
        atleastonegitok = False
        modified = []
        messages = []
        warnings = []
        for sg in self.modifiedfiles:
            fn = sg.xmlfile
            repo, saveok, gitok = gitinterface.save(fn, version, sg.xml,
                                                    warnings, messages, self.do_git)
            if gitok:
                atleastonegitok = True

        if atleastonegitok and self.do_git:
            rtc = repo.git.commit("-m", "metamorphosed coref editor: %s files saved" % (len(self.modifiedfiles)), author=self.author)
            print("commited %s" % (fn), rtc)

        self.modifiedfiles = set()
        if not warnings:
            warnings = None
        if not messages:
            messages = None
        return messages, warnings


#    def oosavefiles(self, sgs, version="2"):
#        atleastonegitok = False
#        modified = []
#        messages = []
#        warnings = []
#        for sg in self.modifiedfiles:
#            fn = sg.xmlfile
#            gitok = False
#            try:
#                print("check git for <%s>" % fn)
#                repo = git.Repo(os.path.dirname(fn))
#                print("ZZZZ", repo.untracked_files)
#                if fn in repo.untracked_files:
#                    raise FileNotGitControlled("%s not controlled by git" % fn)
#                    
#                gitok = True
#
#                # file versioned under git, we overwrite the input file
#                print("writing orig")
#                ofp = open(fn, "w")
#            except (git.exc.InvalidGitRepositoryError, FileNotGitControlled)  as e:
#                print("no git repo", e)
#                # file not versioned, we write a new file
#                try:
#                    ofp = open(fn + "." + version, "w")
#                except Exception as e:
#                    print("cannot write %s" % fn, e)
#                    warnings.append("cannot write %s: %s. File not saved" % (fn, e))
#                    continue
#
#            print(sg.xml(), file=ofp)
#            print("%s written (git: %s)" % (ofp.name, gitok))
#            messages.append("%s written (git: %s)" % (ofp.name, gitok))
#            ofp.close()
#
#            if gitok:
#                #rtc = repo.git.status()
#                try:
#                    rtc = repo.git.diff(os.path.basename(fn))
#                    if rtc:
#                        rtc = repo.git.add(os.path.basename(fn))
#                        atleastonegitok = True
#                        #rtc = repo.git.commit("-m", "metamorphosed coref editor: %s of '%s' saved" % (", ".join(modified), fn), author=self.author)
#                        #print("commited %s" % (fn), rtc)
#                    else:
#                        print("nothing to commit for %s" % (fn), rtc)
#                except Exception as e:
#                    print("COMMIT Error <%s> <%s> <%s>" % (e, fn, rtc))
#                    warnings.append("commit error <%s> <%s> <%s>" % (e, fn, rtc))
#                    pass
#        if atleastonegitok:
#            rtc = repo.git.commit("-m", "metamorphosed coref editor: %s files saved" % (len(self.modifiedfiles)), author=self.author)
#            print("commited %s" % (fn), rtc)
#
#        self.modifiedfiles = set()
#        if not warnings:
#            warnings = None
#        if not messages:
#            messages = None
#        return messages, warnings


    def start(self):
        self.app.run(host="0.0.0.0", port=self.port) #, threaded=False, processes=4)
        version = "2"
        self.savefiles(self.modifiedfiles, version)



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
            if len(value) == 0:
                raise ServerException("Parameter '%s' must not be empty." % paramName)
            else:
                return str(value)
        if paramType == "boolean":
            if not( str(value).lower() in ("true", "1", "false", "0")):
                raise ServerException("Parameter '%s' should be a boolean (i.e. one of 'true', 'false', '0', '1')." % paramName)
            else:
                return (value.lower() in ("true", "1"))
        if paramType == "integer":
            if value == "" and isOptional:
                return defaultValue
            elif not self.isInt.match(value):
                raise ServerException("Parameter '%s' must be an integer." % paramName)
            else:
                return int(value)
        if paramType == "float":
            if value == "" and isOptional:
                return defaultValue
            elif not self.isFloat.match(value):
                raise ServerException("Parameter '%s' must be a float." % paramName)
            else:
                return float(value)

        raise ServerException("Another stupid error occurred. Invalid paramtype? %s %s" % (paramName, paramType))

class ServerException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)



if __name__ == "__main__":
    # ./corefserver.py -p 4567 -x pp_001.xml pp.amr.txt
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--port", "-p", default=4567, type=int, help="port to use")
    parser.add_argument("--xml", "-x", nargs="+", help="AMR file to edit")
    parser.add_argument("--amrfiles", "-a", nargs="+", help="AMR files which contain the indicated files")
    parser.add_argument("--author", default=None, help="author (for git), use format 'Name <mail@example.com>', if absent current user+mail is used")
    parser.add_argument("--nogit", dest="git", default=True, action="store_false", help='no git add/commit, even if file is git controlled')

    #parser.add_argument("--pbframes", "-P", default=None, help="Propbank frameset documentation (directory with xml files)")
    #parser.add_argument("--constraints", "-C", default=None, help="constraints for subjects and predicates (yaml file)")
    #parser.add_argument("--readonly", "--ro", default=False, action="store_true", help='browse corpus only')


    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()

        aes = CorefServer(args.port, args.xml, args.amrfiles, author=args.author, do_git=args.git)
        aes.start()

