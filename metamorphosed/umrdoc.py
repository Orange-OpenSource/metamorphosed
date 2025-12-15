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


# read and store an UMR file
import copy
import json
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

mydir = os.path.dirname(__file__)
VARNAME = re.compile(r"^s\d+[a-z]\d*$")


class UMRDocGraph:
    # read from a file in umrDOC.__init__()
    valid_dg_rels = None

    def __init__(self, dg, defaultsentid):
        lexer = shlex.shlex(dg.replace(":", " :"))
        lexer.wordchars += "-:"
        lexer.source = 'source'

        # to get all possibilities from existing UMR 2.0 files
        # sl = set()
        # pl = set()
        # ol = set()

        # for tok in lexer:
        #    print(tok)
        toklist = list(lexer)
        # print(dg, toklist)

        self.id = "s%ss0" % defaultsentid[3:]

        variables = set() # all variables
        resources = set() # all subjects and objects which are not a variable
        relations = set()
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
                        relations.add(toklist[ix + 1])
                        ix += 2
                ix += 1

            # S and P which are not variables
            fixed = set(["author", "author2", "author3", "author4", "author5",
                         "document-creation-time", "root",
                         "past-reference", "present-reference", "future-reference",
                         "purpose", "null-conceiver",
                         "have-condition-91", "have-condition",
                         "have-concession-91", "have-concessive-condition-91", "have-purpose-91",
                         ])

            for s, p, o in self.docgraph["coref"]:
                variables.add(s)
                variables.add(o)
                # pl.add((p, "c"))
            for s, p, o in self.docgraph["modal"]:
                # pl.add((p, "m"))
                if s not in fixed:
                    variables.add(s)
                else:
                    resources.add(s)
                    # sl.add((s, "m"))
                if o not in fixed:
                    variables.add(o)
                else:
                    resources.add(o)
                    # ol.add((o, "m"))

            for s, p, o in self.docgraph["temporal"]:
                # pl.add((p, "t"))
                if s not in fixed:
                    variables.add(s)
                else:
                    resources.add(s)
                    # sl.add((s, "t"))
                if o not in fixed:
                    variables.add(o)
                else:
                    resources.add(o)
                    # ol.add((o, "t"))

        # print(json.dumps(self.docgraph, indent=2))
        # print(sorted(variables))
        # for s in sl: print("S\t%s\t%s" % s)
        # for p in pl: print("P\t%s\t%s" % p)
        # for o in ol: print("O\t%s\t%s" % o)

    def getcopy(self):
        return copy.deepcopy(self.docgraph)

    def add(self, what, s, p, o, concepts):
        msg = self.checktriple(what, s, p, o, concepts)
        if len(msg):
            return msg

        if what not in self.docgraph:
            return "invalid document graph type %s" % what
        if (s, p, o) not in self.docgraph[what]:
            self.docgraph[what].append((s, p, o))
        else:
            return "%s triple exists already: %s, %s, %s" % (what, s, p, o)

        return None

    def delete(self, what, pos):
        if len(self.docgraph[what]) > pos:
            del self.docgraph[what][pos]

    def modify(self, what, pos, s, p, o, concepts):
        msg = self.checktriple(what, s, p, o, concepts)
        if len(msg):
            return msg
        if len(self.docgraph[what]) > pos:
            if pos == 0 and what == "modal":
                if (s, p, o) != ("root", ":modal", "author"):
                    msg = ["First :modal triple must be <tt>root :modal author</tt> and not <tt>%s %s %s</tt>" % self.docgraph["modal"][0]]
                    return msg
            #print("ATTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", what, pos, s,p,o, file=sys.stderr)
            del self.docgraph[what][pos]
            self.docgraph[what].insert(pos, (s, p, o))
        return None

    def checktriple(self, what, s, p, o, concepts=None):
        # check whether triples are conform do UMR specifications
        # TODO check whether o is a valid variable of corresponding sentence level graph
        msg = []
        if what == "coref":
            if not VARNAME.match(s):
                msg.append("Bad %s subject: <tt>%s</tt>.it must be a variable matching <tt>%s</tt>" % (what, s, VARNAME.pattern))
            if not VARNAME.match(o):
                msg.append("Bad %s object: <tt>%s</tt>. It must be a variable matching <tt>%s</tt>" % (what, o, VARNAME.pattern))
        else:
            if not VARNAME.match(s) and s not in UMRDocGraph.valid_dg_rels[what].get("subjects", []):
                msg.append("Bad %s subject: <tt>%s</tt>. It must be a variable matching <tt>%s</tt> or one of %s" % (what, s, VARNAME.pattern, UMRDocGraph.valid_dg_rels[what].get("subjects")))
            if not VARNAME.match(o) and o not in UMRDocGraph.valid_dg_rels[what].get("objects", []):
                msg.append("Bad %s object: <tt>%s</tt>. It must be a variable matching <tt>%s</tt> or one of %s" % (what, o, VARNAME.pattern, UMRDocGraph.valid_dg_rels[what].get("objects")))
        if p not in UMRDocGraph.valid_dg_rels[what].get("predicates", []):
            msg.append("Bad %s predicate: <tt>%s</tt>. It must be one of <tt>%s</tt>" % (what, p, " ".join(UMRDocGraph.valid_dg_rels[what].get("predicates"))))
        if concepts:
            if o not in concepts and o not in UMRDocGraph.valid_dg_rels[what].get("objects", []):
                msg.append("Bad %s object: %s is not a variable of Sentence level graph" % (what, o))
        return msg

    def validate(self, variables):
        msg = []
        if self.docgraph["modal"]:
            if self.docgraph["modal"][0] != ("root", ":modal", "author"):
                msg.append("First :modal triple must be <tt>root :modal author</tt> and not <tt>%s %s %s</tt>" % self.docgraph["modal"][0])

        if UMRDocGraph.valid_dg_rels is not None:
            for what in self.docgraph:
                for s, p, o in self.docgraph[what]:
                    msg.extend(self.checktriple(what, s, p, o, variables))
        return msg

    def write(self, ofp=sys.stdout):
        print("(%s / sentence" % self.id, end="", file=ofp)
        for k in self.docgraph:
            if self.docgraph[k]:
                print("\n   :%s (%s)" % (k, "\n        ".join(["(%s %s %s)" % tr for tr in self.docgraph[k]])), end="", file=ofp)
        print(")", file=ofp)


