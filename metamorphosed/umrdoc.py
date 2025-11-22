#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2025,  Orange
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

# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke


# read and store an AMR file
import os
import re
import shlex
import sys

import penman

# silence penman
import logging
logging.getLogger('penman').setLevel(logging.ERROR)

from metamorphosed.exception import ServerException
from metamorphosed.amrdoc import AMRsentence


class UMRDocGraph:
    def __init__(self, dg):
        lexer = shlex.shlex(dg.replace(":", " :"))
        lexer.wordchars += "-:"
        lexer.source = 'source'

        # for tok in lexer:
        #    print(tok)
        toklist = list(lexer)
        #print(dg, toklist)

        self.variables = set() # all variables
        self.resources = set() # all subjects and objects which are not a variable
        self.relations = set()
        self.docgraph = {"temporal": [],
                         "modal": [],
                         "coref": []}
        if len(toklist) > 0:
            self.id = toklist[1]
            state = None
            indent = 0
            ix = 3
            while ix < len(toklist) - 4:
                tok = toklist[ix]
                if tok in [":temporal", ":modal", ":coref"]:
                    state = tok
                elif state:
                    if tok == "(":
                        indent += 1
                    elif tok == ")":
                        indent -= 1
                    elif indent == 0:
                        state = None
                    elif indent == 2:
                        self.docgraph[state[1:]].append((tok, toklist[ix + 1], toklist[ix + 2]))
                        self.relations.add(toklist[ix + 1])
                        ix += 2
                ix += 1

            fixed = set(["author", "author2", "author3", "author4", "author5",
                         "document-creation-time", "root",
                         "past-reference", "present-reference", "future-reference",
                         "purpose", "null-conceiver",
                         "have-condition-91", "have-condition",
                         "have-concession-91", "have-concessive-condition-91", "have-purpose-91",
                         ])

            for s, p, o in self.docgraph["coref"]:
                self.variables.add(s)
                self.variables.add(o)
            for s, p, o in self.docgraph["modal"]:
                if s not in fixed:
                    self.variables.add(s)
                else:
                    self.resources.add(s)
                if o not in fixed:
                    self.variables.add(o)
                else:
                    self.resources.add(o)

            for s, p, o in self.docgraph["temporal"]:
                if s not in fixed:
                    self.variables.add(s)
                else:
                    self.resources.add(s)
                if o not in fixed:
                    self.variables.add(o)
                else:
                    self.resources.add(o)

        #print(json.dumps(self.docgraph, indent=2))
        #print(sorted(self.variables))

    def write(self, ofp=sys.stdout):
        print("(%s / sentence" % self.id, end="", file=ofp)
        for k in self.docgraph:
            if self.docgraph[k]:
                print("\n   :%s (%s)" % (k, "\n        ".join(["(%s %s %s)" % tr for tr in self.docgraph[k]])), end="", file=ofp)
        print(")", file=ofp)


