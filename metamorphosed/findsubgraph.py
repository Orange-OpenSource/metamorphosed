#!/usr/bin/env python3

# conda activate graph

import json
import re

import penman

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import XSD


ISINT = re.compile(r"^[+-]?[0-9]+$")
ISFLOAT = re.compile(r"^[+-]?[0-9]+\.[0-9]+$")


class SubGraphRDF:
    def __init__(self, subgraph):
        self.prefix = "http://metamorphosed"

        self.subgraph = subgraph
        if subgraph:
            self.query_triples, self.sg_conceptset, _, self.parsedsubgraph = self.amr2rdf(self.subgraph)

    def cmp(self, graph):
        debug = False
        self.graph = graph
        self.parsedgraph = None

        #print("QT", self.query_triples.serialize(format="nt"))
        for sc_c in self.sg_conceptset:
            if sc_c != "*" and sc_c not in self.graph:
                if debug:
                    print("MISSING CONCEPTS <%s>" % sc_c)
                return None

        self.rdfgraph, conceptset, self.instances, self.parsedgraph = self.amr2rdf(self.graph)
        #print("GRAPH", self.rdfgraph.serialize(format="nt"))

        #if not sg_conceptset.issubset(conceptset):
        #    print("MISSING CONCEPTS")
        #    return None
        #print(dir(rdfgraph))

        self.querytext = self.query(self.query_triples)
        if debug:
            print("QUERY", self.querytext)
        qres = self.rdfgraph.query(self.querytext)
        #print("ZZ", dir(qres),
        #      qres.bindings,
        #      qres.serialize("json"))

        if debug:
            print("BINDINGS:", json.dumps(qres.bindings, indent=2))
        return qres.bindings

    def amr2rdf(self, amr):
        # the graph is the RDF store, the subgraph the query
        # if the query returns something, the graph contains the subgraph
        if isinstance(amr, str):
            parsedgraph = penman.decode(amr)
            edges = parsedgraph.edges()
            attributes = parsedgraph.attributes()
            ginstances = parsedgraph.instances()
            origtriples = parsedgraph.triples
            variables = parsedgraph.variables()
            #for tr in parsedgraph.triples:
            #    print("triple", tr)
        else:
            parsedgraph = None
            edges = []
            ginstances = []
            attributes = []
            variables = set()
            for s, p, o in amr:
                if o == ":instances":
                    ginstances.append((s, p, o))
                    variables.add(s)
                elif o in variables:
                    edges.append((s, p, o))
                else:
                    attributes.append((s, p, o))
            origtriples = ginstances + edges + attributes
        #rdfgraph = Graph() # RDF Graph
        rdfgraph = Graph(store="Oxigraph") # much faster sparql queries
        debug = 1 == 0 #False

        triples = {} # s: [(p,o)]
        triples_inv = {} # o: [(p-of, s)]
        instances = {} # var: concept

        wildcardcounter = 1
        # transform the AMR into an RDF representation
        #print("eeee", origtriples)
        for s, p, o in origtriples:
            if p == ":instances":
                CURTYPE = "i"
            elif o in variables:
                CURTYPE = "e"
            else:
                CURTYPE = "a"

        if 1:
            #print("triple", CURTYPE, s,p,o)
            #if CURTYPE == "e":
            for s, p, o in edges:
                if debug:
                    print("EDGE", s, p, o)

                if s not in triples:
                    triples[s] = [(p, o)]
                else:
                    triples[s].append((p, o))

                if o not in triples_inv:
                    triples_inv[o] = [(p + "-of", s)]
                else:
                    triples_inv[o].append((p + "-of", s))

                subj = URIRef(self.prefix + "/var/" + s)
                if p == ":*":
                    pred = URIRef(self.prefix + "/var/wildcard%d" % wildcardcounter)
                    wildcardcounter += 1

                else:
                    pred = URIRef(self.prefix + "/pred/" + p[1:])
                obj = URIRef(self.prefix + "/var/" + o)
                rdfgraph.add((subj, pred, obj))

            #elif CURTYPE == "i":
            for s, p, o in ginstances:
                if debug:
                    print("INST", s, p, o)
                if not s or not o:
                    continue

                subj = URIRef(self.prefix + "/var/" + s)
                pred = URIRef(self.prefix + "/instance")
                if o == "*":
                    obj = URIRef(self.prefix + "/var/wildcard%d" % wildcardcounter)
                    wildcardcounter += 1
                else:
                    obj = URIRef(self.prefix + "/uri/" + o)
                rdfgraph.add((subj, pred, obj))
                instances[s] = o

            #else: #if CURTYPE == "a":
            for s, p, o in attributes:
                if debug:
                    print("ATTR", s, p, o)
                if not s or not o:
                    continue

                if s not in triples:
                    triples[s] = [(p, o)]
                else:
                    triples[s].append((p, o))

                if o not in triples_inv:
                    triples_inv[o] = [(p + "-of", s)]
                else:
                    triples_inv[o].append((p + "-of", s))

                subj = URIRef(self.prefix + "/var/" + s)
                pred = URIRef(self.prefix + "/pred/" + p[1:])
                if o[0] == '"':
                    obj = Literal(o[1:-1], datatype=XSD.string)
                elif o[0] == '-':
                    obj = Literal(o, datatype=XSD.string)
                else:
                    if ISFLOAT.match(o):
                        obj = Literal(o, datatype=XSD.float)
                    if ISINT.match(o):
                        obj = Literal(o, datatype=XSD.int)
                    else:
                        obj = URIRef(self.prefix + "/uri/" + o)
                rdfgraph.add((subj, pred, obj))

        conceptset = set(instances.values())
        #print("CONCEPTLIST", conceptset)

        if debug:
            print(rdfgraph.serialize(format="nt"))

        return rdfgraph, conceptset, ginstances, parsedgraph

    def query(self, query_triples):
        self.sparqllines = []
        varlen = len(self.prefix + "/var/")

        for stmt in query_triples:
            #print("STMT", stmt)
            s = None
            p = "<%s>" % stmt[1]
            o = "<%s>" % stmt[2]

            # variable in subject position
            if stmt[0].startswith(self.prefix + "/var/"):
                s = "?%s" % stmt[0][varlen:]

            # variable in predicate position
            if stmt[1].startswith(self.prefix + "/var/"):
                p = "?%s" % stmt[1][varlen:]

            # variable in object position
            if isinstance(stmt[2], Literal):
                o = '"%s"' % stmt[2]
            elif stmt[2].startswith(self.prefix + "/var/"):
                o = "?%s" % stmt[2][varlen:]
            self.sparqllines.append("%s %s %s ." % (s, p, o))

        query = "select distinct * where {\n  %s\n}" % ("\n  ".join(self.sparqllines))
        #print(query)
        return query


