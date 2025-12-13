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

# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke


# read and store an AMR file
import os
import re
import sys

import penman

# silence penman
import logging
logging.getLogger('penman').setLevel(logging.ERROR)

from metamorphosed.exception import ServerException
#from exception import ServerException

ONESPACE = re.compile("[ \n\t]+")


class AMRsentence:
    def __init__(self, penmanstr):
        self.amr = penmanstr
        self.text = None # ::snt
        self.id = None # ::id
        self.idrest = None
        self.savedateorig = ""
        self.date = None
        self.savedaterest = ""
        self.tokens = None # ::tok
        self.comments = []

    def modcomment(self, comments):
        self.comments.clear()
        for c in comments.split("\n"):
            c = c.strip()
            if c:
                self.comments.append(c)

    def write(self, ofp=sys.stdout, onlyheader=False):
        if self.id:
            if self.idrest:
                print("# ::id %s ::%s" % (self.id, "::".join(self.idrest)), file=ofp)
            else:
                print("# ::id %s" % self.id, file=ofp)
        if self.text:
            print("# ::snt %s" % self.text, file=ofp)

        if self.date:
            if self.savedaterest:
                print("# ::save-date %s %s" % (self.date, self.savedaterest), file=ofp)
            else:
                print("# ::save-date %s" % (self.date), file=ofp)
        elif self.savedateorig:
            print("# ::save-date %s" % self.savedateorig, file=ofp)
        if self.tokens:
            print("# ::tok", " ".join(self.tokens))

        for c in self.comments:
            print("#", c, file=ofp)
        if not onlyheader:
            print(self.amr.strip(), file=ofp)
            print(file=ofp)

    def tsv(self, #meta=False, ofp=sys.stdout
            ):
        #if meta:
        #    if self.id:
        #        print("# ::id %s" % self.id, file=ofp)
        #    if self.text:
        #        print("# ::snt %s" % self.text, file=ofp)
        try:
            g = penman.decode(self.amr)
            # for s,p,o in g.triples:
            #     print("%s\t%s\t%s" % (s,p,o))
            return g.triples
        except Exception as e:
            print("ERROR: %s" % e, file=sys.stderr)
            return []

#    def oneline(self, meta=False, ofp=sys.stdout):
#        if meta:
#            if self.id:
#                if self.idrest:
#                    print("# ::id %s ::%s" % (self.id, " ::".join(self.idrest)), file=ofp)
#                else:
#                    print("# ::id %s" % self.id, file=ofp)
#            if self.text:
#                print("# ::snt %s" % self.text, file=ofp)
#            for c in self.comments:
#                print("#", c, file=ofp)
#
#        res = ONESPACE.sub(" ", self.amr)
#        print(res)

    def getconceptlist(self):
        variables = {} # var concept
        try:
            g = penman.decode(self.amr)
            for s, p, o in g.instances():
                variables[s] = o
        except Exception as e:
            print("ERROR in getting instances", e, __file__)
            pass
        return variables

    def getwikilink(self, inst):
        # get a wiki link for instance inst if existing
        try:
            g = penman.decode(self.amr)
            #print("aaa", inst)
            for s, p, o in g.attributes():
                #print("bbb", s, p, o)
                if s == inst and p == ":wiki":
                    return o.replace('"', '')
        except Exception as e:
            print("ERROR in getting wiki link", e, __file__)

        return None

    def findtext(self, regex):
        if self.text:
            #rtc = re.search(regex, self.text, re.IGNORECASE)
            try:
                rtc = re.finditer(regex, self.text, re.IGNORECASE)
                if rtc:
                    return rtc
            except Exception as e:
                raise ServerException('bad regular expression "%s": %s' % (regex, e))

        return [] #False

    def findcomment(self, regex):
        if self.comments:
            try:
                for c in self.comments:
                    rtc = list(re.finditer(regex, c, re.IGNORECASE))
                    if rtc:
                        return rtc
            except Exception as e:
                raise ServerException('bad regular expression "%s": %s' % (regex, e))

        return [] #False

    def findid(self, regex):
        if self.id:
            try:
                rtc = re.search(regex, self.id, re.IGNORECASE)
                if rtc:
                    return True
            except Exception as e:
                raise ServerException('bad regular expression "%s": %s' % (regex, e))

        return False

