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

# this code is based on https://github.com/snowblink14/smatch/blob/master/smatch.py
# Copyright (C) 2015 Shu Cai and Kevin Knight
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# - The above copyright notice and this permission notice shall be included in all
#      copies or substantial portions of the Software.
# - THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#      INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#      PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
#      FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#      OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# version 2.8.0 as of 12th November 2023

import collections
import random
import sys

import penman

import metamorphosed.amrdoc as amrdoc

# silence penman
import logging
logging.getLogger('penman').setLevel(logging.ERROR)


# Error log location
ERROR_LOG = sys.stderr

# Debug log location
DEBUG_LOG = sys.stderr

# Outputs micro Smatch (P/R/F1 calculated on total sum of matched triples, gold triples, test triples)


class Smatch:
    def __init__(self, verbose=False, veryVerbose=False, single_score=True):
        # total number of iteration in smatch computation
        self.iteration_num = 5

        # verbose output switch.
        # Default false (no verbose output)
        self.verbose = verbose
        self.veryVerbose = veryVerbose

        # single score output switch.
        # Default true (compute a single score for all AMRs in two files)
        self.single_score = single_score

        # precision and recall output switch.
        # Default false (do not output precision and recall, just output F score)
        #self.pr_flag = False

        # dictionary to save pre-computed node mapping and its resulting triple match count
        # key: tuples of node mapping
        # value: the matching triple count
        self.match_triple_dict = collections.OrderedDict()

    def generate_amr_lines(self, f1, f2):
        """
        Read one AMR line at a time from each file handle
        :param f1: file handle (or any iterable of strings) to read AMR 1 lines from
        :param f2: file handle (or any iterable of strings) to read AMR 2 lines from
        :return: generator of cur_amr1, cur_amr2 pairs: one-line AMR strings
        """
        #print("OPEN")
        doc1 = amrdoc.AMRdoc(f1)
        doc2 = amrdoc.AMRdoc(f2)
        #sentences1 = iter(doc1.sentences)
        sentences2 = iter(doc2.sentences)
        for sent1 in doc1.sentences:
            #print("lllll")
            #sent1 = next(sentences1)
            try:
                sent2 = next(sentences2)
            except StopIteration:
                pass
            if not sent1 and not sent2:
                pass
            elif not sent1:
                print("Error: File 1 has less AMRs than file 2", file=ERROR_LOG)
                print("Ignoring remaining AMRs", file=ERROR_LOG)
            elif not sent2:
                print("Error: File 2 has less AMRs than file 1", file=ERROR_LOG)
                print("Ignoring remaining AMRs", file=ERROR_LOG)
            else:
                #print("AAAA",sent1.id)
                #yield sent1.amr, sent2.amr
                yield sent1, sent2
                continue
            break

    def score_amr_pairs(self, f1, f2, justinstance=False, justattribute=False, justrelation=False):
        """
        Score one pair of AMR lines at a time from each file handle
        :param f1: file handle (or any iterable of strings) to read AMR 1 lines from
        :param f2: file handle (or any iterable of strings) to read AMR 2 lines from
        :param justinstance: just pay attention to matching instances
        :param justattribute: just pay attention to matching attributes
        :param justrelation: just pay attention to matching relations
        :return: generator of cur_amr1, cur_amr2 pairs: one-line AMR strings
        """
        # matching triple number, triple number in test file, triple number in gold file
        total_match_num = total_test_num = total_gold_num = 0
        # Read amr pairs from two files
        for sent_num, (cur_amr1, cur_amr2) in enumerate(self.generate_amr_lines(f1, f2), start=1):
            self.match_triple_dict.clear()
            try:
                best_match_num, test_triple_num, gold_triple_num, _, _, _, _ = self.get_amr_match(cur_amr1.amr.replace("\n", ""),
                                                                                                  cur_amr2.amr.replace("\n", ""),
                                                                                                  sent_num=sent_num,  # sentence number
                                                                                                  justinstance=justinstance,
                                                                                                  justattribute=justattribute,
                                                                                                  justrelation=justrelation)
            except penman.exceptions.DecodeError as e:
                print("Invalid PENMAN", e)
                best_match_num = 0
                test_triple_num = 1 # need something > 0 here, else R and P are 100% in the case of bas penman!
                gold_triple_num = 1
            total_match_num += best_match_num
            total_test_num += test_triple_num
            total_gold_num += gold_triple_num
            # clear the matching triple dictionary for the next AMR pair
            #self.match_triple_dict.clear()
            #print("ZZZZ", best_match_num, test_triple_num, gold_triple_num)
            number_of_diffs = max(test_triple_num, gold_triple_num) - best_match_num
            #print("#Diffs", number_of_diffs)
            if not self.single_score:  # if each AMR pair should have a score, compute and output it here
                yield sent_num, cur_amr1.id, cur_amr2.id, number_of_diffs, self.compute_f(best_match_num, test_triple_num, gold_triple_num)
        if self.verbose:
            print("Total match number, total triple number in AMR 1, and total triple number in AMR 2:", file=DEBUG_LOG)
            print(total_match_num, total_test_num, total_gold_num, file=DEBUG_LOG)
            print("---------------------------------------------------------------------------------", file=DEBUG_LOG)
        if self.single_score:  # output document-level smatch score (a single f-score for all AMR pairs in two files)
            yield -1, "", "", -1, self.compute_f(total_match_num, total_test_num, total_gold_num)

    def parse_AMR(self, amr, prefix):
        node_map_dict = {} # old: new
        reversemap = {} # new:old

        triples = [] # all triples
        tvars = {} # var: concept
        instancetriples = []
        othertriples = []

        #try:
        tree = penman.parse(amr)
        #except penman.exceptions.DecodeError as e:
        #    print("invalid penman format", e)
        #    return reversemap, None, None, None

        top = None
        for branch in tree.nodes():
            s = branch[0]
            if not top:
                top = s
            #print(s)
            #if s in usedvariables:
            #    s = "%s_new%d" % (s, i)

            for po in branch[1]:
                #print("   ", po)
                p = po[0]
                o = po[1]

                if p == "/":
                    p = ":instance"
                    tvars[s] = o
                    #if not s[0] in self.varletters:
                    #    self.varletters[s[0]] = set([s])
                    #else:
                    #    self.varletters[s[0]].add(s)
                if not isinstance(o, str):
                    o = o[0]
                #print("TR", s,p,o)
                #if o in usedvariables:
                #    o = "%s_new%d" % (o, i)
                if p == ":instance":
                    instancetriples.append((s, p, o))
                else:
                    othertriples.append((s, p, o))
                triples.append((s, p, o))
        #print("4444", triples)

        for i, (s, p, o) in enumerate(instancetriples):
            n = "%s%d" % (prefix, i)
            node_map_dict[s] = n
            reversemap[n] = s
        #print("NM", node_map_dict)
        instances = []
        if top is not None:
            attributes = [("TOP", node_map_dict.get(top), "top")]
        else:
            attributes = []
        relations = []
        for s, p, o in instancetriples:
            instances.append(("instance", node_map_dict[s], o))

        exceptions = set([":prep-on-behalf-of", ":prep-out-of", ":consist-of"])
        # edges
        for u, r, v in othertriples:
            if u not in node_map_dict or v not in node_map_dict:
                # not an edge
                continue
            #print("ZZZZZZ", u,r,v)
            # we detect a relation (r) between u and v, with direction u to v.
            # in most cases, if relation name ends with "-of", e.g."arg0-of",
            # it is reverse of some relation. For example, if a is "arg0-of" b,
            # we can also say b is "arg0" a.
            # If the relation name ends with "-of", we store the reverse relation.
            # but note some exceptions like "prep-on-behalf-of" and "prep-out-of"
            # also note relation "mod" is the reverse of "domain"
            if r.endswith("-of") and r not in exceptions:
                relations.append((r[1:-3], node_map_dict[v], node_map_dict[u]))
            elif r == ":mod":
                relations.append(("domain", node_map_dict[v], node_map_dict[u]))
            else:
                relations.append((r[1:], node_map_dict[u], node_map_dict[v]))

        # attributes
        for s, p, o in othertriples:
            if s in node_map_dict and o in node_map_dict:
                continue
            if o[0] == '"':
                o = o[1:-1] + "_"

            attributes.append((p[1:], node_map_dict[s], o))

        return reversemap, instances, attributes, relations

