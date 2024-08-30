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

# reify and un reify AMR graphs:
#  AMR without reification:        AMR with reification:
#  (l / leave-11                   (l / leave-11
#     :ARG0 (g / girl)                :ARG0 (g / girl)
#     :cause (a / arrive-01           :ARG1-of (c / cause-01
#               :ARG1 (b / boy)))                 :ARG0 (a / arrive-01
#                                                         :ARG1 (b / boy))))

import io
import os
import re
import sys

import penman


class Reification:
    def __init__(self, relation, reification, domain, range1):
        self.relation = relation
        self.reification = reification
        self.domain = domain
        self.range1 = range1

    def __str__(self):
        return "%s %s %s %s" % (self.relation, self.reification, self.domain, self.range1)

    def getdomain(self):
        return self.domain

    def getrange(self):
        return self.range1


class Reificator:
    def __init__(self, table):
        self.REIFY = {}
        self.UNREIFY = {}
        self.REIFICATIONS = []
        ifp = open(table)
        for line in ifp:
            line = line.strip()
            if not line or line[0] == "#":
                continue
            elems = line.split("\t")
            if len(elems) >= 4:
                self.REIFICATIONS.append(Reification(elems[0], elems[1], elems[2], elems[3]))
            else:
                print('Bad format in "%s": "%s"' % (table, line), file=sys.stderr)
        for r in self.REIFICATIONS:
            self.REIFY[r.relation] = r
            self.UNREIFY[r.reification] = r

        #for x in self.REIFY:
        #    print(x, self.REIFY[x])
        print("%d reifications loaded" % (len(self.REIFICATIONS)), file=sys.stderr)

        self.VARPREFIX = "zzz"

    def getquivalences(self):
        # for the UI
        e = []
        for r in self.REIFICATIONS:
            e.append("%s ↔ %s" % (r.relation, r.reification))
        return e

    def reify(self, pm, triples=None, only=None):
        if not triples:
            graph = penman.decode(pm)
            oldtriples = graph.triples
        else:
            oldtriples = triples
        newtriples = []
        ctnew = 0
        # fin existing zzN variables
        existing = []
        for s, p, o in oldtriples:
            if p == ":instance" and s is not None and s.startswith(self.VARPREFIX):
                existing.append(int(s[len(self.VARPREFIX):]))
        if existing:
            ctnew = sorted(existing)[-1] + 1
        for s, p, o in oldtriples:
            #print(s, p, o)
            if p in self.REIFY and (only is None or p in only):
                reification = self.REIFY[p]
                #print("RRR", reification)
                newtriples.append(("%s%d" % (self.VARPREFIX, ctnew), ":instance", reification.reification))
                newtriples.append(("%s%d" % (self.VARPREFIX, ctnew), reification.domain, s))
                newtriples.append(("%s%d" % (self.VARPREFIX, ctnew), reification.range1, o))
                ctnew += 1
            else:
                newtriples.append((s, p, o))

        if triples:
            return newtriples

        #print("NEW")
        #for tr in newtriples:
        #    print(tr)
        npm = penman.encode(penman.Graph(newtriples))
        return str(npm)

    def dereify(self, pm, #returntriples=False,
                only=None):
        # cannot work if the reified relations has other arguments than domain and range !!
        graph = penman.decode(pm)
        newtriples = []
        #ctnew = 0
        reif_instances = {} # var: reification-concept
        reif_args = {} # var: {ARG: var}
        errmsgs = []
        for s, p, o in graph.instances():
            #print(s, p, o)
            if p == ":instance":
                if o in self.UNREIFY and (only is None or o in only):
                    reif_instances[s] = o
        #print("AAA", reif_instances)
        for s, p, o in graph.triples:
            if s in reif_instances and p != ":instance":
                if p.startswith(":ARG"):
                    if s not in reif_args:
                        reif_args[s] = {}
                    reif_args[s][p] = o
                else:
                    print("information loss:", s, p, o, file=sys.stderr)
                    errmsgs.append("information loss: cannot attache edge « %s %s %s » after dereification. Please modify graph." % (s, p, o))

        for v in reif_args:
            if len(reif_args[v]) < 2:
                #print("missing argument", reif_args[v], file=sys.stderr)
                errmsgs.append("concept to derify does only have one :ARGn edge: %s" % " ".join(reif_args[v].keys()))
        for s, p, o in graph.triples:
            #print(s,p,o)
            if s not in reif_instances:
                newtriples.append((s, p, o))
            else:
                if p == ":instance":
                    reif = self.UNREIFY[o]
                    relation = reif.relation
                    news = reif_args[s].get(reif.getdomain())
                    newo = reif_args[s].get(reif.getrange())
                    print(s, reif.getdomain(), reif.getrange())
                    if news is None:
                        errmsgs.append("concept to dereify does not have %s edge." % reif.getdomain())
                    elif newo is None:
                        errmsgs.append("concept to dereify does not have %s edge." % reif.getrange())
                    else:
                        newtriples.append((news, relation, newo))

                    #print(relation)

        #if returntriples:
        #    return newtriples, errmsgs

        # crashes if additional args in deriefied concept!!!!
        if not errmsgs:
            npm = penman.encode(penman.Graph(newtriples))

            # print()
            # print(pm)
            # print(npm)
            return str(npm), errmsgs
        else:
            return None, errmsgs

    def compare(self, pm1, pm2):
        import smatch

        res = smatch.score_amr_pairs(io.StringIO(pm1),
                                     io.StringIO(pm2))
        prec, recall, f1 = list(res)[0]
        print("P: %.1f R: %.1f F: %.1f" % (prec, recall, f1))


