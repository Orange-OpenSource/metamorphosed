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
#    * Neither the name of the <organization> nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
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

# get a setd of nodes which are connect
# from a potentially disconnected graph


#class CheckGraph1:
#    def __init__(self, triples):
#        subgraphs = []
#
#        join = 0
#        for s, p, o in sorted(triples):
#            #print("\ntriple", s, o)
#            if not subgraphs:
#                subgraphs.append(set([s, o]))
#            else:
#                found = False
#                for sg in subgraphs:
#                    if s in sg or o in sg:
#                        sg.add(s)
#                        sg.add(o)
#                        found = True
#                        break
#                if not found:
#                    subgraphs.append(set([s, o]))
#
#                #print("BBB", subgraphs)
#                if len(subgraphs) > 1:
#                    todelete = []
#                    i = 0
#                    while i < len(subgraphs) - 1:
#                        j = i + 1
#                        while j < len(subgraphs):
#                            #print("iii", i,j, len(subgraphs))
#                            join += 1
#                            print("join??", join, subgraphs[i], subgraphs[j])
#                            if subgraphs[i].intersection(subgraphs[j]):
#                                print("yes")
#                                subgraphs[i].update(subgraphs[j])
#                                todelete.append(subgraphs[j])
#                                j += 1
#                            j += 1
#                        i += 1
#                    #print("delete:", todelete)
#                    for s in todelete:
#                        subgraphs.remove(s)
#                    #print(subgraphs)
#                    for x in subgraphs:
#                        print(sorted(x))


def findsubgraphs(triples):
    subgraphs = []
    # if an triple-o is not a variable,
    # it is an literal, which needs to have a distinctive suffix to
    # avoid to pretend that graphs are "linked" by a literal (which is not the case)
    variable = set()
    for s, p, o in sorted(triples):
        if p == ":instance":
            variable.add(s)

    #print("variables", sorted(variable))
    for i, (s, p, o) in enumerate(sorted(triples)):
        #if p == ":instance":
        #    continue
        if o not in variable or p == ":instance":
            o += "##%d" % i

        #print("SSSS triple", s, p, o)
        subgraphs.append(set([s, o]))

    ignore_sgs = set()
    join = 0
    if len(subgraphs) > 1:
        while True:
            modified = False
            i = 0
            while i < len(subgraphs) - 1:
                #print("i", i)
                if i in ignore_sgs:
                    i += 1
                    continue
                j = i + 1
                while j < len(subgraphs):
                    #print("j", j)
                    #print("iii", len(subgraphs), ignore_sgs)
                    if j in ignore_sgs:
                        j += 1
                        continue

                    join += 1
                    #print("join??", join, subgraphs[i], subgraphs[j])
                    if subgraphs[i].intersection(subgraphs[j]):
                        #print("yes")
                        subgraphs[i].update(subgraphs[j])
                        ignore_sgs.add(j)
                        modified = True
                        j += 1
                    j += 1
                i += 1
            #print("EEEE", modified, ignore_sgs)

            if not modified:
                #print("ende")
                break
            #sglen = len(ignore_sgs)

    finalsgs = []
    for i, sg in enumerate(subgraphs):
        if i not in ignore_sgs:
            #print("TTTT", sg)
            finalsgs.append(sg)
    return finalsgs