class UMRsentence(AMRsentence):
    def __init__(self, sentencegraph, alignements, documentgraph, sentid, meta, index, words, comments, other):
        AMRsentence.__init__(self, sentencegraph)
        self.alignments = alignements
        self.docgraph = UMRDocGraph(documentgraph, sentid)
        self.wiok = True # Index: and Words: lines are both not None and have the same length
        self.index = index
        self.words = words
        self.comments = comments
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

        self.other = other # other information like glosses and translations
        self.meta = meta
        if 8 in self.other:
            self.text = " ".join(other.get(8)[1]) # TODO use TOKENLINE
        if not self.text and self.words:
            if self.wiok:
                self.text = " ".join(self.words)
            #else:
            #    self.text = self.words.strip()
        if sentid:
            self.id = sentid
            self.varprefix = "s" + sentid.split("snt")[-1] # the sentence number is the required prefix
        self.pg = None # penman.Graph

    def getcopy(self):
        return copy.deepcopy(self.alignments)

    def getAlignments(self, alignments=None):
        # outputs the alignments in a way easy to display in index.js
        if alignments is None:
            alignments = self.alignments
        out = {} # word pos: [umrvar, ...]
        for umrvar in alignments:
            for index in alignments[umrvar]:
                start = index[0]
                end = index[1]
                for pos in range(start, end + 1, 1):
                    if pos not in out:
                        out[pos] = []
                    out[pos].append(umrvar)

        return out

    def write(self, ofp=sys.stdout, onlyheader=False):
        print("################################################################################", file=ofp)
        if self.meta:
            metainfo = [":: %s = %s" % (k, v) for k, v in self.meta.items()]
            print("# meta-info", " ".join(metainfo), file=ofp)
        else:
            print("# meta-info", file=ofp)
        print("# ::", self.id, file=ofp)
        for c in self.comments:
            print("#", c, file=ofp)
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
            if self.index:
                print("Index:", "\t".join([str(x) for x in self.index]), file=ofp)
            if self.words:
                print("Words:", "\t".join(self.words), file=ofp)
        for k in self.other:
            name = self.other[k][0]
            values = self.other[k][1]
            print("%s: %s" % (name, "\t".join(values)), file=ofp)
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
                msg.append("%s: alignment &lt;%s&gt; not in sentence level graph" % (self.id, k))
            if isinstance(self.index, list):
                for startend in self.alignments[k]:
                    if startend[0] > 0 and startend[0] not in self.index:
                        msg.append("%s: alignment &lt;%s&gt; start position not in Index: %s" % (self.id, startend[0], self.index))
                    if startend[1] > 0 and startend[1] not in self.index:
                        msg.append("%s: alignment &lt;%s&gt; end position not in Index: %s" % (self.id, startend[1], self.index))
        if not self.wiok:
            msg.append("Index: &lt;%s&gt; and Words: &lt;%s&gt; do not correspond" % (self.index, self.words))
        msg.extend(self.docgraph.validate(variables))
        return msg


