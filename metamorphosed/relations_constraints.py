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


import re

import yaml

# Format
# subjects:
#   subject-class:
#      relation:
#         - object-class
#         - _regex
# predicates:
#   :location:
#      - city

# Example

# subjects:
#   name:
#     :op1:
#       - _".*"
# predicates:
#   :quant:
#       - _\d+
#       - _\d+\.\d+

# types and an argument to validate with isinstance()
fixedtypes = {
    "_string": str,
    "_int": int,
    "_float": float}


class Predicate:
    def __init__(self, p, objects):
        self.pred = p
        self.objects = []

        if objects:
            for o in objects:
                if o.startswith("_"):
                    self.objects.append(re.compile(o[1:]))
                else:
                    self.objects.append(o)

    def __str__(self, indent=""):
        res = ["%spred: <%s>" % (indent, self.pred)]
        for o in self.objects:
            res.append("%s  object: <%s>" % (indent, o))
        return "\n".join(res)

    def valid(self, o, oclass):
        #print("TEST PREDICATE %s %s/%s" % (self.pred, o, oclass))
        if not self.objects:
            # no constraint, no invalid object
            return True
        ok = False
        for valid_o in self.objects:
            if isinstance(valid_o, str):
                if valid_o == oclass:
                    ok = True
                    break
            else:
                mo = valid_o.match(o)
                if mo:
                    ok = True
                    break
        return ok


class Subject:
    def __init__(self, s, preds):
        self.subject = s
        self.predicates = {} # pred: Predicate
        self.predicates_regex = [] # [(pred compiled, Predicate)]
        for p in preds:
            if p.startswith("_"):
                P = Predicate(p, preds[p])
                self.predicates_regex.append((re.compile(p[1:]), P))
            else:
                P = Predicate(p, preds[p])
                self.predicates[p] = P

    def __str__(self):
        res = ["subject: <%s>" % self.subject]
        for p in self.predicates:
            res.append(self.predicates[p].__str__("  "))
        for (r, P) in self.predicates_regex:
            res.append(P.__str__("  "))
        return "\n".join(res)


EMPTY_SUBJECT = "_"


class Constraints:
    def __init__(self, fn):
        if fn:
            self.data = yaml.load(open(fn), Loader=yaml.Loader)
            subjects = self.data.get("subjects")
            preds = self.data.get("predicates")

            self.S = {} # s: Subject

            if subjects:
                for s in subjects:
                    S = Subject(s, subjects[s])
                    self.S[s] = S

            if preds:
                # predicates which are tested for any subject
                self.S[EMPTY_SUBJECT] = Subject(EMPTY_SUBJECT, preds)

        else:
            self.data = {}
            self.S = {} # s: Subject
            self.P = {} # p: Predicate

    def validate(self, triples, debug=False):
        errors = []
        classes = {} # inst: class
        for s, p, o in triples:
            # we must know of which class an instance instantiates
            if p == ":instance":
                classes[s] = o

        if debug:
            print("instances:")
            for i, c in classes.items():
                print("  ", i, c)

        #for k in self.S:
        #    print ("QQQ", k, self.S[k])
        for s, p, o in triples:
            if p != ":instance":
                if debug:
                    print("\ntriple", s, p, o)
                if p.endswith("-of"):
                    oclass = classes.get(s)
                    sclass = classes.get(o)
                else:
                    sclass = classes.get(s)
                    oclass = classes.get(o)

                if sclass in self.S:
                    if debug:
                        print("TEST SUBJECT %s/%s %s" % (s, sclass, p))
                    S = self.S[sclass]

                    if p not in S.predicates:
                        ok = False
                        for reobj, P in S.predicates_regex:
                            #print("AAA", reobj, P)
                            if reobj.match(p) and P.valid(o, oclass):
                                ok = True
                                break
                        if not ok:
                            errors.append("instance «%s» of «%s» has an invalid relation «%s»" % (s, sclass, p))
                        continue
                    if S.predicates[p] is not None:
                        P = S.predicates[p]
                        ok = P.valid(o, oclass)

                        if not ok:
                            errors.append("instance «%s» of «%s» with relation «%s» has invalid object «%s» of «%s»" % (s, sclass, p, o, oclass))
                            continue

                if EMPTY_SUBJECT in self.S:
                    empty = self.S[EMPTY_SUBJECT]
                    if p in empty.predicates:
                        P = empty.predicates[p]
                        ok = P.valid(o, oclass)
                        if not ok:
                            errors.append("relation «%s» has invalid object «%s» of «%s»" % (p, o, oclass))
                            continue

                    if empty.predicates_regex:
                        ok = True
                        for reobj, P in empty.predicates_regex:
                            #print("AAA", reobj, P)
                            if reobj.match(p) and not P.valid(o, oclass):
                                ok = False

                        if not ok:
                            errors.append("relation «%s» has invalid object «%s» of «%s»" % (p, o, oclass))

        return errors

    def show(self):
        print(self.data)
        print("subjects:")
        for s in self.S.values():
            print(s)

        print("\n")


if __name__ == "__main__":
    import readline
    import sys

    import penman
    cc = Constraints(sys.argv[1])
    cc.show()

    tr = [("z0",	":instance",	"bear-02"),
          ("z1",	":instance",	"person"),
          ("z2",	":instance",	"name"),
          ("z3",	":instance",	"city"),
          ("z4",	":instance",	"name"),
          ("z1",	":wiki",	'"Q156586"'),
          ("z4",	":op1",	'"London"'),
          #("z4",	":op1",	'London'),
          ("z3",	":wiki",	'"Q84"'),
          ("z0",	":ARG1",	"z1"),
          ("z1",	":name",	"z2"),
          ("z0",	":location",	"z3"),
          ("z3",	":name",	"z4"),
          ("z0",	":date",	"d"),
          ("d", ":instance", "date-entity"),
          ("d", ":month", '9'),
          ("d", ":day", '11'),
          ("d", ":year", '2010')]

    tr2 = [("d", ":instance", "date-entity"),
           ("d", ":month", '9'),
           ("d", ":day", '11'),
           ("d", ":year", '2010')]
    tr3 = [('e', ':instance', 'eat-01'),
           ('e', ':ARG0', 'ii'),
           ('ii', ':instance', 'i'),
           ('e', ':ARG1', 'a'),
           ('a', ':instance', 'and'),
           ('a', ':op1', 'h'),
           ('h', ':instance', 'ham'),
           ('a', ':op2', 'e2'),
           ('e2', ':instance', 'egg')]

    print(tr3)
    ee = cc.validate(tr3, True)
    for e in ee:
        print("***", e)

    while True:
        text = ""
        line = input(">>")
        if not line:
            break
        while line:
            text += " " + line.strip()
            line = input()
        text = text.strip()
        #print(text)
        parsedgraph = penman.decode(text)
        ee = cc.validate(parsedgraph.triples, True)
        print(parsedgraph.triples)
        for e in ee:
            print("***", e)