if __name__ == "__main__":
    tr = [
        ("a3", "p", "a4"),
        ("A", "p", "B"),
        ("D", "p", "E"),
        ("G", "p", "H"),
        ("G", "p", "I"),
        ("E", "p", "F"),
        ("B", "p", "C"),
        ("G", "p", "A"),
        ("AA", "p", "BB"),
        ("CC", "p", "DD"),

        ("AA", "p", "B"),
        ("DD", "p", "EE"),
        ("FF", "p", "GG"),
        ("GG", "p", "F"),

        ("a1", "p", "a2"),
        ("a1", "p", "a3"),
        ("EE", "p", "a4"),
        ]

    tr2 = [
        ("i", ":instance", "ii"),
        ("k", ":instance", "know-01"),
        ("k", ":ARG0", "i"),
        ("k", ":polarity", "-"),
        ("o", ":instance", "open-01"),
        ("o", ":ARG1", "r"),
        ("o", ":polarity", "-"),
        ("r", ":instance", "restaurant"),
        ("k", ":ARG0", "o"),
        ]

    tr3 = [
        ('a', ':instance', 'and'),
        ('a', ':op1', 'g'),
        ('a', ':op2', 'g2'),
        ('g', ':instance', 'guess-01'),
        ('g', ':ARG0', 'i'),
        ('i', ':instance', 'i'),
        ('g2', ':instance', 'get-through-12'),
        ('g2', ':polarity', '-'),
        ('g2', ':ARG0', 'i'),
        ('g2', ':degree', 'za2'),
        ('za2', ':instance', 'at-all'),
        ('i3', ':instance', 'i'),
        ]

    tr4 = [
        ('a', ':instance', 'and'),
        ('e', ':instance', 'experience-01'),
        ('a', ':op1', 'e'),
        ('r', ':instance', 'research-institute'),
        ('e', ':ARG0', 'r'),
        ('n', ':instance', 'name'),
        ('r', ':name', 'n'),
        ('n', ':op1', '"Nanjing"'),
        ('n', ':op2', '"Zijin"'),
        ('n', ':op3', '"Mountain"'),
        ('a2', ':instance', 'and'),
        ('e', ':ARG1', 'a2'),
        ('o', ':instance', 'observe-01'),
        ('a2', ':op1', 'o'),
        ('a3', ':instance', 'and'),
        ('o', ':ARG1', 'a3'),
        ('K', ':instance', 'KOMET'),
        ('a3', ':op1', 'K'),
        ('p', ':instance', 'planetoid'),
        ('a3', ':op2', 'p'),
        ('r2', ':instance', 'research-01'),
        ('a2', ':op2', 'r2'),
        ('r2', ':ARG1', 'a3'),
        ('m', ':instance', 'more-than'),
        ('e', ':duration', 'm'),
        ('t', ':instance', 'temporal-quantity'),
        ('m', ':op1', 't'),
        ('t', ':quant', '40'),
        ('c', ':instance', 'century'),
        ('t', ':unit', 'c'),
        ('o2', ':instance', 'organization'),
        ('a', ':op2', 'o2'),
        ('o3', ':instance', 'only'),
        ('o2', ':mod', 'o3'),
        ('c2', ':instance', 'country'),
        ('o2', ':location', 'c2'),
        ('n2', ':instance', 'name'),
        ('c2', ':name', 'n2'),
        ('n2', ':op1', '"China"'),
        ('b', ':instance', 'bureau'),
        ('o2', ':domain', 'b'),
        ('r3', ':instance', 'research-01'),
        ('b', ':mod', 'r3'),
        ('p2', ':instance', 'planet'),
        ('r3', ':ARG1', 'p2'),
        ('r4', ':instance', 'research-01'),
        ('b', ':poss_research-institute', 'r4'),
        ('ii', ':instance', 'issue-02'),
        ('r4', ':ARG1', 'ii'),
        ('c3', ':instance', 'collide-01'),
        ('ii', ':ARG0', 'c3'),
        ('b2', ':instance', 'body'),
        ('c3', ':ARG1', 'b2'),
        ('b3', ':instance', 'blue'),
        ('b2', ':mod', 'b3'),
        ('l', ':instance', 'long-03'),
        ('r4', ':ARG1-of', 'l'),
        ('b4', ':instance', 'begin-01'),
        ('a', ':op3', 'b4'),
        ('b4', ':ARG0', 'b'),
        ('r5', ':instance', 'research-01'),
        ('b4', ':ARG1', 'r5'),
        ('r5', ':ARG0', 'b'),
        ('r5', ':ARG1', 'ii'),
        ('s', ':instance', 'since'),
        ('b4', ':time', 's'),
        ('d', ':instance', 'date-entity'),
        ('s', ':op1', 'd'),
        ('d', ':year', '1988'),
        ('a4', ':instance', 'also'),
        ('b4', ':mod', 'a4')]
    #c1 = CheckGraph1(tr)

    print("==========")
    #c1 = CheckGraph(tr)
    for x in findsubgraphs(tr4):
        print(sorted(x))

    #import penman
    #pm = penman.encode(penman.Graph(tr3))