ALIGNMENT = re.compile(r"^(-?\d+)-(-?\d+)$")

# needed to edit the lines starting with
TOKENLINES = {"Morphemes": 1,
              "Morphemes(English)": 2,
              "Part of Speech": 3,
              "Words(English)": 4,
              "Morpheme Gloss(English)": 5,
              "Morpheme Gloss(Spanish)": 6,
              "Morpheme Category": 7,
              "Sentence": 8,
              "Translation(English)": 9,
              "Translation(Spanish)": 10
              }

TOKLINESNUM = {}
for k, v in TOKENLINES.items():
    TOKLINESNUM[v] = k


class UMRdoc:
    def __init__(self, fn, verbose=True, rename_duplicate_ids=False, docgraphrel=mydir + "/data/docgraph.json"):
        self.rename_duplicate_ids = rename_duplicate_ids
        self.verbose = verbose
        self.sentences = []
        self.ids = {} # id: sentence
        self.fn = fn

        if docgraphrel:
            with open(docgraphrel) as ifp:
                UMRDocGraph.valid_dg_rels = json.load(ifp)

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
                    self.add(sentenceblock, alignments, documentblock, sentid, meta, index, words, comments, other)
                else:
                    if sentenceblock or documentblock or alignments or index or words or other:
                        print("* Missing '# ::sntN' line. Sentence ignored", sentid, linect, file=sys.stderr)
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
                comments = []
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
                    #other[elems[0]] = elems[1].split()
                    other[TOKENLINES[elems[0]]] = (elems[0], elems[1].split())

                elif line.startswith("# sentence level graph:"):
                    state = 1
                elif line.startswith("# alignment:"):
                    state = 2
                elif line.startswith("# document level annotation:"):
                    state = 3
                elif line.startswith("#######"):
                    state = None
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
            self.add(sentenceblock, alignments, documentblock, sentid, meta, index, words, comments, other)
        else:
            if sentenceblock or documentblock or alignments or index or words or other:
                print("* Missing '# ::sntN' line. Sentence ignored", sentid, linect, file=sys.stderr)

    def add(self, sentenceblock, alignments, documentblock, sentid, meta, index, words, comments, other):
        wiok = True # if index and words do not go together, we keep that what we find
        usent = UMRsentence("\n".join(sentenceblock), alignments, "\n".join(documentblock), sentid, meta, index, words, comments, other)

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

    def validate(self, validators, addids=False):
        msgs = []
        for sent in self.sentences:
            triples = sent.tsv()
            ee = sent.validate(triples) # validate from UMRSentence
            if ee:
                if addids:
                    for m in ee:
                        msgs.append((sent.id, m))
                else:
                    msgs += ee
            for v in validators:
                ee = v.validate(triples)
                if ee:
                    if addids:
                        for m in ee:
                            msgs.append((sent.id, m))
                    else:
                        msgs += ee
                #for e in ee:
                #    print("ZZZ", e)
            try:
                ddd = penman.parse(sent.amr.replace("\n", "")) # penman needs \n replaced to detect quote errors
            except Exception as e:
                if addids:
                    msgs.append(sent.id, str(e))
                else:
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
