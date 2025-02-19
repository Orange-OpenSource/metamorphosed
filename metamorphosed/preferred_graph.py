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

import json
import os
import time

from metamorphosed.exception import ServerException

NOT_CHOSEN = "not_chosen"

class PreferredGraphs:
    def __init__(self, amrfiledict, preferredfile):
        self.filedict = amrfiledict
        #self.filedict = {self.filename: self.amrdoc}
        self.preferredfile = preferredfile
        self.preferred = {}

        self.num_sentences = len(next(iter(self.filedict.values())).sentences)
        self.main_doc = next(iter(self.filedict.values()))
        if os.path.isfile(preferredfile):
            with open(preferredfile) as ifp:
                obj = json.load(ifp)
                #print(obj)
                if "preferred" not in obj:
                    raise ServerException("bad format for preferred file '%s' does not contain 'preferred'" % (preferredfile))
                if "files" not in obj:
                    raise ServerException("bad format for preferred file '%s' does not contain 'files'" % (preferredfile))
                self.preferred = obj["preferred"]
                if (set(self.filedict.keys())) != set(obj["files"]):
                    raise ServerException("files specified preferred file '%s' do not correspond to files given '%s' != '%s'" % (preferredfile, list(self.filedict.keys()), obj["files"]))
                # must be {"pos": position of sentence in file # Attention: must be a stringnot an int ! json.dumps() silently transforms int keys in strings
                #             {
                #               "sid": sentence id
                #               "source": filename with best graph
                #             }
                #          }
                # TODO check with jsonschema

                # check whether all sources in this file are loaded via --compare
                for pos, obj in self.preferred.items():
                    if obj.get("source") not in self.filedict and obj.get("source") != NOT_CHOSEN:
                        raise ServerException("preferred file '%s' contains a source (pos:%s, sid:%s) '%s' not used in this session" % (preferred, pos, obj.get("sid"), obj.get("source")))

    def set(self, sentnum, sent, source):
        # set source of preferred graph
        self.preferred[str(sentnum)] = {"sid": sent.id, "source": source}

    def get(self, sentnum):
        # set source of preferred graph
        sentnumstr = str(sentnum) # needs to be a string since the json file (which is written) cannot have int keys
        if sentnumstr in self.preferred:
            return self.preferred[sentnumstr]
        else:
            return None

    def save(self):
        outfn = self.preferredfile
        if outfn.endswith(".json"):
            outfnbase = outfn[:-5]
        else:
            outfnbase = outfn
        with open(outfnbase + ".amr.txt", "w") as ofp:
            print(" *  saving preferred graphs into", outfn + ".amr.txt")
            for pos in range(self.num_sentences):
                strpos = str(pos + 1)
                if strpos in self.preferred:
                    source = self.preferred[strpos]["source"]
                    if source != NOT_CHOSEN:
                        adoc = self.filedict[source]
                        sent = adoc.sentences[pos]
                        now = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
                        sent.comments.append("::preferred %s ::choose-date %s" % (source, now))
                        sent.write(ofp)
                else:
                    # not yet chosen, output empty graph
                    self.main_doc.sentences[pos].write(ofp, onlyheader=True)
                    print("()\n", file=ofp)

            if os.path.isfile(outfn):
                outfn += ".2"

            with open(outfn, "w") as ofp:
                print(" *  saving list of preferred graphs in", outfn)
                # self.otheramrdocs = [doc,aps]
                dico = {"files": list(self.filedict.keys())}
                sortedpreferred = {}
                for key in sorted(self.preferred, key=int):
                    if self.preferred[key]["source"] != NOT_CHOSEN:
                        sortedpreferred[key] = self.preferred[key]
                dico["preferred"] = sortedpreferred
                if len(sortedpreferred) != len(self.main_doc.sentences):
                    print(" ** ATTENTION output file incomplete, for some sentences no preferred graphs has been chosen")
                print(json.dumps(dico, indent=2, ensure_ascii=False), file=ofp)
