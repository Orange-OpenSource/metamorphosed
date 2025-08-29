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
#
# SPDX-License-Identifier: BSD-3-Clause
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke

# version 1.8 as of 29th August 2025

# read .xml and if present .json file (if absent, AMRfiles must be given) and display a block of sentences with coreferences (from XML)
# allow adding new coreferences and deleting incorrect ones

import collections
import os
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

import amrs2dot


VERSION = "1.8"

# hurts E402. TODO change somehow
parent = pathlib.Path(os.path.abspath(__file__)).parent.parent
sys.path.append(str(parent))
import metamorphosed.amrdoc as amrdoc

# TODO:
#   annotate aucomatically all instances of an given context which have the same :wiki relation


class Sentence:
    def __init__(self, sid, order, post, speaker, su):
        self.AMRsentence = None # AMRsentence object
        self.sid = sid
        self.order = order
        self.post = post
        self.speaker = speaker
        self.su = su

    def __repr__(self):
        return "%s: %s" % (self.sid, self.AMRsentence.text)

    def xml(self, parent):
        a = ET.SubElement(parent, "amr")
        a.attrib["id"] = self.sid
        a.attrib["order"] = self.order
        a.attrib["post"] = self.post
        a.attrib["speaker"] = self.speaker
        a.attrib["su"] = self.su
        return a


class ImplicitRole:
    def __init__(self, argument, sid, parentconcept, parentvariable):
        self.argument = argument
        self.sid = sid
        self.parentconcept = parentconcept
        self.parentvariable = parentvariable

    def __repr__(self):
        return '<implicitrole argument="%s" id="%s" parentconcept="%s" parentvariable="%s"/>' % \
               (self.argument, self.sid, self.parentconcept, self.parentvariable)

    def xml(self, parent):
        ir = ET.SubElement(parent, "implicitrole")
        ir.attrib["argument"] = self.argument
        ir.attrib["id"] = self.sid
        ir.attrib["parentconcept"] = self.parentconcept
        ir.attrib["parentvariable"] = self.parentvariable


CID = re.compile("([A-Za-z]+-)([0-9]+)")


class Partwhole:
    def __init__(self, bid, xmlparent):
        mo = CID.match(bid)
        if mo:
            self.prefix = mo.group(1)  # rel ou singleton
            self.bid = int(mo.group(2))
        else:
            self.bid = bid
            self.prefix = ""

        self.wholeid = None
        self.partids = []
        for x in xmlparent:
            if x.tag == "whole":
                if self.wholeid:
                    print("ERROR: more than 'whole' tag in partwhole %s" % bid, file=sys.stderr)
                self.wholeid = x.attrib["id"]
            elif x.tag == "part":
                self.partids.append(x.attrib["id"])

    def xml(self, parent):
        m = ET.SubElement(parent, "partwhole")
        m.attrib["relationid"] = "%s%s" % (self.prefix, self.bid)
        if self.wholeid:
            w = ET.SubElement(m, "whole")
            w.attrib["id"] = self.wholeid
        for p in self.partids:
            w = ET.SubElement(m, "part")
            w.attrib["id"] = p


class Setmember:
    def __init__(self, bid, xmlparent):
        mo = CID.match(bid)
        if mo:
            self.prefix = mo.group(1)  # rel ou singleton
            self.bid = int(mo.group(2))
        else:
            self.bid = bid
            self.prefix = ""

        self.superset = None
        self.members = []
        for x in xmlparent:
            if x.tag == "superset":
                if self.superset:
                    print("ERROR: more than 'superset' tag in setmember %s" % bid, file=sys.stderr)
                self.superset = x.attrib["id"]
            elif x.tag == "member":
                self.members.append(x.attrib["id"])

    def xml(self, parent):
        m = ET.SubElement(parent, "setmember")
        m.attrib["relationid"] = "%s%s" % (self.prefix, self.bid)
        if self.superset:
            w = ET.SubElement(m, "superset")
            w.attrib["id"] = self.superset
        for p in self.members:
            w = ET.SubElement(m, "member")
            w.attrib["id"] = p