#    def findamr(self, regex):
#        if self.amr:
#            #rtc = re.search(regex, self.amr) #, re.IGNORECASE)
#            rtc = re.finditer(regex, self.amr) #, re.IGNORECASE)
#            if rtc:
#                #print(rtc)
#                return rtc
#        return False


class AMRdoc:
    def __init__(self, fn, verbose=True, rename_duplicate_ids=False):
        self.sentences = []
        self.ids = {} # id: sentence
        self.fn = fn

        if isinstance(fn, str):
            ifp = open(fn)
        else:
            # here fn is a opened file or sys.stdin etc
            ifp = fn

        amrblock = []
        sentid = None
        idrest = None # after the id in the ::id line
        text = None
        tokens = None
        savedateorig = None
        date = None
        savedaterest = ""
        savedateRE = re.compile(r"# ::save-date (\w+) (\w+) (\d+), (\d+) (.*)")
        comments = []
        duplicated = {} # id: number
        for line in ifp:
            line = line.rstrip()
            #print("LL <%s>" % line)
            if not line:
                if amrblock:
                    asent = AMRsentence("\n".join(amrblock))
                    asent.id = sentid
                    asent.idrest = idrest
                    asent.text = text
                    asent.tokens = tokens
                    asent.savedateorig = savedateorig
                    asent.date = date
                    asent.savedaterest = savedaterest
                    asent.comments = comments
                    sentid = None
                    idrest = None
                    text = None
                    tokens = None
                    savedateorig = None
                    date = None
                    savedaterest = ""

                    amrblock = []
                    comments = []
                    self.sentences.append(asent)
                    newid = asent.id # we do not want to overwrite an ID, event if it's a duplicate
                    if asent.id is not None and asent.id in self.ids:
                        if asent.id not in duplicated:
                            duplicated[asent.id] = 1
                        else:
                            duplicated[asent.id] += 1
                        if verbose:
                            print("*** duplicate sentence id <%s> renamed to <%s-%d>" % (asent.id, asent.id, duplicated[asent.id]), file=sys.stderr)
                        #print("     ", asent.comments, file=sys.stderr)
                        newid = "%s-%d" % (asent.id, duplicated[asent.id])

                        if rename_duplicate_ids:
                            asent.id = "%s-%d" % (asent.id, duplicated[asent.id])

                    self.ids[newid] = asent
            elif line.startswith("# ::id "):
                elems = line[7:].split("::")
                #sentid = line[7:]
                sentid = elems[0].strip()
                if len(elems) > 1:
                    idrest = elems[1:]
                #print("AAAA", sentid, idrest)
            elif line.startswith("# ::wikidata "):
                if not sentid:
                    sentid = line[13:]
            elif line.startswith("# ::snt "):
                text = line[8:]
            elif line.startswith("# ::tok "):
                tokens = line[8:].split()
            elif line.startswith("# ::save-date "):
                # parse save-date line to avoid deleting other information
                mo = savedateRE.match(line)
                if mo:
                    date = "%s %s %s, %s" % (mo.group(1), mo.group(2), mo.group(3), mo.group(4))
                    savedaterest = mo.group(5)
                savedateorig = line[14:]
            elif line.startswith("#"):
                comments.append(line[1:].strip())
            else:
                amrblock.append(line)

        if amrblock:
            # we pass here only if there is no final empty line in the amr file
            asent = AMRsentence("\n".join(amrblock))
            asent.id = sentid
            asent.text = text
            asent.tokens = tokens
            asent.comments = comments
            self.sentences.append(asent)
            self.ids[sentid] = asent
        if verbose:
            fnn = fn
            if not isinstance(fn, str):
                fnn = fn.name
            print("%d sentences read from %s" % (len(self.sentences), fnn), file=sys.stderr)

    def tsv(self):
        # output all AMR graphs as triple list
        return [sent.tsv() for sent in self.sentences]

#    def oneline(self):
#        # out put all AMR graphs in PENMAN on a single line
#        for sent in self.sentences:
#            sent.oneline()

#    def stats(self):
#        # out put all AMR graphs in PENMAN on a single line
#        for sent in self.sentences:
#            sent.oneline()

    def validate(self, validators, addids=False):
        msgs = []
        for sent in self.sentences:
            for v in validators:
                ee = v.validate(sent.tsv())
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
                #print("eee",ddd)
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