class UMRsentence(AMRsentence):
    def __init__(self, sentencegraph, alignements, documentgraph, sentid, meta, index, words, other):
        AMRsentence.__init__(self, sentencegraph)
        self.alignments = alignements
        self.docgraph = UMRDocGraph(documentgraph)
        self.wiok = True # Index: and Words: lines are both not None and have the same length
        self.index = index
        self.words = words
        self.varprefix = None

        if index is None:
            print("* missing 'Index' line", sentid, file=sys.stderr)
            self.wiok = False
        else:
            self.index = [int(x) for x in index.split()]

        if words is None:
            print("* missing 'Words' line", sentid, file=sys.stderr)
            self.wiok = False
        else:
            self.words = words.split()

        if self.wiok:
            # we found both index and words
            #il = index.split()
            #wl = words.split()
            if index and words and len(self.index) != len(self.words):
                # but they do not have the same length
                print("* Words do not correspond do Index", sentid, words, index, file=sys.stderr)
                self.wiok = False
                #self.index = index
                #self.words = words
            #else:
            #    self.index = [int(x) for x in il]
            #    self.words = wl

        self.other = other
        self.meta = meta
        self.text = other.get("Sentence")
        if not self.text and self.words:
            if self.wiok:
                self.text = " ".join(self.words)
            #else:
            #    self.text = self.words.strip()
        if sentid:
            self.id = sentid
            self.varprefix = "s" + sentid.split("snt")[-1] # the sentence number is the required prefix
        self.pg = None # penman.Graph

    def write(self, ofp=sys.stdout, onlyheader=False):
        print("################################################################################", file=ofp)
        if self.meta:
            metainfo = [":: %s = %s" % (k, v) for k, v in self.meta.items()]
            print("# meta-info", " ".join(metainfo), file=ofp)
        else:
            print("# meta-info", file=ofp)
        print("# ::", self.id, file=ofp)
        istr = []
        wstr = []

        if self.wiok:
            for ix in range(len(self.index)):
                ilen = len(str(self.index[ix]))
                wlen = len(str(self.words[ix]))
                maxlen = max(ilen, wlen)
                istr.append(f"{str(self.index[ix]):{maxlen}}")
                wstr.append(f"{self.words[ix]:{maxlen}}")
            print("Index:", " ".join(istr), file=ofp)
            print("Words:", " ".join(wstr), file=ofp)
        else:
            print("Index:", self.index, file=ofp)
            print("Words:", self.words, file=ofp)
        for k in self.other:
            print("%s:%s" % (k, self.other[k]), file=ofp)
        print(file=ofp)
        print("# sentence level graph:", file=ofp)
        print(self.amr, file=ofp)
        #print("\n", file=ofp)
        print("# alignment:", file=ofp)
        for k, vv in self.alignments.items():
            print("%s: " % k, end="", file=ofp)
            print(", ".join(["%d-%d" % (x[0], x[1]) for x in vv]), file=ofp)
        print("\n", file=ofp)
        print("# document level annotation:", file=ofp)
        self.docgraph.write(ofp=ofp)
        print("\n\n", file=ofp)

    def validate(self, triples):
        msg = []
        # check what can be checked without resources
        # variables in alignment must be in graph
        variables = set()
        for s, p, o in triples:
            if p == ":instance":
                variables.add(s)
                if self.varprefix:
                    if not s.startswith(self.varprefix):
                        msg.append("%s: variable &lt;%s&gt; does not start with %s" % (self.id, s, self.varprefix))
                else:
                    msg.append("%s: no sentence number" % (self.id))
        for k in self.alignments:
            if k not in variables:
                msg.append("%s: alignment <%s> not in sentence level graph" % (self.id, k))
            if isinstance(self.index, list):
                for startend in self.alignments[k]:
                    if startend[0] > 0 and startend[0] not in self.index:
                        msg.append("%s: alignment <%s> start position not in Index: %s" % (self.id, startend[0], self.index))
                    if startend[1] > 0 and startend[1] not in self.index:
                        msg.append("%s: alignment <%s> end position not in Index: %s" % (self.id, startend[1], self.index))
        if not self.wiok:
            msg.append("Index: &lt;%s&gt; and Words: &lt;%s&gt; do not correspond" % (self.index, self.words))
        return msg


ALIGNMENT = re.compile(r"^(-?\d+)-(-?\d+)$")