class Mention:
    def __init__(self, concept, sid, variable, text):
        self.concept = concept
        self.sid = sid
        self.variable = variable
        self.text = text

    def __repr__(self):
        return '<mention concept="%s" id="%s" variable="%s"/>' % (self.concept, self.sid, self.variable)

    def xml(self, parent):
        m = ET.SubElement(parent, "mention")
        m.attrib["concept"] = self.concept
        m.attrib["id"] = self.sid
        m.attrib["variable"] = self.variable
        if self.text:
            m.text = self.text
        return m


class IdentChain:
    def __init__(self, cid, xmlparent=None):
        mo = CID.match(cid)
        if mo:
            self.prefix = mo.group(1)  # rel ou singleton
            self.cid = int(mo.group(2))
        else:
            self.cid = cid
            self.prefix = ""
        self.mentions = []
        self.implicitroles = []
        if xmlparent is not None:
            # parsing data, if absent, creating new chain
            for x in xmlparent:
                if x.tag == "mention":
                    m = Mention(x.attrib["concept"], x.attrib["id"], x.attrib["variable"], x.text)
                    self.mentions.append(m)
                elif x.tag == "implicitrole":
                    ir = ImplicitRole(x.attrib["argument"], x.attrib["id"], x.attrib["parentconcept"], x.attrib["parentvariable"])
                    self.implicitroles.append(ir)

    def __repr__(self):
        res = ["identchain %s%s" % (self.prefix, self.cid)]
        for m in self.mentions:
            res.append(str(m))
        for m in self.implicitroles:
            res.append(str(m))
        return "\n\t".join(res)

    def xml(self, parent, newcid=None):
        ic = ET.SubElement(parent, "identchain")
        #print("ZZZ",newcid, self.prefix, self.cid)
        if newcid:
            # when writing the XML file, we need rel-0 to rel-n without missing number
            if not self.prefix:
                pref = "rel-"
            else:
                pref = self.prefix
            ic.attrib["relationid"] = "%s%s" % (pref, newcid)
        else:
            ic.attrib["relationid"] = self.prefix + str(self.cid)
        for mention in self.mentions:
            mention.xml(ic)
        for implicitrole in self.implicitroles:
            implicitrole.xml(ic)

        return ic


# contains a XML file
class SentenceGroup:
    def __init__(self, xmlfile, allamrsentences):
        self.xmlfile = xmlfile

        self.sids = collections.OrderedDict() # id: Sentence (contains also PENMAN)
        self.sid2sentpos = {} # sid: position of sentence in group (starts with 0)
        self.sentpos2sid = {}

        #self.chaines = collections.OrderedDict() # id: Chain
        self.chaines = []

        self.singletons = []
        self.bridging = []

        #self.other = [] # for the time being singletons and bridging
        self.comment = None
        tree = ET.parse(self.xmlfile)
        self.svgs = {} # sentpos: last svg graph # needed to know whether or not we have to call dot
        self.scaling = 1

        for child in tree.getroot():
            if child.tag == "comment":
                self.comment = child.text
            elif child.tag == "sentences":
                self.annotator = child.attrib["annotator"]
                self.docid = child.attrib["docid"]
                self.end = child.attrib["end"]
                self.site = child.attrib["site"]
                self.sourcetype = child.attrib["sourcetype"]
                self.start = child.attrib["start"]
                self.threadid = child.attrib["threadid"]

                for amr in child:
                    sentence = Sentence(amr.attrib["id"],
                                        amr.attrib["order"],
                                        amr.attrib["post"],
                                        amr.attrib["speaker"],
                                        amr.attrib["su"]
                                        )

                    sentence.AMRsentence = allamrsentences[sentence.sid]
                    self.sids[sentence.sid] = sentence

            elif child.tag == "relations":
                for rel in child:
                    if rel.tag == "identity":
                        for identchain in rel:
                            ic = IdentChain(identchain.attrib["relationid"], identchain)
                            #self.chaines[ic.cid] = ic
                            self.chaines.append(ic)
                    elif rel.tag == "singletons":
                        for identchain in rel:
                            ic = IdentChain(identchain.attrib["relationid"], identchain)
                            #self.chaines[ic.cid] = ic
                            self.singletons.append(ic)
                    elif rel.tag == "bridging":
                        for br in rel:
                            if br.tag == "partwhole":
                                pp = Partwhole(br.attrib["relationid"], br)
                                self.bridging.append(pp)
                            elif br.tag == "setmember":
                                pp = Setmember(br.attrib["relationid"], br)
                                self.bridging.append(pp)
                            else:
                                print("Error: invalid tag '%s'" % br.tag, file=sys.stderr)
                    else:
                        print("Error: invalid tag '%s'" % rel.tag, file=sys.stderr)
                        #self.other.append(rel)

        for sp, sid in enumerate(self.sids):
            self.sid2sentpos[sid] = sp
            self.sentpos2sid[sp] = sid
        #self.addtexttomention()