#    def writedoc(self, ofp):
#        for i, sent in enumerate(self.sentences):
#            if i+1 in self.aps:
#                if self.aps[i+1].modified:
#                    modified.append(str(i+1))
#                    sent.date = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
#                sent.write(ofp, onlyheader=True)
#                #print("SENT", i+1, self.aps[i+1].modified, sent.id, sent.text, self.aps[i+1].triples)
#                self.aps[i+1].write(ofp)
#            else:
#                sent.write(ofp)


# output concepts and frequency of relations to other concepts/literals
def relations_between_concepts(ads, depth=2):
    output = []
    concepts = {} # {concept: {relation: {concept: freq}}}
    for ad in ads:
        for sent in ad.sentences:
            instances = {} # inst: concept
            for s, p, o in sent.tsv():
                if p == ":instance":
                    instances[s] = o
            for s, p, o in sent.tsv():
                if p != ":instance":
                    sclass = instances[s]
                    oclass = instances.get(o, "lit:" + o)

                    if depth == 1:
                        if sclass in concepts:
                            concepts[sclass] += 1
                        else:
                            concepts[sclass] = 1
                        continue

                    if sclass in concepts:
                        relations = concepts[sclass]
                    else:
                        relations = {}
                        concepts[sclass] = relations

                    if depth == 2:
                        if p in relations:
                            relations[p] += 1
                        else:
                            relations[p] = 1
                        continue

                    if p in relations:
                        objectconcepts = relations[p]
                    else:
                        objectconcepts = {}
                        relations[p] = objectconcepts
                    if oclass in objectconcepts:
                        objectconcepts[oclass] += 1
                    else:
                        objectconcepts[oclass] = 1
    for c in sorted(concepts):
        if depth == 1:
            #print(c, concepts[c], sep="\t")
            output.append("%s\t%s" % (c, concepts[c]))
            continue
        #print(c)
        output.append(c)
        for r in sorted(concepts[c]):
            if depth == 2:
                #print("   %s\t%s" % (r, concepts[c][r]))
                output.append("   %s\t%s" % (r, concepts[c][r]))
                continue
            #print("   ", r)
            output.append("   " + r)
            for oc in sorted(concepts[c][r]):
                #print("     %s\t%s" % (oc, concepts[c][r][oc]))
                output.append("     %s\t%s" % (oc, concepts[c][r][oc]))

    return output