class UMRdoc:
    def __init__(self, fn, verbose=True, rename_duplicate_ids=False):
        self.rename_duplicate_ids = rename_duplicate_ids
        self.verbose = verbose
        self.sentences = []
        self.ids = {} # id: sentence
        self.fn = fn

        if isinstance(fn, str):
            ifp = open(fn)
        else:
            # here fn is a opened file or sys.stdin etc
            ifp = fn

        sentid = None
        meta = {}
        comments = []
        self.duplicated = {} # id: number
        index = None
        words = None
        other = {}
        sentenceblock = []
        documentblock = []
        alignments = {} # var: [(from, to), ...]
        state = 0 # 1: after "# sentence level graph", 2: after "# alignment", 3: after "# document level"
        for linect, line in enumerate(ifp, 1):
            line = line.rstrip()
            if not line:
                continue
            elif line.startswith("# meta-info"):
                if sentid:
                    # save preceding sentence
                    self.add(sentenceblock, alignments, documentblock, sentid, meta, index, words, other)

                # start next sentence
                meta = {}
                if ("::") in line:
                    for keyval in line.split("::")[1:]:
                        fields = keyval.split("=")
                        meta[fields[0].strip()] = fields[1].strip()

                state = 0
                sentid = None
                sentenceblock = []
                alignments = {}
                documentblock = []
                index = None
                words = None
                other = {} # Morphme;s POS, Translations etc
            else:
                if line.startswith("# :: "):
                    sentid = line[5:]
                elif line.startswith("Index: "):
                    if index:
                        print("* duplicate 'Index' line", sentid, linect, file=sys.stderr)
                    #index = line.split(":", 1)[1].split()
                    index = line.split(":", 1)[1]
                elif line.startswith("Words: "):
                    if words:
                        print("* duplicate 'Words' line", sentid, linect, file=sys.stderr)
                    #words = line.split(":", 1)[1].split()
                    words = line.split(":", 1)[1]
                elif line.startswith("Morphemes:") \
                        or line.startswith("Morphemes(English):") \
                        or line.startswith("Part of Speech:") \
                        or line.startswith("Words(English):") \
                        or line.startswith("Morpheme Gloss(English):") \
                        or line.startswith("Morpheme Gloss(Spanish):") \
                        or line.startswith("Morpheme Category:") \
                        or line.startswith("Sentence:") \
                        or line.startswith("Translation(English):") \
                        or line.startswith("Translation(Spanish):"):
                    elems = line.split(":", 1)
                    other[elems[0]] = elems[1]

                elif line.startswith("# sentence level graph:"):
                    state = 1
                elif line.startswith("# alignment:"):
                    state = 2
                elif line.startswith("# document level annotation:"):
                    state = 3
                elif line.startswith("#"):
                    comments.append(line[1:])
                elif state == 0:
                    print("* unexpected line", sentid, linect, line, file=sys.stderr)
                elif state == 1:
                    sentenceblock.append(line)
                elif state == 2:
                    elems = line.strip().split(":")
                    if len(elems) != 2:
                        print("* bad alignment", sentid, linect, line, file=sys.stderr)
                    alignments[elems[0]] = []
                    for e in elems[1].strip().split(","):
                        mo = ALIGNMENT.match(e.strip())
                        #print(line, mo)
                        alignments[elems[0]].append((int(mo.group(1)), int(mo.group(2))))
                elif state == 3:
                    documentblock.append(line)
        if sentid:
            self.add(sentenceblock, alignments, documentblock, sentid, meta, index, words, other)

    def add(self, sentenceblock, alignments, documentblock, sentid, meta, index, words, other):
        wiok = True # if index and words do not go together, we keep that what we find
        usent = UMRsentence("\n".join(sentenceblock), alignments, "\n".join(documentblock), sentid, meta, index, words, other)

        self.sentences.append(usent)
        newid = usent.id # we do not want to overwrite an ID, event if it's a duplicate
        if usent.id is not None and usent.id in self.ids:
            if usent.id not in self.duplicated:
                self.duplicated[usent.id] = 1
            else:
                self.duplicated[usent.id] += 1
            if self.verbose:
                print("*** duplicate sentence id <%s> renamed to <%s-%d>" % (usent.id, usent.id, self.duplicated[usent.id]), file=sys.stderr)
                #print("     ", asent.comments, file=sys.stderr)
            newid = "%s-%d" % (usent.id, self.duplicated[usent.id])

            if self.rename_duplicate_ids:
                usent.id = "%s-%d" % (usent.id, self.duplicated[usent.id])
        self.ids[newid] = usent

    def validate(self, validators):
        msgs = []
        for sent in self.sentences:
            triples = sent.tsv()
            ee = sent.validate(triples) # validate from UMRSentence
            if ee:
                msgs += ee
            for v in validators:
                ee = v.validate(triples)
                if ee:
                    msgs += ee
                #for e in ee:
                #    print("ZZZ", e)
            try:
                ddd = penman.parse(sent.amr.replace("\n", "")) # penman needs \n replaced to detect quote errors
            except Exception as e:
                msgs.append(str(e))
        return msgs

    def getsentencelist(self):
        sents = []
        for sent in self.sentences:
            sents.append((sent.id, sent.text))
        return sents


def main():
    import argparse

    parser = argparse.ArgumentParser("UMRdoc validation")

    parser.add_argument("--file", "-f", required=True, nargs="+", help="AMR file to read")
    parser.add_argument("--rels", "-R", default=None, help="list of valid AMR-relations (simple text file)")
    #parser.add_argument("--pbframes", "-P", default=None, help="Propbank frameset documentation (directory with xml files)")
    parser.add_argument("--constraints", "-C", default=None, help="constraints for subjects and predicates (yaml file)")
    parser.add_argument("--stats", "-s", default=False, action="store_true", help='calculate stats and create graphs')
    #parser.add_argument("--conceptlist", default=False, action="store_true", help="calculate stats and output only a list of concepts")
    #parser.add_argument("--concepts", "-c", default=0, type=int, help='show links between concepts (1, 2, 3)')
    parser.add_argument("--validate", "-v", default=False, action="store_true", help='validate sentences (needs at least one of --rels, --pbframes, --constraints)')

    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()

        validators = []

        if args.validate:
            import AMR_relations
            #import propbank_frames
            import relations_constraints

            if args.rels:
                validators.append(AMR_relations.Relations(args.rels))
            #if args.pbframes:
            #    validators.append(propbank_frames.PropBankFrames(args.pbframes))
            if args.constraints:
                validators.append(relations_constraints.Constraints(args.constraints))

            #print(validators)
        ads = []

        for fn in args.file:
            ad = UMRdoc(fn)
            #for sent in ad.sentences:
            #    sent.write()
            if args.validate:
                msg = ad.validate(validators)
                for m in msg:
                    print("Problem:", m)

            ads.append(ad)
            #ad.tsv()
            #ad.oneline()
        #if args.stats:
        #    stats(ads, args.conceptlist)
        #if args.concepts > 0:
        #    for x in relations_between_concepts(ads, depth=args.concepts):
        #        print(x)


if __name__ == "__main__":
    main()