#    def addtexttomention(self):
#        # add :wiki relation text to Mention if absent (only needed to complete XML files without, created with earlier versions of corefeditor
#        modified = False
#        for i,chain in enumerate(self.chaines):
#            for mention in chain.mentions:
#                if not mention.text:
#                    amrsent = self.sids[mention.sid].AMRsentence
#                    wiki = amrsent.getwikilink(mention.variable)
#                    #print("mention", wiki)
#                    if wiki and wiki != "-":
#                        mention.text = wiki
#                        modified = True
#        return modified

    def getchains(self):
        # return a list of coref chains
        sentpos = {} # sentid: pos in sids
        implicitroles = {} # sentpos: [chainid, parentvar, ARG]
        for pos, sid in enumerate(self.sids):
            sentpos[sid] = pos
        res = []
        #for cid in self.chaines:
        for cid, chain in enumerate(self.chaines):
            #print("CID", cid)
            newchain = [] # sentpos: var
            #ic = self.chaines[cid]
            for mention in chain.mentions: #ic.mentions:
                pos = sentpos[mention.sid]
                #print("wwmention", pos, mention)
                newchain.append((pos, mention.variable))

            for ir in chain.implicitroles:
                pos = sentpos[ir.sid]
                #print("wwchain", pos, ir)
                if pos not in implicitroles:
                    implicitroles[pos] = []
                implicitroles[pos].append((cid, ir.parentvariable, ir.argument))
            #if len(newchain) > 1:
            res.append(newchain)
        return res, implicitroles

    def addtochain(self, instancefrom, instanceto):
        # we detect the corefchain of instancefrom
        # if any, add instanceto to this chain
        # if no chain, create new chain and add both instances to it
        modified = False
        elems = instancefrom.split("_")
        from_sentpos = int(elems[1])
        from_var = elems[2]

        elems = instanceto.split("_")
        to_sentpos = int(elems[1])
        to_var = elems[2]

        #print("First  ", from_sentpos, from_var)
        #print("Second ", to_sentpos, to_var)

        # find chaines for both instances (and delete instanceto from its current chain
        from_chain = -1
        to_chain = -1
        to_mention = None

        for i, chain in enumerate(self.chaines):
            #print("CHAIN", i, "length", len(chain.mentions))
            for mention in chain.mentions:
                #print(" MENTION", mention)
                sentpos = self.sid2sentpos[mention.sid]
                if sentpos == from_sentpos and mention.variable == from_var:
                    #print(" !!found from", sentpos, from_var)
                    from_chain = i
                if sentpos == to_sentpos and mention.variable == to_var:
                    #print(" !!found to", sentpos, to_var)
                    to_chain = i
                    to_mention = mention

            if from_chain >= 0 and to_chain >= 0:
                break

        if from_chain >= 0:
            # first clicked node is in a chain
            if from_sentpos == to_sentpos and from_var == to_var:
                # two clicks on the same instance: delete it from its chain
                self.chaines[to_chain].mentions.remove(to_mention)
                if from_sentpos in self.svgs:
                    # delete svg, because we have to redo it
                    # del self.svgs[from_sentpos]
                    # delete all svgs, because renumbering of chaines may have changed everywhere
                    self.svgs = {}

                modified = True
            elif to_chain != from_chain:
                # second clicked node added to the chain of the first
                amrsent = self.sids[self.sentpos2sid[to_sentpos]].AMRsentence
                concept = amrsent.getconceptlist().get(to_var, "_unspec_")
                wiki = amrsent.getwikilink(to_var)

                m = Mention(concept, self.sentpos2sid[to_sentpos], to_var, wiki)
                self.chaines[from_chain].mentions.append(m)
                modified = True
                if to_sentpos in self.svgs:
                    del self.svgs[to_sentpos]

                #chain.mentions[from_chain].append((to_sentpos, to_var))
                if to_chain > 0:
                    # delete toinstance from its old chain
                    self.chaines[to_chain].mentions.remove(to_mention)
                    if from_sentpos in self.svgs:
                        del self.svgs[from_sentpos]

        else:
            # first node is not in a chain: new chain
            if from_sentpos != to_sentpos or from_var != to_var:
                # we clicked on different instances
                # create new Chain
                ic = self.newchain()

                amrsentfrom = self.sids[self.sentpos2sid[from_sentpos]].AMRsentence
                concept = amrsentfrom.getconceptlist().get(from_var, "_unspec_")
                wiki = amrsentfrom.getwikilink(from_var)
                m1 = Mention(concept, self.sentpos2sid[from_sentpos], from_var, wiki)
                #print("BBB", concept, wiki)

                amrsentto = self.sids[self.sentpos2sid[to_sentpos]].AMRsentence
                concept = amrsentto.getconceptlist().get(to_var, "_unspec_")
                wiki = amrsentto.getwikilink(to_var)
                m2 = Mention(concept, self.sentpos2sid[to_sentpos], to_var, wiki)
                #print("CCC", concept, wiki)
                ic.mentions.append(m1)
                ic.mentions.append(m2)
                modified = True
                if from_sentpos in self.svgs:
                    del self.svgs[from_sentpos]
                if to_sentpos in self.svgs:
                    del self.svgs[to_sentpos]

        #print("\nAFTER OP")
        newchains = []
        for i, chain in enumerate(self.chaines):
            if (len(chain.mentions) + len(chain.implicitroles)) < 2:
                # delete chain with only a single mention
                sentpos = self.sid2sentpos[chain.mentions[0].sid]
                if sentpos in self.svgs:
                    del self.svgs[sentpos]

                #print("DELETE", end=" ")
                modified = True
            else:
                newchains.append(chain)
            #print("ACHAIN", i, "length", len(chain.mentions))
            #for mention in chain.mentions:
            #    print(" AMENTION", mention)
            #for ir in chain.implicitroles:
            #    print(" AIMPLICR", ir)
        self.chaines = newchains
        return modified

    def newchain(self):
        cid = 0
        cids = []
        for chain in self.chaines:
            cids.append(chain.cid)

        #while "rel-%d" % cid in cids:
        while cid in cids:
            cid += 1
            continue
        cid = "rel-%d" % cid
        ic = IdentChain(cid, xmlparent=None)
        self.chaines.append(ic)
        return ic

    def __repr__(self):
        res = [self.docid]
        for so in self.sids.values():
            res.append(str(so))

        for ch in self.chaines: #.values():
            res.append(str(ch))

        for o in self.singletons:
            res.append(ET.tostring(o).decode("UTF-8"))
        for o in self.bridging:
            res.append(ET.tostring(o).decode("UTF-8"))
        #for o in self.other:
        #    #print("ww", type(o), dir(o))
        #    #print("zz", ET.tostring(o).decode("UTF-8"))
        #    res.append(ET.tostring(o).decode("UTF-8"))
        return "\n\t".join(res)

    def xml(self, ofp=None):
        # recreate XML for output
        doc = ET.Element("document")

        if self.comment:
            comment = ET.SubElement(doc, "comment")
            comment.text = self.comment
        sentences = ET.SubElement(doc, "sentences")
        sentences.attrib["annotator"] = self.annotator
        sentences.attrib["docid"] = self.docid
        sentences.attrib["end"] = self.end
        sentences.attrib["site"] = self.site
        sentences.attrib["sourcetype"] = self.sourcetype
        sentences.attrib["start"] = self.start
        sentences.attrib["threadid"] = self.threadid

        for amr in self.sids.values():
            amr.xml(sentences)

        relations = ET.SubElement(doc, "relations")

        identity = ET.SubElement(relations, "identity")
        last = 0
        for i, identchain in enumerate(sorted(self.chaines, key=lambda x: x.cid)):
            #identchain.xml(identity, i)
            identchain.xml(identity)
            last = i
        singletons = ET.SubElement(relations, "singletons")
        for i, identchain in enumerate(sorted(self.singletons, key=lambda x: x.cid), last + 1):
            #identchain.xml(singletons, i)
            identchain.xml(singletons)

        bridging = ET.SubElement(relations, "bridging")
        for i, br in enumerate(sorted(self.bridging, key=lambda x: x.bid), last + 1):
            #identchain.xml(singletons, i)
            br.xml(bridging)

        #for o in self.other:
        #    relations.append(o)

        #print(ET.tostring(doc).decode("UTF-8"))
        raw = ET.tostring(doc, encoding="utf-8")
        reparsed = minidom.parseString(raw)
        xmlstring = reparsed.toprettyxml(indent="  ").replace('<?xml version="1.0" ?>',
                                                              '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE msamr SYSTEM "msamr.dtd">\n',)

        if ofp:
            print(xmlstring, file=ofp)
        else:
            return xmlstring