if __name__ == "__main__":
    g = """(o / obvious-01
    :ARG1 (a / and
      :op1 (l / leave-17
        :polarity -
        :ARG1 (o2 / or
          :op1 (p / problem
            :topic (s2 / society))
          :op2 (p3 / problem
            :topic (p2 / politics))))
      :op2 (l2 / leave-17
         :polarity -
                     :ARG1 (s / sequela
                              :ARG0-of (c / cause-01
                                          :ARG1 (h / headache
                                                   :beneficiary (g / generation
                                                                   :time (a2 / after
                                                                             :op1 t))))))
            :time (t / then)))"""

    sg = """(zo2 / or
                              :op1 (zp / problem
                                      :topic (zs2 / society))
                              :op2 (zp3 / problem
                                       :topic (zp2 / politics))) """

    g1 = """(a / and
    :op1 (s / see-01
      :polarity -
      :quant 5000
      :ARG0 (c / cat
        :name (n1 / name :op1 "chat")     )
      :ARG1 (m / mouse
        :name (n / name :op1 "souris")        )
      :location (k / kitchen))
    :op2 (s2 / see-01
      :polarity -
      :ARG0 (d / dog)
      :ARG1 c))"""

    sg1 = """(zs / see-01
    :polarity -
    :ARG0 (zc / *)
    :location (k / kitchen)
    )
    """

    g2 = """(k / murder-01
   :ARG0 (a / amr-unknown)
   :ARG1 (p / person
            :name (n / name
                     :op1 "JFK")
            :wiki "Q9696"))"""

    sg2 = "( x / murder-01 :ARG1 ( k / person))"
    sg2 = "( x / murder-01 :* ( k / person))"
    #sg2 = "( x / murder-01 :ARG1 ( k / *))"

    g3 = """(p / possible-01
     :ARG1 (t / tie-01
            :ARG1 (k / knot)
            :location (l / location
                         :quant 14
                         :mod (e / exotic)
                         :ARG1-of (d / differ-02)))
      :time (n / now))"""
    sg3 = """(t2 / tie-01
            :ARG1 (k2 / knot)
            :location (l2 / *))"""

    # pg = penman.decode(g1)
    # g1 = list(pg.triples)

    # (g, sg), (g1, sg1),  #(g2, sg2),
    for (full, sub) in [(g3, sg3)]:
        print("FULL", full, "SUB", sub, sep="\n")
        sg = SubGraphRDF(sub)
        bindings = sg.cmp(full)
        if bindings:
            for b in bindings:
                for v in b:
                    gvar = b[v].split("/")[-1]
                    print("SUBGRAPH", v, "\tMAINGRAPH", gvar)
