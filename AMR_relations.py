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

# reads list of valid relations (or list of concepts) in AMR 

class Relations:
    def __init__(self, relfn, isconceptlist=False):
        self.isconceptlist = isconceptlist
        self.relations = set() # :ARG0, :mod, ...

        if relfn:
            ifp = open(relfn)
            if not isconceptlist:
                self.relations.add(":instance")
            for line in ifp:
                line = line.strip()
                if not line or line[0] == "#":
                    continue
                self.relations.add(line)

    def validate(self, triples):
        # return ARG relations which ar note defined for the given concept
        errors = []
        if self.relations:
            for s,p,o in triples:
                if not self.isconceptlist:
                    if p not in self.relations:
                        errors.append("invalid relation '%s'" % (p))
                else:
                    if p == ":instance" and o not in self.relations:
                        errors.append("invalid concept '%s'" % (o))
        else:
            # no messages because no data to validate on
            pass
        return errors


if __name__ == "__main__":

    # grep -h : ~/SemanticData/AMR/amr3/amr_annotation_3.0/data/amrs/split/training/amr-release-3.0-amrs-training-*txt | grep -v "#" | perl -ne "s/ +/\n/g; print" | grep ^: | sort -u  > relations.txt

    pd = Relations("relations.txt")
    #for c in pd.concepts:
    #    print(c)
    #    for a in pd.concepts[c]:
    #        print("   %s: %s" % (a, pd.concepts[c][a]))
    tr = [("z0",	":instance",	"bear-02"),
          ("z1",	":instance",	"person"),
          ("z2",	":instance",	"name"),
          ("z3",	":instance",	"city"),
          ("z4",	":instance",	"name"),
          ("z1",	":wiki",	"Q156586"),
          ("z4",	":op1",	"London"),
          ("z3",	":wiki",	"Q84"),
          ("z0",	":ARG1",	"z1"),
          ("z1",	":name",	"z2"),
          ("z0",	":location",	"z3"),
          ("z3",	":name",	"z4")]
    print(pd.validate(tr))