#    def format(self, format="svg"):
#        # returns an SVG graph of all sentences
#        penmans = []
#        for amrid in self.sids:
#            #print(self.sids[amrid].amr, file=sys.stderr)
#            penmans.append("# ::id %s\n" % amrid + self.sids[amrid].AMRsentence.amr)
#        # transform internal identiychains in et list of [(sentpos, varname)] similarly to amr_coref
#        chains = self.getchains()
#        #print("CHAINS", chains)
#        a2 = amrs2dot.AMRs2dot(penmans, chains)
#        if format == "svg":
#            return a2.dot().decode("utf8")
#        else:
#            a2.dot(format="pdf")

    def multiformat(self, format="svg", showfrom=None, shownumber=None, scaling=1):
        # returns an list SVG graphs for all sentences
        penmans = []
        for amrid in self.sids:
            #print(self.sids[amrid].amr, file=sys.stderr)
            penmans.append("# ::id %s\n# ::snt %s\n%s" % (amrid, self.sids[amrid].AMRsentence.text, self.sids[amrid].AMRsentence.amr))

        # transform internal identiychains in et list of [(sentpos, varname)] similarly to amr_coref
        chains, implicitroles = self.getchains()
        #print("CHAINS", chains)
        #print("IRs   ", implicitroles)
        #implicitroles = self.getimplicittroles()

        if scaling != self.scaling:
            # new scaling, all SVGs must be recalculated
            self.svgs = {}
            self.scaling = scaling
        a2 = amrs2dot.AMRs2dot(penmans, chains, implicitroles, scaling)
        # put mentions and irs in a table to be displayed as
        # relid: sentpos: var/concept, ....

        table = {} # relid: [sentpos var/concept], .... (TODO suboptimal creating HTML code here ....)
        for cid, chain in enumerate(self.chaines):
            bgcolor, fgcolor = a2.chainid2col(cid)
            temp_table = []

            for mention in chain.mentions:
                sentpos = self.sid2sentpos[mention.sid]

                wiki = ""
                if mention.text:
                    wiki = " «%s»" % mention.text

                temp_table.append((sentpos, '<span class="chain" data="G_%s_%s" style="background-color:%s;color:%s"><b>%s</b>: %s / %s%s</span>' %
                                  (sentpos, mention.variable,
                                   bgcolor, fgcolor,
                                   sentpos + 1, mention.variable, mention.concept, wiki)))
            for ir in chain.implicitroles:
                sentpos = self.sid2sentpos[ir.sid]
                # TODO add class="chain" and data="I %s_%s" % sentpos,cid
                # for implicits: but we do not have a variable only the cid
                # this needs a change in addtochain() to take cid
                # from I_... and not var from G_...
                temp_table.append((sentpos, '<span class="chain" style="background-color:%s;color:%s"><b>%s</b>: <i>i%s / implicit</i></span>' %
                                  (bgcolor, fgcolor,
                                   sentpos + 1, ir.parentvariable)))
            temp_table.sort()
            table[cid] = [b for a, b in temp_table]

        #for x in table:
        #    print(x, table[x])

        # get the sentecence number and varaible of singletons to display them in the bridging section
        singletons = {} # bid: sentenceid, variable
        for ic in self.singletons:
            bid = ic.cid
            prefix = ic.prefix
            if ic.mentions:
                m = ic.mentions[0]
                sentpos = self.sid2sentpos[m.sid]
                singletons["%s%s" % (prefix, bid)] = (m.sid, sentpos + 1, m.variable, m.concept, None)
            elif ic.implicitroles:
                ir = ic.implicitroles[0]
                sentpos = self.sid2sentpos[ir.sid]
                singletons["%s%s" % (prefix, bid)] = (ir.sid, sentpos + 1, ir.parentvariable, ir.parentconcept, ir.argument)

        def getchainfromtable(relid, table, singletons):
            if relid in singletons:
                msid, sentpos, mvar, mconc, narg = singletons[relid]
                return '<span class="chain" style="background-color:#E8E8E8;">%s: %s / %s</span>' % (sentpos, mvar, mconc)

            elems = relid.split("-")
            if len(elems) != 2:
                return relid
            try:
                cid = int(elems[1])
                return " ".join(table[cid])
            except Exception:
                return relid

        bridgingtable = {}
        for bridge in self.bridging:
            bridgingtable[bridge.bid] = []
            if isinstance(bridge, Setmember):
                supersetid = bridge.superset
                #if supersetid in singletons:
                #    msid, sentpos, mvar, mconc, narg = singletons[supersetid]
                #    superset = "%s: %s / %s" % (sentpos, mvar, mconc)
                #else:
                superset = getchainfromtable(supersetid, table, singletons)
                bridgingtable[bridge.bid].append('<span class="bridgingtype">Superset: %s</span><br>members: ' % (superset))

                for m in bridge.members:
                    bridgingtable[bridge.bid].append(getchainfromtable(m, table, singletons))
                #bridgingtable[bridge.bid].append("</td></tr></table>")

            else:
                wholeid = bridge.wholeid
                #if wholeid in singletons:
                #    msid, sentpos, mvar, mconc, narg = singletons[wholeid]
                #    superset = "%s: %s / %s" % (sentpos, mvar, mconc)
                #else:
                whole = getchainfromtable(wholeid, table, singletons)
                bridgingtable[bridge.bid].append('<span class="bridgingtype">Whole: %s</span><br>parts: ' % (whole))
                for m in bridge.partids:
                    bridgingtable[bridge.bid].append(getchainfromtable(m, table, singletons))

        return a2.multidot(self.svgs, showfrom, shownumber), table, bridgingtable


