#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2025, Orange
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

# read standard AMR format and produce UMR format (notably for alignments)

import sys
import metamorphosed.amrdoc as amrdoc

import penman

class AMR2UMR:
    def __init__(self, infile): #, outfile):
        adoc = amrdoc.AMRdoc(infile)

        for ct, sent in enumerate(adoc.sentences, 1):
            # read id, sentence and AMR
            # extract alignments if present
            # rename variables

            
            print("#" * 80)
            print("# meta-info :: sent_id =", sent.id)
            print("# :: snt%d" % ct)
            if sent.tokens:
                print("Index:", "\t".join([str(x+1) for x in range(len(sent.tokens))]))
                print("Words:", "\t".join(sent.tokens))
            elif sent.text:
                print("Index:", "\t".join([str(x+1) for x in range(len(sent.text.split()))]))
                print("Words:", "\t".join(sent.text.split()))
            print("Sentence:", sent.text)
            amr, alignments = self.umrise(ct, sent.amr)
            
            print("# sentence level graph:")
            print(amr)
            print("\n")
            
            print("# alignment:")
            for k, vv in alignments.items():
                if "-" in k:
                    # RoleAlignments not available in UMR
                    print("#", end="")    
                print("%s: " % k, end="")
                print(", ".join(["%d-%d" % (x[0], x[1]) for x in vv]))
            print("\n")
            
            print("# document level annotation:")
            print("\n")

    def umrise(self, nr, pm):
        pg = penman.decode(pm)

        newvars = {} # old: new
        newtriples = []
        for s, p, o in pg.triples:
            if s in pg.variables():
                s2 = "s%d%s" % (nr, s)
                newvars[s] = s2
                s = s2
            if p != ":instance" and o in pg.variables():
                o2 = "s%d%s" % (nr, o)
                newvars[o] = o2
                o = o2
            newtriples.append((s, p, o))

        alignments = {} # var: [(from, to), ...]
        for tr,eds in pg.epidata.items():
            s2 = newvars.get(tr[0], tr[0])
            o2 = newvars.get(tr[2], tr[2])
            #print(tr)
            for ed in eds:
                if isinstance(ed, penman.surface.AlignmentMarker):
                    #print("  ", ed, ed.mode, ed.indices)
                    if ed.mode == 1: # RoleAlignment
                        edge = s2 + "-" + o2
                        for ix in ed.indices:
                            if edge not in alignments:
                                alignments[edge] = [(ix, ix)]
                            else:
                                alignments[edge].append((ix, ix))
                    else: # Alignment:
                        for ix in ed.indices:
                            if s2 not in alignments:
                                alignments[s2] = [(ix, ix)]
                            else:
                                alignments[s2].append((ix, ix))

        return penman.encode(penman.Graph(newtriples), indent=4), alignments

if __name__ == "__main__":
    a2u = AMR2UMR(sys.argv[1])
