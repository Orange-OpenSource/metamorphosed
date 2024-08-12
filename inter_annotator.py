#!/usr/bin/env python3

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

import amrdoc
#from smatch_pm import Smatch
#from smatchpp import Smatchpp, solvers, data_helpers

import amr_comparison


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
                print("!!! file %s and %s differ in number of sentences" % (d.fn, self.docs[0].fn))
                raise Exception("file %s and %s differ in number of sentences" % (d.fn, self.docs[0].fn))

    def eval(self, micro=True, runs=1, ofp=sys.stdout, report=None, smatchpp=False):
        rfp = None
        if report:
            rfp = open(report, "w")

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
                        print("                sentence comparison diffs.: %s" % ([float("%.4f" % (x)) for x in localdiffresults]), file=ofp)

                    lmean = sum(localresults) / len(localresults)
                    ldmean = sum(localdiffresults) / len(localdiffresults)
                    results.append(lmean)
                    diffresults.append(ldmean)

                    if rfp:
                        couple = "annotator %d-%d" % (fi1, fi2)
                        print(couple,
                              "\t".join(["%.2f" % (100 * x) for x in localresults]),
                              "%.2f" % (100 * lmean),
                              "\t".join(["%.2f" % (x) for x in localdiffresults]),
                              "%.2f" % (ldmean),
                              sep="\t", file=rfp)

                    #print("annotator", fi1, fi2, localresults, lmean)
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
                    print("                annotator pairs diffs.: %s" % ([float("%.2f" % (x)) for x in localdiffresults]), file=ofp)

                lmean = sum(localresults) / len(localresults)
                ldmean = sum(localdiffresults) / len(localdiffresults)
                results.append(lmean)
                diffresults.append(ldmean)

                if rfp:
                    sid = sent1.id
                    if not sid:
                        sid = ix
                    print(sid,
                          "\t".join(["%.2f" % (100 * x) for x in localresults]),
                          "%.2f" % (100 * lmean),
                          "\t".join(["%.2f" % (x) for x in localdiffresults]),
                          "%.2f" % (ldmean),
                          sep="\t", file=rfp)
                #print("sent", ix, localresults, lmean)
                if self.last > 0 and ix == self.last:
                    break

            mean = sum(results) / len(results)
            dmean = sum(diffresults) / len(diffresults)
            if self.debug:
                print("averages for %d sentences (smatch): %s" % (len(results), [float("%.2f" % (100 * x)) for x in results]), file=ofp)
                print("                          (diffs): %s" % ([float("%.2f" % (x)) for x in diffresults]), file=ofp)
            print("annotator pair inter-annotator agreement Smatch F1: %.2f differences: %.4f" % (100 * mean, dmean), file=ofp)


if __name__ == "__main__":
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

    args = parser.parse_args()
    iaa = IAA(args.files, debug=args.debug, first=args.first, last=args.last)
    iaa.eval(micro=args.sentences, runs=args.runs, ofp=sys.stdout, report=args.report, smatchpp=args.smatchpp)