class CorefEditor:
    def __init__(self, xmlfiles, #jsonfile=None,
                 amrfiles=None):
        #if not jsonfile and not amrfiles:
        #    raise Exception("Hey, I need either the jsonfile or amrfiles to find sentences")

        self.amrdocs = {} # fn: AMRdoc
        self.sids = collections.OrderedDict() # sid: AMRsentence

        #if amrfiles:
        for fn in amrfiles:
            fn = os.path.abspath(fn)
            ad = amrdoc.AMRdoc(fn)
            self.amrdocs[fn] = ad
            self.sids.update(ad.ids)
        #else:
        #    loadedfiles = set()
        #    ifp = open(jsonfile)
        #    jobj = json.load(ifp)
        #    for dico in jobj:
        #        if dico["file"] in loadedfiles:
        #            # avoid load a file twixe
        #            continue
        #        loadedfiles.add(dico["file"])
        #        ad = amrdoc.AMRdoc(dico["file"])
        #        self.amrdocs[dico["file"]] = ad
        #        self.sids.update(ad.ids)

        self.sentencegroups = collections.OrderedDict() # xmlfile: sgObj
        for xmlfile in xmlfiles:
            sg = SentenceGroup(xmlfile, self.sids)
            self.sentencegroups[xmlfile] = sg


if __name__ == "__main__":
    # ./corefeditor.py -x pp_001.xml -j pp_001.json
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", "-x", required=True, type=str, help="coreference xml file")
    #parser.add_argument("--json", "-j", type=str, help="json file corresponding to xml")
    parser.add_argument("amrfiles", nargs="+", help="AMR files which contain the indicated files")

    if len(sys.argv) < 2:
        parser.print_help()
    else:
        args = parser.parse_args()

        ce = CorefEditor(args.xml, #args.json,
                         args.amrfiles)
        ce.format(format="pdf")
