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


# calculates the inter-annotator agreement using smatch
# files must have the same number of sentences

# macro
# for all sentences
#   get average of smatch of all couples of annotators
# average of average smatch scores for all sentences

# micro
# for all annotator couples
#    get smatch of all sentences, and get average
# average of average scores of all annotator couples

# option: using number of differences between two graphs instead of smatch

import sys

import metamorphosed.amrdoc as amrdoc
import metamorphosed.amr_comparison as amr_comparison


class IAA:
    def __init__(self, files, debug=True, first=0, last=0):
        self.docs = []
        self.numfiles = len(files)
        self.debug = debug
        self.last = last
        self.first = first
        for fn in files:
            doc = amrdoc.AMRdoc(fn)
            self.docs.append(doc)
        for d in self.docs[1:]:
            if len(d.sentences) != len(self.docs[0].sentences):
                # if length > last, we can go on
                if last and len(d.sentences) > last and len(self.docs[0].sentences) > last:
                    continue
                print("!!! file %s and %s differ in number of sentences" % (d.fn, self.docs[0].fn))
                raise Exception("file %s and %s differ in number of sentences" % (d.fn, self.docs[0].fn))

    def eval(self, micro=True, runs=1, ofp=sys.stdout, report=None, smatchpp=False, sortcolumn=None):
        rfp = None
        if report:
            rfp = open(report, "w")
            reportlines = []

        if micro:
            # comparing all sentences of a pair of annotators and calculate an average fo each pair of annotators
            results = [] # list of averages of smatch of annotator pairs on all sentences
            diffresults = []  # list of averages of differences of annotator pairs on all sentences
            if rfp:
                headers = ["annotators"]
                for ix, s in enumerate(self.docs[0].sentences):
                    sid = s.id
                    if not sid:
                        sid = ix
                    headers.append("smatch: %s" % sid)
                headers.append("average smatch")
                for s in self.docs[0].sentences:
                    sid = s.id
                    if not sid:
                        sid = ix
                    headers.append("diffs: %s" % s.id)
                headers.append("average diffs")
                print("\t".join(headers), file=rfp)

            for fi1 in range(self.numfiles):
                for fi2 in range(fi1 + 1, self.numfiles):
                    localresults = [] # list of smatch on all sentences for a given annotator pair
                    localdiffresults = [] # list of diffs on all sentences for a given annotator pair
                    for ix in range(len(self.docs[0].sentences)):
                        if ix < self.first:
                            continue
                        if self.last > 0 and ix > self.last:
                            break

                        sent1 = self.docs[fi1].sentences[ix]
                        sent2 = self.docs[fi2].sentences[ix]

                        compres = amr_comparison.compare(sent1.amr, sent2.amr, runs=runs, use_smatchpp=smatchpp, align=False)

                        localresults.append(compres.f1)
                        localdiffresults.append(compres.number_of_diffs)

                    if self.debug:
                        print("annotators %d/%d: sentence comparison smatch: %s" % (fi1, fi2, [float("%.2f" % (100 * x)) for x in localresults]), file=ofp)
                        print("                sentence comparison diffs.: %s" % ([x for x in localdiffresults]), file=ofp)

                    lmean = sum(localresults) / len(localresults)
                    ldmean = sum(localdiffresults) / len(localdiffresults)
                    results.append(lmean)
                    diffresults.append(ldmean)

                    if rfp:
                        couple = "annotator %d-%d" % (fi1, fi2)
                        entry = [couple]
                        for x in localresults:
                            entry.append(round(100 * x, 2))
                        entry.append(round(100 * lmean, 2))
                        for x in localdiffresults:
                            entry.append(x)
                        entry.append(round(ldmean, 2))

                        reportlines.append(entry)

                    #print("annotator", fi1, fi2, localresults, lmean)
            if rfp:
                if sortcolumn is not None:
                    reportlines = sorted(reportlines, key=lambda x: x[sortcolumn])
                for line in reportlines:
                    s = [str(i) for i in line]
                    print("\t".join(s), file=rfp)
            # calculating the average
            mean = sum(results) / len(results)
            if self.debug:
                print("averages for %d annotator pairs (smatch): %s" % (len(results), [float("%.2f" % (100 * x)) for x in results]), file=ofp)
                print("                                (diffs): %s" % ([float("%.4f" % x) for x in diffresults]), file=ofp)
            dmean = sum(diffresults) / len(diffresults)
            print("sentence inter-annotator agreement Smatch F1: %.2f differences: %.4f" % (100 * mean, dmean), file=ofp)

        else:
            # comparing all pairs of annotators of a sentence and calculate an average for each sentence
            results = [] # list of averages of all sentences smatch of all annotator pairs
            diffresults = []  # differences on all sentences
            if rfp:
                headers = ["id"]
                for fi1 in range(self.numfiles):
                    for fi2 in range(fi1 + 1, self.numfiles):
                        headers.append("smatch %d-%d" % (fi1, fi2))
                headers.append("average smatch")
                for fi1 in range(self.numfiles):
                    for fi2 in range(fi1 + 1, self.numfiles):
                        headers.append("diffs %d-%d" % (fi1, fi2))
                headers.append("average diffs")
                print("\t".join(headers), file=rfp)

            for ix in range(len(self.docs[0].sentences)):
                if ix < self.first:
                    continue

                localresults = [] # list of smatch for all annotator pairs for a given sentence
                localdiffresults = []
                for fi1 in range(self.numfiles):
                    sent1 = self.docs[fi1].sentences[ix]
                    for fi2 in range(fi1 + 1, self.numfiles):
                        sent2 = self.docs[fi2].sentences[ix]
                        if sent1.id != sent2.id:
                            print("!! Sentences to be compared have different ids: %s != %s" % (sent1.id, sent2.id))

                        compres = amr_comparison.compare(sent1.amr, sent2.amr, runs=runs, use_smatchpp=smatchpp, align=True)

                        localresults.append(compres.f1)
                        localdiffresults.append(compres.number_of_diffs)
                if self.debug:
                    print("sentence %5d: annotator pairs smatch: %s" % (ix, [float("%.2f" % (100 * x)) for x in localresults]), file=ofp)
                    print("                annotator pairs diffs.: %s" % ([x for x in localdiffresults]), file=ofp)

                lmean = sum(localresults) / len(localresults)
                ldmean = sum(localdiffresults) / len(localdiffresults)
                results.append(lmean)
                diffresults.append(ldmean)

                if rfp:
                    sid = sent1.id
                    if not sid:
                        sid = ix
                    entry = [sid]
                    for x in localresults:
                        entry.append(round(100 * x, 2))
                    entry.append(round(100 * lmean, 2))
                    for x in localdiffresults:
                        entry.append(x)
                    entry.append(round(ldmean, 2))
                    reportlines.append(entry)
                #print("sent", ix, localresults, lmean)

                if self.last > 0 and ix == self.last:
                    break

            if rfp:
                if sortcolumn is not None:
                    reportlines = sorted(reportlines, key=lambda x: x[sortcolumn])
                for line in reportlines:
                    s = [str(i) for i in line]
                    print("\t".join(s), file=rfp)
            mean = sum(results) / len(results)
            dmean = sum(diffresults) / len(diffresults)
            if self.debug:
                print("averages for %d sentences (smatch): %s" % (len(results), [float("%.2f" % (100 * x)) for x in results]), file=ofp)
                print("                          (diffs): %s" % ([float("%.2f" % (x)) for x in diffresults]), file=ofp)
            print("annotator pair inter-annotator agreement Smatch F1: %.2f differences: %.4f" % (100 * mean, dmean), file=ofp)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="inter-annotator agreement")
    parser.add_argument("--files", '-f', nargs="+", required=True, type=argparse.FileType('r'), help='AMR files of all annotatoris')
    parser.add_argument("--sentences", '-s', action='store_true', default=False, help='sentences are in inner loop')
    parser.add_argument("--debug", '-d', action='store_true', help='debug')
    parser.add_argument("--smatchpp", "-S", action='store_true', help='use smatchpp (https://github.com/flipz357/smatchpp) instead of smatch')
    parser.add_argument("--report", '-r', help='filename for a report in TSV format')
    parser.add_argument('--runs', type=int, default=1, help='run smatch n times to get the best possible match')
    parser.add_argument('--first', type=int, default=0, help='skip first n sentences')
    parser.add_argument('--last', type=int, default=0, help='stop after sentences n')
    parser.add_argument('--sortcol', type=int, default=None, help='sort data in report file on column (needs --report)')

    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()
        iaa = IAA(args.files, debug=args.debug, first=args.first, last=args.last)
        iaa.eval(micro=args.sentences, runs=args.runs, ofp=sys.stdout, report=args.report, smatchpp=args.smatchpp, sortcolumn=args.sortcol)


if __name__ == "__main__":
    main()
