#!/usr/bin/env python3

import sys

import penman
import rdflib
import metamorphosed.findsubgraph as findsubgraph
import graph as AMRgraph


def replace(graph, subgraph, replgraph, gid=None, debug=False):
    sg = findsubgraph.SubGraphRDF(subgraph)
    bindings = sg.cmp(graph)

    #if sg.parsedgraph:
    #    print("GGGG", sg.parsedgraph, sg.parsedgraph.top)

    #print("SSSS", sg.parsedsubgraph, sg.parsedsubgraph.top)
    #if debug:
    #    print("BINDINGS", bindings)
    if bindings:
        #todelete = set()
        top_to_use = None
        for b in bindings:
            for v in b:
                gvar = b[v].split("/")[-1]
                if debug:
                    print("SUBGRAPH <%s>" % v, "\tMAINGRAPH <%s>" % gvar, "<%s>" % sg.parsedsubgraph.top)

                vv = str(v) # v is an instance of RDF variable

                if vv == sg.parsedsubgraph.top:
                    top_to_use = gvar
                    #print("ttu", top_to_use)
                #if not v.startswith("wildcard"):
                #    todelete.add(gvar)
        # create this automatically from input
        # where contains the subgraph (to be deleted)
        # delete == where (?)
        # insert gets the new subgraph and must be linked to the rest):
        #   the top variable of the deleted graph must be the variable used in insert for the top of the new graph
        #   all other variables must be absent from initial graph
        # top is the top of the original graph, unless the top changes...
        query = """
delete {
  ?l2 <http://metamorphosed/instance> ?wildcard1 .
  ?k2 <http://metamorphosed/instance> <http://metamorphosed/uri/knot> .
  ?t2 <http://metamorphosed/instance> <http://metamorphosed/uri/tie-01> .
  ?t2 <http://metamorphosed/pred/location> ?l2 .
  ?t2 <http://metamorphosed/pred/ARG1> ?k2 .
    }
insert {
    ?l2 <http://metamorphosed/instance> ?wildcard1 .
    <http://metamorphosed/var/t> <http://metamorphosed/instance> <http://metamorphosed/uri/marry-01> .
    <http://metamorphosed/var/t> <http://metamorphosed/pred/location> ?l2 .
}
where {
  ?l2 <http://metamorphosed/instance> ?wildcard1 .
  ?k2 <http://metamorphosed/instance> <http://metamorphosed/uri/knot> .
  ?t2 <http://metamorphosed/instance> <http://metamorphosed/uri/tie-01> .
  ?t2 <http://metamorphosed/pred/location> ?l2 .
  ?t2 <http://metamorphosed/pred/ARG1> ?k2 .
}
"""
        existing_vars = sg.parsedgraph.variables()
        new_vars = {} # v-insert: newvar  # to avoid duplicates
        #print("QQQ", "\n  ".join(sg.sparqllines))

        parsedrepl = penman.decode(replgraph)
        wildcardcounter = 1
        insertsparql = []
        for s, p, o in parsedrepl.triples:
            if s in new_vars:
                s = new_vars[s]
            elif s == parsedrepl.top:
                s = "<http://metamorphosed/var/%s>" % top_to_use
            elif s[-1] == "+":
                if s[:-1] in new_vars:
                    s = new_vars[s[:-1]]
                else:
                    nw = "<http://metamorphosed/var/xx%d>" % len(new_vars)
                    new_vars[s[:-1]] = nw
                    s = nw
            else:
                s = "?%s" % s

            if o in new_vars:
                o = new_vars[o]
            elif o == "*":
                o = "?wildcard%d" % wildcardcounter
                wildcardcounter += 1
            elif o == parsedrepl.top:
                o = "<http://metamorphosed/var/%s>" % top_to_use

            elif o[-1] == "+":
                if o[:-1] in new_vars:
                    o = new_vars[o[:-1]]
                else:
                    nw = "<http://metamorphosed/var/xx%d>" % len(new_vars)
                    new_vars[o[:-1]] = nw
                    o = nw
            elif o in parsedrepl.variables():
                o = "?%s" % o
            else:
                o = "<http://metamorphosed/uri/%s>" % o

            if p == ":instance":
                p = "<http://metamorphosed/instance>"
            else:
                p = "<http://metamorphosed/pred/%s>" % p[1:] # get rid of colon
            #print("rrrrr %s %s %s ." % (s, p, o))
            insertsparql.append("%s %s %s ." % (s, p, o))
        #print("RRRR", parsedrepl.top)
        #print("SSSS", sg.parsedsubgraph.top)
        if debug:
            print("top_to_use", top_to_use)

        query = "delete {\n  %s\n}\ninsert {\n  %s\n}\nwhere {\n  %s\n}" % \
                ("\n  ".join(sg.sparqllines),
                 "\n  ".join(insertsparql),
                 "\n  ".join(sg.sparqllines))
        if debug:
            print("QUERY", query, sep="\n")
        qres = sg.rdfgraph.update(query)

        #print("EEEE", sg.rdfgraph.serialize(format="nt"))
        qres = sg.rdfgraph.query("""SELECT ?s ?p ?o WHERE { ?s ?p ?o }""")
        newtriples = []
        for row in qres:
            #print("RRR", row)
            if isinstance(row.o, rdflib.term.Literal):
                o = '"%s"' % str(row.o)
            else:
                o = row.o.split('/')[-1]

            #print(f"{row.s.split('/')[-1]} :{row.p.split('/')[-1].replace(':', '')} {o}")
            newtriples.append((row.s.split('/')[-1], ":" + row.p.split('/')[-1], o))
        #print("top", sg.parsedgraph.top)

        # order triples more or less as in the original graph
        order = {} # triple: position
        for tr in sg.parsedgraph.triples:
            order[tr] = len(order)

        #print("oooo", order)
        #print("mmmmm", newtriples)
        newtriples = sorted(newtriples, key=lambda x: order.get(x, 1000))
        #print("nnnnn", newtriples)

        try:
            npm = penman.encode(penman.Graph(newtriples, top=sg.parsedgraph.top))
            return npm
        except Exception as e:
            # disconnected graph?
            sgs = AMRgraph.findsubgraphs(newtriples)

            pms = []
            print("Disconnected graph (id: %s):" % gid, file=sys.stderr)
            for sg in sgs:
                ntriples = []

                for tr in newtriples:
                    if tr[0] in sg or (tr[2] in sg and tr[1] != ":instance"):
                        ntriples.append(tr)
                pm = penman.encode(penman.Graph(ntriples))
                print("Graph", pm, file=sys.stderr)
                pms.append(pm)
        #print(npm)

    return None


if __name__ == "__main__":
    g3 = """(p / possible-01
     :ARG1 (t / tie-01
            :ARG1 (k / knot)
            :location (l / location
                         :quant 14
                         :mod (e / exotic)
                         :ARG1-of (d / differ-02)))
      :time (n / now))"""
    # in sg3 and rg3: identical variables must be used if instances correspond
    sg3 = """(t2 / tie-01
            :ARG1 (k2 / knot)
            :location (l2 / *))"""
    rg3 = """(t2 / marry-01
            :location (l2 / *))"""
    npm = replace(g3, sg3, rg3)
    print(npm)
