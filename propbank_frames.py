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


# loads propbank frames in XML format
# https://github.com/propbank/propbank-frames/ or AMR3 data
import glob
import re
import xml.etree.ElementTree as ET


class Lemma:
    def __init__(self, lemma):
        self.lemma = lemma
        self.rolesets = []

    def __str__(self):
        template = '<h2>%s</h2>\n' % self.lemma
        print("LLLLL", self.lemma, self.rolesets)
        for r in self.rolesets:
            template += "%s\n" % r
        #template += ""
        return template


class Roleset:
    def __init__(self, rid, name):
        self.id = rid
        self.name = name
        self.roles = {} # role: def
        self.examples = []

    def __str__(self):
        #print("ZZZ2", self.id, self.name)
        template = '<h3>%s: <i>%s</i></h3>' % (self.id, self.name)
        template += '<h4>role definitions</h4>\n<ul>\n'
        for r, d in self.roles.items():
            template += '<li><span class="ARG%stext">ARG%s</span>: %s\n' % (r, r, d)
        template += "</ul>"
        template += '<h4>examples</h4>\n<ul>\n'
        for e in self.examples:
            template += "<li><i>%s</i>\n" % (e)
        template += "</ul>\n<hr/>"
        return template


class Example:
    def __init__(self):
        self.text = None
        self.args = {} #  ARG: argument
        self.rel = None

    def __str__(self):
        res = self.text
        for a, t in self.args.items():
            try:
                res = re.sub(r"((?<=\W)|^)%s(?=\W)" % t, '<span class="%stext">%s</span>' % (a, t), res)
            except Exception as e:
                print("Problem in PropBank documentation", e)

        if self.rel:
            #res = res.replace(self.rel, "<b>%s</b>" % self.rel)
            res = res.replace(self.rel, '<span class="docinstance predname">%s</span>' % self.rel)
        return res