def stats(ads, conceptlist, plotting=True, outdir="."):
    triples = []
    sentences = 0
    for ad in ads:
        sentences += len(ad.sentences)
        for sent in ad.sentences:
            triples += sent.tsv()
        #print("DDD", triples)
    relations = {} # rel: freq
    concepts = {} # cpt: freq
    for s, p, o in triples:
        if s is None or o is None:
            continue
        if p == ":instance":
            if o in concepts:
                concepts[o] += 1
            else:
                concepts[o] = 1
        elif p == ":wiki":
            continue
        elif p.startswith(":snt") or p.startswith(":op"):
            continue
        else:
            if p in relations:
                relations[p] += 1
            else:
                relations[p] = 1
    print("# sentences:", sentences)

    def mean_med(dico):
        mean = sum(dico.values()) / len(dico)
        v = sorted(list(dico.values()))
        #if len(dico) % 2 == 0:
        med = v[int(len(dico) / 2)]
        #return mean,med
        return "mean: %.2f median: %d" % (mean, med), mean, med

    #relations= {"a": 1,"b": 2,"c": 10,"d": 7,"e": 30 }
    meanmed, meanr, medr = mean_med(relations)
    print("# relations: %d %s" % (len(relations), meanmed))
    #for k,v in sorted(relations.items(), key=lambda x: x[1]):
    #    print(k,v)

    mverbs = re.compile("-[0-9][0-9]$")
    meanmed, mean, med = mean_med(concepts)
    #for k,v in concepts.items():
    #    print(k,v)
    print("# concepts:", len(concepts), meanmed)
    # ctverbs = 0
    verbs = {} # concept: freq
    others = {}
    for c in concepts:
        if mverbs.search(c):
            verbs[c] = concepts[c]
        else:
            others[c] = concepts[c]
    meanmed, meanv, medv = mean_med(verbs)
    print("  # verbs: ", len(verbs), meanmed)
    #for k,v in sorted(verbs.items(), key=lambda x: x[1]):
    #    print(k,v)

    meanmed, meano, medo = mean_med(others)
    print("  # others:", len(others), meanmed)
    #for k,v in sorted(others.items(), key=lambda x: x[1]):
    #    print(k,v)

    if conceptlist:
        for c in verbs:
            print("%s\t%d" % (c, verbs[c]))
        for c in others:
            print("%s\t%d" % (c, others[c]))
        return

    ofp = open(os.path.join(outdir, "verbalconcepts-list.txt"), "w")
    for c in verbs:
        print("%s\t%d" % (c, verbs[c]), file=ofp)
    ofp.close()
    ofp = open(os.path.join(outdir, "nonverbalconcepts-list.txt"), "w")
    for c in others:
        print("%s\t%d" % (c, others[c]), file=ofp)
    ofp.close()
    ofp = open(os.path.join(outdir, "relations-list.txt"), "w")
    for c in relations:
        print("%s\t%d" % (c, relations[c]), file=ofp)
    ofp.close()

    if plotting:
        print("plotting graph...")
        import matplotlib.pyplot as plt

        def graph(dico, fn, mean, med, logscale=True):
            # print(sorted(dico.values()))
            plt.rcParams["font.family"] = "Lato"
            plt.rcParams["figure.figsize"] = [6.4, 2] # default 6.4, 4.8
            plt.bar(range(len(dico)), sorted(dico.values(), reverse=True),
                    color="#ff7900")
            plt.ylabel("frequency")

            # plt.hist(sorted(dico.values(), reverse=True), bins=100, density=True)
            if logscale:
                plt.yscale('log')

            plt.axhline(mean, color='#50be87', linestyle='--', label="mean")
            plt.axhline(med, color='#9164cd', linestyle='--', label="median")
            plt.legend()
            #plt.gca().axes.get_xaxis().set_visible(False)
            #plt.show()
            plt.savefig(fn, format="pdf", bbox_inches='tight')
            plt.clf()

        graph(relations, "rels.pdf", meanr, medr)
        graph(verbs, "verbalconcepts.pdf", meanv, medv)
        graph(others, "nonverbalconcepts.pdf", meano, medo)


def main():
    import argparse

    parser = argparse.ArgumentParser("AMRdoc validation")

    parser.add_argument("--file", "-f", required=True, nargs="+", help="AMR file to read")
    parser.add_argument("--rels", "-R", default=None, help="list of valid AMR-relations (simple text file)")
    parser.add_argument("--pbframes", "-P", default=None, help="Propbank frameset documentation (directory with xml files)")
    parser.add_argument("--constraints", "-C", default=None, help="constraints for subjects and predicates (yaml file)")
    parser.add_argument("--stats", "-s", default=False, action="store_true", help='calculate stats and create graphs')
    parser.add_argument("--conceptlist", default=False, action="store_true", help="calculate stats and output only a list of concepts")
    parser.add_argument("--concepts", "-c", default=0, type=int, help='show links between concepts (1, 2, 3)')
    parser.add_argument("--validate", "-v", default=False, action="store_true", help='validate sentences (needs at least one of --rels, --pbframes, --constraints)')

    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()

        validators = []

        if args.validate:
            import AMR_relations
            import propbank_frames
            import relations_constraints

            if args.rels:
                validators.append(AMR_relations.Relations(args.rels))
            if args.pbframes:
                validators.append(propbank_frames.PropBankFrames(args.pbframes))
            if args.constraints:
                validators.append(relations_constraints.Constraints(args.constraints))

            #print(validators)
        ads = []

        for fn in args.file:
            ad = AMRdoc(fn)
            msg = ad.validate(validators)
            for m in msg:
                print("Problem:", m)

            ads.append(ad)
            #ad.tsv()
            #ad.oneline()
        if args.stats:
            stats(ads, args.conceptlist)
        if args.concepts > 0:
            for x in relations_between_concepts(ads, depth=args.concepts):
                print(x)


if __name__ == "__main__":
    main()