#    def oooparse_AMR(self, pm, prefix):
#        graph = penman.decode(pm)
#        node_map_dict = {} # old: new
#        reversemap = {} # new:old
#        # map each node to its new name (e.g. "a1")
#        for i, (s, p, o) in enumerate(graph.instances()):
#            n = "%s%d" % (prefix, i)
#            node_map_dict[s] = n
#            reversemap[n] = s
#        #print("NM", node_map_dict)
#        instances = []
#        attributes = [("TOP", node_map_dict[graph.top], "top")]
#        relations = []
#        for s, p, o in graph.instances():
#            instances.append(("instance", node_map_dict[s], o))
#        exceptions = set([":prep-on-behalf-of", ":prep-out-of", ":consist-of"])
#        for s, p, o in graph.edges():
#            #print("ZZZZZZ", s,p,o)
#            # we detect a relation (r) between u and v, with direction u to v.
#            # in most cases, if relation name ends with "-of", e.g."arg0-of",
#            # it is reverse of some relation. For example, if a is "arg0-of" b,
#            # we can also say b is "arg0" a.
#            # If the relation name ends with "-of", we store the reverse relation.
#            # but note some exceptions like "prep-on-behalf-of" and "prep-out-of"
#            # also note relation "mod" is the reverse of "domain"
#            if p.endswith("-of") and p not in exceptions:
#                relations.append((p[1:-3], node_map_dict[o], node_map_dict[s]))
#            elif p == ":mod":
#                relations.append(("domain", node_map_dict[o], node_map_dict[s]))
#            else:
#                relations.append((p[1:], node_map_dict[s], node_map_dict[o]))
#
#        for s, p, o in graph.attributes():
#            if o[0] == '"':
#                o = o[1:-1] + "_"
#
#            attributes.append((p[1:], node_map_dict[s], o))
#
#        return reversemap, instances, attributes, relations

    def get_amr_match(self, cur_amr1, cur_amr2, sent_num=1,
                      justinstance=False, justattribute=False, justrelation=False):
        nodemap1, instance1, attributes1, relation1 = self.parse_AMR(cur_amr1, "a")
        nodemap2, instance2, attributes2, relation2 = self.parse_AMR(cur_amr2, "b")

        if self.verbose:
            print("AMR pair", sent_num, file=DEBUG_LOG)
            print("============================================", file=DEBUG_LOG)
            print("AMR 1 (one-line):", cur_amr1, file=DEBUG_LOG)
            print("AMR 2 (one-line):", cur_amr2, file=DEBUG_LOG)
            print("Instance triples of AMR 1:", len(instance1), file=DEBUG_LOG)
            print(instance1, file=DEBUG_LOG)
            print("Attribute triples of AMR 1:", len(attributes1), file=DEBUG_LOG)
            print(attributes1, file=DEBUG_LOG)
            print("Relation triples of AMR 1:", len(relation1), file=DEBUG_LOG)
            print(relation1, file=DEBUG_LOG)
            #for r in sorted(relation1): print(r, file=DEBUG_LOG)
            print("Instance triples of AMR 2:", len(instance2), file=DEBUG_LOG)
            print(instance2, file=DEBUG_LOG)
            print("Attribute triples of AMR 2:", len(attributes2), file=DEBUG_LOG)
            print(attributes2, file=DEBUG_LOG)
            print("Relation triples of AMR 2:", len(relation2), file=DEBUG_LOG)
            print(relation2, file=DEBUG_LOG)
            #for r in sorted(relation2): print(r, file=DEBUG_LOG)
        # optionally turn off some of the node comparison
        doinstance = doattribute = dorelation = True
        if justinstance:
            doattribute = dorelation = False
        if justattribute:
            doinstance = dorelation = False
        if justrelation:
            doinstance = doattribute = False
        (best_mapping, best_match_num) = self.get_best_match(instance1, attributes1, relation1,
                                                             instance2, attributes2, relation2,
                                                             "a", "b", doinstance=doinstance,
                                                             doattribute=doattribute, dorelation=dorelation)
        #print("B MN", best_match_num)
        alignments, mappednodes = self.print_alignment(best_mapping, instance1, instance2)

        if self.verbose:
            print("best match number", best_match_num, file=DEBUG_LOG)
            print("best node mapping", best_mapping, file=DEBUG_LOG)
            print("Best node mapping alignment:", self.print_alignment(best_mapping, instance1, instance2), file=DEBUG_LOG)
        if justinstance:
            test_triple_num = len(instance1)
            gold_triple_num = len(instance2)
        elif justattribute:
            test_triple_num = len(attributes1)
            gold_triple_num = len(attributes2)
        elif justrelation:
            test_triple_num = len(relation1)
            gold_triple_num = len(relation2)
        else:
            test_triple_num = len(instance1) + len(attributes1) + len(relation1)
            gold_triple_num = len(instance2) + len(attributes2) + len(relation2)

        def reorg(instances, attributes, relations):
            outgoing = {} # node {rel: [target]}
            for p, s, o in instances:
                outgoing[s] = {"instance": [o]}
            for p, s, o in attributes:
                if s not in outgoing:
                    outgoing[s] = {}
                if p not in outgoing[s]:
                    outgoing[s][p] = []
                outgoing[s][p].append(o)
            for p, s, o in relations:
                if s not in outgoing:
                    outgoing[s] = {}
                if p not in outgoing[s]:
                    outgoing[s][p] = []
                outgoing[s][p].append(o)
            return outgoing
        outgoing1 = reorg(instance1, attributes1, relation1)
        outgoing2 = reorg(instance2, attributes2, relation2)
        #print("TT1", outgoing1)
        #print("TT2", outgoing2)

        ok = 0

        instances1OK = set() # variables which are correctly mapped
        rel1OK = set() # (s,p,o) which maps correctly
        instances2OK = set() # variables
        rel2OK = set() # (s,p,o)

        for s1, s2 in mappednodes.items():
            #if outgoing1[s1]["instance"] == outgoing2[s2]["instance"]:
            #    print(s1, s2, "OK")
            #    ok += 1
            #else:
            #    print(s1, s2, "KO")
            #print("\nsss", s1, s2)
            for p in outgoing1[s1]:
                if p in outgoing2[s2]:
                    o1 = outgoing1[s1][p]
                    o2 = outgoing2[s2][p]
                    if o1[0] not in mappednodes:
                        if o1 == o2:
                            #print("OK:I/A", nodemap1[s1], nodemap2[s2], p, outgoing1[s1][p])
                            ok += 1
                            if p == "instance":
                                instances1OK.add(nodemap1[s1])
                                instances2OK.add(nodemap2[s2])
                            else:
                                oo1 = o1[0]
                                if oo1[-1] == "_":
                                    oo1 = '"%s"' % o1[0][:-1]
                                oo2 = o2[0]
                                if oo2[-1] == "_":
                                    oo2 = '"%s"' % o2[0][:-1]
                                rel1OK.add((nodemap1[s1], ":" + p, oo1))
                                rel2OK.add((nodemap2[s2], ":" + p, oo2))

                    elif mappednodes.get(o1[0]) == o2[0]:
                        #print("OK:REL", nodemap1[s1], nodemap2[s2], p, outgoing1[s1][p])
                        ok += 1
                        rel1OK.add((nodemap1[s1], ":" + p, nodemap1[o1[0]]))
                        rel2OK.add((nodemap2[s2], ":" + p, nodemap2[o2[0]]))
                        if p == "domain":
                            rel1OK.add((nodemap1[o1[0]], ":mod", nodemap1[s1]))
                            rel2OK.add((nodemap2[o2[0]], ":mod", nodemap2[s2]))
                        elif p == "mod":
                            rel1OK.add((nodemap1[o1[0]], ":domain", nodemap1[s1]))
                            rel2OK.add((nodemap2[o2[0]], ":domain", nodemap2[s2]))
                        else:
                            rel1OK.add((nodemap1[o1[0]], ":" + p + "-of", nodemap1[s1]))
                            rel2OK.add((nodemap2[o2[0]], ":" + p + "-of", nodemap2[s2]))

        #print("111", instances1OK, "\n   ", rel1OK)
        #print("222", instances2OK, "\n   ", rel2OK)

        #print("ok", ok, best_match_num)
        #print("TTTT", len(instance1) , len(attributes1) , len(relation1))
        #print("GGGG", len(instance2) , len(attributes2) , len(relation2))
        return best_match_num, test_triple_num, gold_triple_num, instances1OK, rel1OK, instances2OK, rel2OK

    def get_best_match(self, instance1, attribute1, relation1,
                       instance2, attribute2, relation2,
                       prefix1, prefix2, doinstance=True, doattribute=True, dorelation=True):
        """
        Get the highest triple match number between two sets of triples via hill-climbing.
        Arguments:
            instance1: instance triples of AMR 1 ("instance", node name, node value)
            attribute1: attribute triples of AMR 1 (attribute name, node name, attribute value)
            relation1: relation triples of AMR 1 (relation name, node 1 name, node 2 name)
            instance2: instance triples of AMR 2 ("instance", node name, node value)
            attribute2: attribute triples of AMR 2 (attribute name, node name, attribute value)
            relation2: relation triples of AMR 2 (relation name, node 1 name, node 2 name)
            prefix1: prefix label for AMR 1
            prefix2: prefix label for AMR 2
        Returns:
            best_match: the node mapping that results in the highest triple matching number
            best_match_num: the highest triple matching number

        """
        # Compute candidate pool - all possible node match candidates.
        # In the hill-climbing, we only consider candidate in this pool to save computing time.
        # weight_dict is a dictionary that maps a pair of node
        (candidate_mappings, weight_dict) = self.compute_pool(instance1, attribute1, relation1,
                                                              instance2, attribute2, relation2,
                                                              prefix1, prefix2, doinstance=doinstance, doattribute=doattribute,
                                                              dorelation=dorelation)
        # weight_dict: a dictionary which contains the matching triple number for every pair of node mapping. The key
        #   is a node pair. The value is another dictionary.
        #         key {-1} is triple match resulting from this node pair alone (instance triples and attribute triples),
        #         and other keys are node pairs that can result in relation triple match together with the first node pair.

        if self.veryVerbose:
            print("Candidate mappings:", file=DEBUG_LOG)
            print(candidate_mappings, file=DEBUG_LOG)
            print("Weight dictionary", file=DEBUG_LOG)
            print(weight_dict, file=DEBUG_LOG)
            #for k in weight_dict:
            #    print(k, file=DEBUG_LOG)
            #    print(instance1[k[0]][1:], instance2[k[1]][1:], file=DEBUG_LOG)
            #    for kk in weight_dict[k]:
            #        print("  ", kk, weight_dict[k][kk], file=DEBUG_LOG)

        best_match_num = 0
        # initialize best match mapping
        # the ith entry is the node index in AMR 2 which maps to the ith node in AMR 1
        best_mapping = [-1] * len(instance1)
        for i in range(self.iteration_num):
            if self.veryVerbose:
                print("Iteration", i, file=DEBUG_LOG)
            if i == 0:
                # smart initialization used for the first round
                cur_mapping = self.smart_init_mapping(candidate_mappings, instance1, instance2)
            else:
                # random initialization for the other round
                cur_mapping = self.random_init_mapping(candidate_mappings)
            # compute current triple match number
            match_num = self.compute_match(cur_mapping, weight_dict)
            if self.veryVerbose:
                print("Node mapping at start", cur_mapping, file=DEBUG_LOG)
                print("Triple match number at start:", match_num, file=DEBUG_LOG)
            while True:
                # get best gain
                (gain, new_mapping) = self.get_best_gain(cur_mapping, candidate_mappings, weight_dict,
                                                         len(instance2), match_num)
                if self.veryVerbose:
                    print("Gain after the hill-climbing", gain, file=DEBUG_LOG)
                # hill-climbing until there will be no gain for new node mapping
                if gain <= 0:
                    break
                # otherwise update match_num and mapping
                match_num += gain
                cur_mapping = new_mapping[:]
                if self.veryVerbose:
                    print("Update triple match number to:", match_num, file=DEBUG_LOG)
                    print("Current mapping:", cur_mapping, file=DEBUG_LOG)
            if match_num > best_match_num:
                best_mapping = cur_mapping[:]
                best_match_num = match_num
        return best_mapping, best_match_num

    def normalize(self, item):
        """
        lowercase and remove quote signifiers from items that are about to be compared
        """
        return item.lower().rstrip('_')

    def compute_pool(self, instance1, attribute1, relation1,
                     instance2, attribute2, relation2,
                     prefix1, prefix2, doinstance=True, doattribute=True, dorelation=True):
        """
        compute all possible node mapping candidates and their weights (the triple matching number gain resulting from
        mapping one node in AMR 1 to another node in AMR2)

        Arguments:
            instance1: instance triples of AMR 1
            attribute1: attribute triples of AMR 1 (attribute name, node name, attribute value)
            relation1: relation triples of AMR 1 (relation name, node 1 name, node 2 name)
            instance2: instance triples of AMR 2
            attribute2: attribute triples of AMR 2 (attribute name, node name, attribute value)
            relation2: relation triples of AMR 2 (relation name, node 1 name, node 2 name
            prefix1: prefix label for AMR 1
            prefix2: prefix label for AMR 2
        Returns:
          candidate_mapping: a list of candidate nodes.
                           The ith element contains the node indices (in AMR 2) the ith node (in AMR 1) can map to.
                           (resulting in non-zero triple match)
          weight_dict: a dictionary which contains the matching triple number for every pair of node mapping. The key
                       is a node pair. The value is another dictionary. key {-1} is triple match resulting from this node
                       pair alone (instance triples and attribute triples), and other keys are node pairs that can result
                       in relation triple match together with the first node pair.


        """
        candidate_mapping = []
        weight_dict = collections.OrderedDict()
        for instance1_item in instance1:
            # each candidate mapping is a set of node indices
            candidate_mapping.append(set())
            if doinstance:
                for instance2_item in instance2:
                    # if both triples are instance triples and have the same value
                    if self.normalize(instance1_item[0]) == self.normalize(instance2_item[0]) and \
                            self.normalize(instance1_item[2]) == self.normalize(instance2_item[2]):
                        # get node index by stripping the prefix
                        node1_index = int(instance1_item[1][len(prefix1):])
                        node2_index = int(instance2_item[1][len(prefix2):])
                        candidate_mapping[node1_index].add(node2_index)
                        node_pair = (node1_index, node2_index)
                        # use -1 as key in weight_dict for instance triples and attribute triples
                        if node_pair in weight_dict:
                            weight_dict[node_pair][-1] += 1
                        else:
                            weight_dict[node_pair] = collections.OrderedDict()
                            weight_dict[node_pair][-1] = 1
        if doattribute:
            for attribute1_item in attribute1:
                for attribute2_item in attribute2:
                    # if both attribute relation triple have the same relation name and value
                    if self.normalize(attribute1_item[0]) == self.normalize(attribute2_item[0]) \
                            and self.normalize(attribute1_item[2]) == self.normalize(attribute2_item[2]):
                        node1_index = int(attribute1_item[1][len(prefix1):])
                        node2_index = int(attribute2_item[1][len(prefix2):])
                        candidate_mapping[node1_index].add(node2_index)
                        node_pair = (node1_index, node2_index)
                        # use -1 as key in weight_dict for instance triples and attribute triples
                        if node_pair in weight_dict:
                            weight_dict[node_pair][-1] += 1
                        else:
                            weight_dict[node_pair] = collections.OrderedDict()
                            weight_dict[node_pair][-1] = 1
        if dorelation:
            for relation1_item in relation1:
                for relation2_item in relation2:
                    # if both relation share the same name
                    if self.normalize(relation1_item[0]) == self.normalize(relation2_item[0]):
                        node1_index_amr1 = int(relation1_item[1][len(prefix1):])
                        node1_index_amr2 = int(relation2_item[1][len(prefix2):])
                        node2_index_amr1 = int(relation1_item[2][len(prefix1):])
                        node2_index_amr2 = int(relation2_item[2][len(prefix2):])
                        # add mapping between two nodes
                        candidate_mapping[node1_index_amr1].add(node1_index_amr2)
                        candidate_mapping[node2_index_amr1].add(node2_index_amr2)
                        node_pair1 = (node1_index_amr1, node1_index_amr2)
                        node_pair2 = (node2_index_amr1, node2_index_amr2)
                        if node_pair2 != node_pair1:
                            # update weight_dict weight. Note that we need to update both entries for future search
                            # i.e weight_dict[node_pair1][node_pair2]
                            #     weight_dict[node_pair2][node_pair1]
                            if node1_index_amr1 > node2_index_amr1:
                                # swap node_pair1 and node_pair2
                                node_pair1 = (node2_index_amr1, node2_index_amr2)
                                node_pair2 = (node1_index_amr1, node1_index_amr2)
                            if node_pair1 in weight_dict:
                                if node_pair2 in weight_dict[node_pair1]:
                                    weight_dict[node_pair1][node_pair2] += 1
                                else:
                                    weight_dict[node_pair1][node_pair2] = 1
                            else:
                                weight_dict[node_pair1] = {-1: 0, node_pair2: 1}
                            if node_pair2 in weight_dict:
                                if node_pair1 in weight_dict[node_pair2]:
                                    weight_dict[node_pair2][node_pair1] += 1
                                else:
                                    weight_dict[node_pair2][node_pair1] = 1
                            else:
                                weight_dict[node_pair2] = {-1: 0, node_pair1: 1}
                        else:
                            # two node pairs are the same. So we only update weight_dict once.
                            # this generally should not happen.
                            if node_pair1 in weight_dict:
                                weight_dict[node_pair1][-1] += 1
                            else:
                                weight_dict[node_pair1] = {-1: 1}
        return candidate_mapping, weight_dict

    def smart_init_mapping(self, candidate_mapping, instance1, instance2):
        """
        Initialize mapping based on the concept mapping (smart initialization)
        Arguments:
            candidate_mapping: candidate node match list
            instance1: instance triples of AMR 1
            instance2: instance triples of AMR 2
        Returns:
            initialized node mapping between two AMRs
        """
        random.seed()
        matched_dict = collections.OrderedDict()
        result = []
        # list to store node indices that have no concept match
        no_word_match = []
        for i, candidates in enumerate(candidate_mapping):
            if not candidates:
                # no possible mapping
                result.append(-1)
                continue
            # node value in instance triples of AMR 1
            value1 = instance1[i][2]
            for node_index in candidates:
                value2 = instance2[node_index][2]
                # find the first instance triple match in the candidates
                # instance triple match is having the same concept value
                if value1 == value2:
                    if node_index not in matched_dict:
                        result.append(node_index)
                        matched_dict[node_index] = 1
                        break
            if len(result) == i:
                no_word_match.append(i)
                result.append(-1)
        # if no concept match, generate a random mapping
        for i in no_word_match:
            candidates = list(candidate_mapping[i])
            while candidates:
                # get a random node index from candidates
                rid = random.randint(0, len(candidates) - 1)
                candidate = candidates[rid]
                if candidate in matched_dict:
                    candidates.pop(rid)
                else:
                    matched_dict[candidate] = 1
                    result[i] = candidate
                    break
        return result

    def random_init_mapping(self, candidate_mapping):
        """
        Generate a random node mapping.
        Args:
            candidate_mapping: candidate_mapping: candidate node match list
        Returns:
            randomly-generated node mapping between two AMRs

        """
        # if needed, a fixed seed could be passed here to generate same random (to help debugging)
        random.seed()
        matched_dict = collections.OrderedDict()
        result = []
        for c in candidate_mapping:
            candidates = list(c)
            if not candidates:
                # -1 indicates no possible mapping
                result.append(-1)
                continue
            found = False
            while candidates:
                # randomly generate an index in [0, length of candidates)
                rid = random.randint(0, len(candidates) - 1)
                candidate = candidates[rid]
                # check if it has already been matched
                if candidate in matched_dict:
                    candidates.pop(rid)
                else:
                    matched_dict[candidate] = 1
                    result.append(candidate)
                    found = True
                    break
            if not found:
                result.append(-1)
        return result

    def compute_match(self, mapping, weight_dict):
        """
        Given a node mapping, compute match number based on weight_dict.
        Args:
        mappings: a list of node index in AMR 2. The ith element (value j) means node i in AMR 1 maps to node j in AMR 2.
        Returns:
        matching triple number
        Complexity: O(m*n) , m is the node number of AMR 1, n is the node number of AMR 2

        """
        # If this mapping has been investigated before, retrieve the value instead of re-computing.
        if self.veryVerbose:
            print("Computing match for mapping", file=DEBUG_LOG)
            print(mapping, file=DEBUG_LOG)
        if tuple(mapping) in self.match_triple_dict:
            if self.veryVerbose:
                print("saved value", self.match_triple_dict[tuple(mapping)], file=DEBUG_LOG)
            return self.match_triple_dict[tuple(mapping)]
        match_num = 0
        # i is node index in AMR 1, m is node index in AMR 2
        for i, m in enumerate(mapping):
            if m == -1:
                # no node maps to this node
                continue
            # node i in AMR 1 maps to node m in AMR 2
            current_node_pair = (i, m)
            if current_node_pair not in weight_dict:
                continue
            if self.veryVerbose:
                print("node_pair", current_node_pair, file=DEBUG_LOG)
            for key in weight_dict[current_node_pair]:
                if key == -1:
                    # matching triple resulting from instance/attribute triples
                    match_num += weight_dict[current_node_pair][key]
                    if self.veryVerbose:
                        print("=== instance/attribute match", weight_dict[current_node_pair][key], file=DEBUG_LOG)
                # only consider node index larger than i to avoid duplicates
                # as we store both weight_dict[node_pair1][node_pair2] and
                #     weight_dict[node_pair2][node_pair1] for a relation
                elif key[0] < i:
                    continue
                elif mapping[key[0]] == key[1]:
                    match_num += weight_dict[current_node_pair][key]
                    if self.veryVerbose:
                        print("=== relation match with", key, weight_dict[current_node_pair][key], file=DEBUG_LOG)
        if self.veryVerbose:
            print("match computing complete, result:", match_num, file=DEBUG_LOG)
        # update match_triple_dict
        self.match_triple_dict[tuple(mapping)] = match_num
        return match_num

    def get_best_gain(self, mapping, candidate_mappings, weight_dict, instance_len, cur_match_num):
        """
        Hill-climbing method to return the best gain swap/move can get
        Arguments:
        mapping: current node mapping
        candidate_mappings: the candidates mapping list
        weight_dict: the weight dictionary
        instance_len: the number of the nodes in AMR 2
        cur_match_num: current triple match number
        Returns:
        the best gain we can get via swap/move operation
        """

        largest_gain = 0
        # True: using swap; False: using move
        use_swap = True
        # the node to be moved/swapped
        node1 = None
        # store the other node affected. In swap, this other node is the node swapping with node1. In move, this other
        # node is the node node1 will move to.
        node2 = None
        # unmatched nodes in AMR 2
        unmatched = set(range(instance_len))
        # exclude nodes in current mapping
        # get unmatched nodes
        for nid in mapping:
            if nid in unmatched:
                unmatched.remove(nid)
        for i, nid in enumerate(mapping):
            # current node i in AMR 1 maps to node nid in AMR 2
            for nm in unmatched:
                if nm in candidate_mappings[i]:
                    # remap i to another unmatched node (move)
                    # (i, m) -> (i, nm)
                    if self.veryVerbose:
                        print("Remap node", i, "from ", nid, "to", nm, file=DEBUG_LOG)
                    mv_gain = self.move_gain(mapping, i, nid, nm, weight_dict, cur_match_num)
                    if self.veryVerbose:
                        print("Move gain:", mv_gain, file=DEBUG_LOG)
                        new_mapping = mapping[:]
                        new_mapping[i] = nm
                        new_match_num = self.compute_match(new_mapping, weight_dict)
                        if new_match_num != cur_match_num + mv_gain:
                            print(mapping, new_mapping, file=ERROR_LOG)
                            print("Inconsistency in computing: move gain", cur_match_num, mv_gain, new_match_num,
                                  file=ERROR_LOG)
                    if mv_gain > largest_gain:
                        largest_gain = mv_gain
                        node1 = i
                        node2 = nm
                        use_swap = False
        # compute swap gain
        for i, m in enumerate(mapping):
            for j in range(i + 1, len(mapping)):
                m2 = mapping[j]
                # no need to compute swap gain if both (i, m2) (j, m) are not in candidate mappings
                # such a swap cannot incur any gains
                if (m2 not in candidate_mappings[i]) and (m not in candidate_mappings[j]):
                    continue
                # swap operation (i, m) (j, m2) -> (i, m2) (j, m)
                # j starts from i+1, to avoid duplicate swap
                if self.veryVerbose:
                    print("Swap node", i, "and", j, file=DEBUG_LOG)
                    print("Before swapping:", i, "-", m, ",", j, "-", m2, file=DEBUG_LOG)
                    print(mapping, file=DEBUG_LOG)
                    print("After swapping:", i, "-", m2, ",", j, "-", m, file=DEBUG_LOG)
                sw_gain = self.swap_gain(mapping, i, m, j, m2, weight_dict, cur_match_num)
                if self.veryVerbose:
                    print("Swap gain:", sw_gain, file=DEBUG_LOG)
                    new_mapping = mapping[:]
                    new_mapping[i] = m2
                    new_mapping[j] = m
                    print(new_mapping, file=DEBUG_LOG)
                    new_match_num = self.compute_match(new_mapping, weight_dict)
                    if new_match_num != cur_match_num + sw_gain:
                        print(mapping, new_mapping, file=ERROR_LOG)
                        print("Inconsistency in computing: swap gain", cur_match_num, sw_gain, new_match_num,
                              file=ERROR_LOG)
                if sw_gain > largest_gain:
                    largest_gain = sw_gain
                    node1 = i
                    node2 = j
                    use_swap = True
        # generate a new mapping based on swap/move
        cur_mapping = mapping[:]
        if node1 is not None:
            if use_swap:
                if self.veryVerbose:
                    print("Use swap gain", file=DEBUG_LOG)
                temp = cur_mapping[node1]
                cur_mapping[node1] = cur_mapping[node2]
                cur_mapping[node2] = temp
            else:
                if self.veryVerbose:
                    print("Use move gain", file=DEBUG_LOG)
                cur_mapping[node1] = node2
        else:
            if self.veryVerbose:
                print("no move/swap gain found", file=DEBUG_LOG)
        if self.veryVerbose:
            print("Original mapping", mapping, file=DEBUG_LOG)
            print("Current mapping", cur_mapping, file=DEBUG_LOG)
        return largest_gain, cur_mapping

    def print_alignment(self, mapping, instance1, instance2):
        """
        print the alignment based on a node mapping
        Args:
            mapping: current node mapping list
            instance1: nodes of AMR 1
            instance2: nodes of AMR 2

        """
        result = []
        #print('I1', instance1)
        #print('I2', instance2)
        #print('MP', mapping)
        mappednodes = {} # nodes from both graphs being identical
        for instance1_item, m in zip(instance1, mapping):
            r = instance1_item[1] + "(" + instance1_item[2] + ")"
            if m == -1:
                r += "-Null"
            else:
                instance2_item = instance2[m]
                r += "-" + instance2_item[1] + "(" + instance2_item[2] + ")"
                #if instance1_item[2] == instance2_item[2]:
                #mappednodes.append((instance1_item[1], instance2_item[1]))
                mappednodes[instance1_item[1]] = instance2_item[1]
            result.append(r)
        #print("MAPPED", mappednodes)
        return " ".join(result), mappednodes

    def compute_f(self, match_num, test_num, gold_num):
        """
        Compute the f-score based on the matching triple number,
                                     triple number of AMR set 1,
                                     triple number of AMR set 2
        Args:
            match_num: matching triple number
            test_num:  triple number of AMR 1 (test file)
            gold_num:  triple number of AMR 2 (gold file)
        Returns:
            precision: match_num/test_num
            recall: match_num/gold_num
            f_score: 2*precision*recall/(precision+recall)
        """
        #print("matchnum", match_num, "test", test_num, "gold", gold_num)
        if test_num == 0 or gold_num == 0:
            return 0.00, 0.00, 0.00
        precision = float(match_num) / float(test_num)
        recall = float(match_num) / float(gold_num)
        if (precision + recall) != 0:
            f_score = 2 * precision * recall / (precision + recall)
            if self.veryVerbose:
                print("F-score:", f_score, file=DEBUG_LOG)
            return precision, recall, f_score
        else:
            if self.veryVerbose:
                print("F-score:", "0.0", file=DEBUG_LOG)
            return precision, recall, 0.00

    def swap_gain(self, mapping, node_id1, mapping_id1, node_id2, mapping_id2, weight_dict, match_num):
        """
        Compute the triple match number gain from the swapping
        Arguments:
        mapping: current node mapping list
        node_id1: node 1 index in AMR 1
        mapping_id1: the node index in AMR 2 node 1 maps to (in the current mapping)
        node_id2: node 2 index in AMR 1
        mapping_id2: the node index in AMR 2 node 2 maps to (in the current mapping)
        weight_dict: weight dictionary
        match_num: the original matching triple number
        Returns:
        the gain number (might be negative)

        """
        new_mapping_list = mapping[:]
        # Before swapping, node_id1 maps to mapping_id1, and node_id2 maps to mapping_id2
        # After swapping, node_id1 maps to mapping_id2 and node_id2 maps to mapping_id1
        new_mapping_list[node_id1] = mapping_id2
        new_mapping_list[node_id2] = mapping_id1
        if tuple(new_mapping_list) in self.match_triple_dict:
            return self.match_triple_dict[tuple(new_mapping_list)] - match_num
        gain = 0
        new_mapping1 = (node_id1, mapping_id2)
        new_mapping2 = (node_id2, mapping_id1)
        old_mapping1 = (node_id1, mapping_id1)
        old_mapping2 = (node_id2, mapping_id2)
        if node_id1 > node_id2:
            new_mapping2 = (node_id1, mapping_id2)
            new_mapping1 = (node_id2, mapping_id1)
            old_mapping1 = (node_id2, mapping_id2)
            old_mapping2 = (node_id1, mapping_id1)
        if new_mapping1 in weight_dict:
            for key in weight_dict[new_mapping1]:
                if key == -1:
                    gain += weight_dict[new_mapping1][-1]
                elif new_mapping_list[key[0]] == key[1]:
                    gain += weight_dict[new_mapping1][key]
        if new_mapping2 in weight_dict:
            for key in weight_dict[new_mapping2]:
                if key == -1:
                    gain += weight_dict[new_mapping2][-1]
                # to avoid duplicate
                elif key[0] == node_id1:
                    continue
                elif new_mapping_list[key[0]] == key[1]:
                    gain += weight_dict[new_mapping2][key]
        if old_mapping1 in weight_dict:
            for key in weight_dict[old_mapping1]:
                if key == -1:
                    gain -= weight_dict[old_mapping1][-1]
                elif mapping[key[0]] == key[1]:
                    gain -= weight_dict[old_mapping1][key]
        if old_mapping2 in weight_dict:
            for key in weight_dict[old_mapping2]:
                if key == -1:
                    gain -= weight_dict[old_mapping2][-1]
                # to avoid duplicate
                elif key[0] == node_id1:
                    continue
                elif mapping[key[0]] == key[1]:
                    gain -= weight_dict[old_mapping2][key]
        self.match_triple_dict[tuple(new_mapping_list)] = match_num + gain
        return gain

    def move_gain(self, mapping, node_id, old_id, new_id, weight_dict, match_num):
        """
        Compute the triple match number gain from the move operation
        Arguments:
            mapping: current node mapping
            node_id: remapped node in AMR 1
            old_id: original node id in AMR 2 to which node_id is mapped
            new_id: new node in to which node_id is mapped
            weight_dict: weight dictionary
            match_num: the original triple matching number
        Returns:
            the triple match gain number (might be negative)

        """
        # new node mapping after moving
        new_mapping = (node_id, new_id)
        # node mapping before moving
        old_mapping = (node_id, old_id)
        # new nodes mapping list (all node pairs)
        new_mapping_list = mapping[:]
        new_mapping_list[node_id] = new_id
        # if this mapping is already been investigated, use saved one to avoid duplicate computing
        if tuple(new_mapping_list) in self.match_triple_dict:
            return self.match_triple_dict[tuple(new_mapping_list)] - match_num
        gain = 0
        # add the triple match incurred by new_mapping to gain
        if new_mapping in weight_dict:
            for key in weight_dict[new_mapping]:
                if key == -1:
                    # instance/attribute triple match
                    gain += weight_dict[new_mapping][-1]
                elif new_mapping_list[key[0]] == key[1]:
                    # relation gain incurred by new_mapping and another node pair in new_mapping_list
                    gain += weight_dict[new_mapping][key]
        # deduct the triple match incurred by old_mapping from gain
        if old_mapping in weight_dict:
            for k in weight_dict[old_mapping]:
                if k == -1:
                    gain -= weight_dict[old_mapping][-1]
                elif mapping[k[0]] == k[1]:
                    gain -= weight_dict[old_mapping][k]
        # update match number dictionary
        self.match_triple_dict[tuple(new_mapping_list)] = match_num + gain
        return gain


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Smatch calculator")
    parser.add_argument('-f', nargs=2, required=True, type=argparse.FileType('r'),
                        help=('Two files containing AMR pairs. '
                              'AMRs in each file are separated by a single blank line'))
    parser.add_argument('-r', type=int, default=4, help='Restart number (Default:4)')
    parser.add_argument('--significant', type=int, default=4, help='significant digits to output (default: 2)')
    parser.add_argument('-v', action='store_true', help='Verbose output (Default:false)')
    parser.add_argument('--vv', action='store_true', help='Very Verbose output (Default:false)')
    parser.add_argument('--ms', action='store_true', default=False,
                        help=('Output multiple scores (one AMR pair a score) '
                              'instead of a single document-level smatch score '
                              '(Default: false)'))
    parser.add_argument('--pr', action='store_true', default=False,
                        help=('Output precision and recall as well as the f-score. '
                              'Default: false'))
    parser.add_argument('--justinstance', action='store_true', default=False, help="just pay attention to matching instances")
    parser.add_argument('--justattribute', action='store_true', default=False, help="just pay attention to matching attributes")
    parser.add_argument('--justrelation', action='store_true', default=False, help="just pay attention to matching relations")

    args = parser.parse_args()

    sm = Smatch(verbose=args.v, veryVerbose=args.vv, single_score=not args.ms)

    floatdisplay = "%%.%df" % args.significant
    for i, sid1, sid2, numdiffs, (precision, recall, best_f_score) in sm.score_amr_pairs(args.f[0], args.f[1],
                                                                                         justinstance=args.justinstance,
                                                                                         justattribute=args.justattribute,
                                                                                         justrelation=args.justrelation):
        # print("Sentence", sent_num)
        if args.pr:
            print("Precision: " + floatdisplay % precision)
            print("Recall: " + floatdisplay % recall)
        print(i, sid1, sid2, numdiffs, "F-score: " + floatdisplay % best_f_score, sep="\t")