class PropBankFrames:
    def __init__(self, dirname):
        self.lemmas = {}
        self.rolesets = set() # all valid rolesets like take-01 etc
        self.roleset_args = {} # take-01: { ARG0: "taker" .... }

        #self.parsefile("%s/finance.xml" % dirname)
        #return

        i = 0
        for i, fn in enumerate(sorted(glob.glob("%s/*.xml" % dirname))):
            #print(fn)
            self.parsefile(fn)
            #break
        print("%d framesets loaded" % (i + 1))

        #for rs in self.roleset_args:
        #    print(rs)
        #    for a in self.roleset_args[rs]:
        #        print("   ", a, self.roleset_args[rs][a])

    def parsefile(self, fn):
        tree = ET.parse(fn)
        for predicate in tree.getroot():
            if predicate.tag == "predicate":
                #print("PRED", predicate.attrib)
                lemma = Lemma(predicate.attrib["lemma"].replace("_", "-"))
                self.lemmas[lemma.lemma] = lemma
                #print("LLLL", lemma)
                for predicateChild in predicate:
                    if predicateChild.tag == "roleset":
                        #print("   ",predicateChild.attrib)
                        roleset = Roleset(predicateChild.attrib["id"], predicateChild.attrib["name"])
                        roleset_args = {} # ARG0: Taker, ...
                        inuse = True
                        for rolesetChild in predicateChild:
                            #print("     ",rolesetChild)
                            if rolesetChild.tag == "roles":
                                for rolesChild in rolesetChild:
                                    if rolesChild.tag == "role":
                                        #print("         ", rolesChild.tag, rolesChild.attrib)
                                        argno = rolesChild.attrib["n"]
                                        roleset.roles[argno] = rolesChild.attrib["descr"]
                                        roleset_args[":ARG" + argno] = rolesChild.attrib["descr"]
                            elif rolesetChild.tag == "usagenotes":
                                for usage in rolesetChild:
                                    if usage.tag == "usage":
                                        if usage.attrib.get("resource") == "AMR" \
                                           and usage.attrib.get("version") == "2019" \
                                           and usage.attrib.get("inuse") == "-":
                                            inuse = False
                                            #print("Unused: Lemma <%s>, Roleset: <%s>" % (lemma.lemma, roleset.name))
                            elif rolesetChild.tag == "example":
                                #print("         ", rolesetChild.attrib)
                                ex = Example()
                                for exampleChild in rolesetChild:
                                    if exampleChild.tag == "text":
                                        #print("           ", exampleChild, exampleChild.text)
                                        #roleset.examples.append(exampleChild.text)
                                        roleset.examples.append(ex)
                                        ex.text = exampleChild.text
                                    elif exampleChild.tag == "arg":
                                        # old format
                                        if "n" in exampleChild.attrib:
                                            nn = exampleChild.attrib["n"]
                                            if nn in "0123456789":
                                                if exampleChild.text:
                                                    ex.args["ARG" + nn] = exampleChild.text.replace('[', ' ').replace(']', ' ')
                                                else:
                                                    ex.args["ARG" + nn] = ""

                                    elif exampleChild.tag == "rel":
                                        # oldformat
                                        ex.rel = exampleChild.text
                                    elif exampleChild.tag == "propbank":
                                        # newer format
                                        for pb in exampleChild:
                                            if pb.tag == "arg":
                                                if "type" in pb.attrib:
                                                    nn = pb.attrib["type"]
                                                    #print("NNNN", pb.text)
                                                    if pb.text:
                                                        if nn.startswith("ARG"):
                                                            ex.args[nn] = pb.text.replace('[', ' ').replace(']', ' ')
                                                        else:
                                                            ex.args[nn] = ""
                                            elif pb.tag == "rel":
                                                ex.rel = pb.text
                        if inuse:
                            rs = predicateChild.attrib["id"].replace(".", "-").replace("_", "-")
                            self.rolesets.add(rs)
                            lemma.rolesets.append(roleset)
                            self.roleset_args[rs] = roleset_args

                #print("%s" % lemma)

    def getdoc(self, triples):
        doclist = []
        for s, p, o in triples:
            if p == ":instance":
                elems = o.rsplit("-", 1)
                if len(elems) > 1 and len(elems[1]) <= 3:
                    # take doc of concept-nn
                    if elems[0] in self.lemmas:
                        doclist.append("%s" % self.lemmas[elems[0]])
                elif len(elems) == 1:
                    # try other concepts if there is a verb
                    if elems[0] in self.lemmas:
                        doclist.append("%s" % self.lemmas[elems[0]])
        return sorted(doclist)

    def validate(self, triples):
        # check whether the AMR concept is a valid roleset in propbank  frames
        errors = []
        if not self.rolesets:
            # no data to check has been loaded
            return []
        for s, p, o in triples:
            if p == ":instance":
                elems = o.rsplit("-", 1)
                if len(elems) > 1 and (len(elems[1]) <= 3 and elems[1].isnumeric()):
                    if o not in self.rolesets:
                        errors.append("«%s» is not a defined propbank roleset" % o)

        # check whether ARG-relations uses are defined for the roleset
        # return ARG relations which ar note defined for the given concept
        instances = {} # var: concept

        for s, p, o in triples:
            if p == ":instance":
                instances[s] = o
            #if p not in self.relations:
            #    errors.append("invalid relation '%s'" % (p))

        for s, p, o in triples:
            if p != ":instance" and instances[s] in self.roleset_args:
                if p.startswith(":ARG"):
                    if p.endswith("-of"):
                        concept = instances[o]
                        p = p[:-3]
                    else:
                        concept = instances[s]

                    if concept not in self.roleset_args or p not in self.roleset_args[concept]:
                        errors.append("invalid argument «%s» for concept «%s»" % (p, concept))
        return errors


if __name__ == "__main__":
    pf = PropBankFrames("~/SemanticData/AMR/amr3/amr_annotation_3.0/data/frames/propbank-amr-frames-xml-2018-01-25/")
