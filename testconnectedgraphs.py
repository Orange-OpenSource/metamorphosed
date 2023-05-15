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



import sys

import penman
import amrdoc
import graph


def countsegs(trs, deleted):
    print("--------------------------------")
    segments = graph.findsubgraphs(trs)
    #print(segments)
    if len(segments) == 1:
        for tr in deleted:
            print("DEL", tr)
        #for tr in trs:
        #    print(tr)

        pm = penman.encode(penman.Graph(trs))
        print(pm)
    else:
        print("SEGS", len(segments))
        #pm = penman.encode(penman.Graph(trs))
    

ad = amrdoc.AMRdoc(sys.argv[1])



for sent in ad.sentences:
    #print (sent.amr)
    print("*****",sent.text)
    g = penman.decode(sent.amr)
    trs = []
    for s,p,o in g.triples:
        if not s:
            continue
        trs.append((s,p,o))

    if trs:
        #print(trs)
        countsegs(trs, deleted=[])

        for x in range(len(trs)):
            trs2 = []
            #if trs[x][1] == ":instance":
            #    continue
            #if trs[x][1] != ":snt1":
            #    continue
            for i,tr in enumerate(trs):
                if i != x:
                    trs2.append(tr)
            countsegs(trs2, deleted=[trs[x]])

    #break