def test(reificator, U, R, out=sys.stdout):
    repl = re.compile("\\s+")
    print("R orig", repl.sub(" ", R), file=out)
    r = reificator.reify(U)
    print("r  new", repl.sub(" ", r), file=out)
    #compare(r, R)
    #return

    print("U orig", repl.sub(" ", U), file=out)
    u, msg = reificator.dereify(R)
    print("u  new", repl.sub(" ", u), file=out)
    print("errors", msg, file=out)
    #compare(u, U)


moninst = None


def getInstance(reiftable=None):
    global moninst
    if not reiftable:
        # no file given. Either it was given earlier, than we have an instance
        # or no file is known, so we return moninst which is None
        return moninst

    if not moninst:
        print("loading", file=sys.stderr)
        moninst = Reificator(reiftable)
    else:
        print("already loaded", file=sys.stderr)
    return moninst


def runtest(table, out=sys.stdout):
    ur1 = """(l / leave-11
                :ARG0 (g / girl)
                :cause (a / arrive-01
                    :ARG1 (b / boy)))"""
    r1 = """(l / leave-11
               :ARG0 (g / girl)
               :ARG1-of (c / cause-01
                           :ARG0 (a / arrive-01
                                    :ARG1 (b / boy))))"""
    r1b = """(l / leave-11
               :ARG0 (g / girl)
               :ARG1-of (c / cause-01
                           :ARG0 (a / arrive-01
                                    :ARG1 (b / boy))
                           :toto ( a1 / anything :yyy 23)
                                    ))"""

    # not equivalent examples !
    ur2 = """(k / know-01
                :ARG0 (w / we)
                :ARG1 (k2 / knife
                    :location (d / drawer)))"""
    ur2b = """(k / know-01
                 :ARG0 (w / we)
                 :ARG1 (d / drawer
                     :location-of (k2 / knife)))"""
    r2 = """(k / know-01
                :ARG0 (w / we)
                :ARG1 (b / be-located-at-91
                  :ARG1 (k2 / knife)
                  :ARG2 (d / drawer)))"""

    ur3 = "(x / xconcept :location (y / yconcept))"
    r3 = "(x /xconcept :ARG1-of (b / be-located-at-91 :ARG2 (y / yconcept)))"

    ur4 = """(d / die-01
              :ARG1 (s / soldier
                     :quantQ 9
                     :subset-of (s3 / soldier
                           :quantQ 20)))"""
    r4 = """(drr / die-01
              :ARG1 (s / soldier
                    :quantQ 9
                    :ARG1-of (i / include-91
                               :ARG2 (s3 / soldier
                                  :quantQ 20))))"""

    #r = reify(ur2b)
    #print(r)

    reificator = getInstance(table)
    test(reificator, ur1, r1, out=out)
    #test(reificator, ur3, r3)
    #test(reificator, ur4, r4)


if __name__ == "__main__":
    import argparse
    mydir = os.path.dirname(__file__)
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default=False, action="store_true", help="log server on screen")
    parser.add_argument("--infile", "-i", default=None, help="file to refify")
    parser.add_argument("--table", "-t", default=mydir + "/reification-table.txt", help="file with reification table")

    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()
        if args.test:
            runtest(args.table)
        elif args.infile:
            import amrdoc
            doc = amrdoc.AMRdoc(args.infile)
            reificator = getInstance(args.table)
            print("# cwd:", os.getcwd())
            print("# generated by:", " ".join(sys.argv))
            for sent in doc.sentences:
                amr2 = reificator.reify(sent.amr)
                sent.write(sys.stdout, onlyheader=True)
                #print("==", sent.amr == amr2)
                #print(sent.amr)
                print(amr2)
                print()
