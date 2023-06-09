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
# Software Name: MetAMoRphosED AMR-Editor
# Author: Johannes Heinecke


import sys
import pytest
import json
import time

from server import AMR_Edit_Server


# run (pytest-6.2.3)
#   pytest unittests.py -vv -s
#  -s shows print statements in test
#  -k test_edit_modliteral (filters tests which do not match argument)

# see: https://flask.palletsprojects.com/en/2.1.x/testing/
#      https://stackoverflow.com/questions/17801300/how-to-run-a-method-before-all-tests-in-all-classes

# launched only once
@pytest.fixture(scope="session")
def app():
    #app = create_app()
    #app.config.update({
    #    "TESTING": True,
    #})
    #print("zzzzzzzzzzzzzzzzzzzz")
    aes = AMR_Edit_Server(4568,
                          "testamr.txt",
                          "propbank-frames/frames/",
                          "relations.txt",
                          "concepts.txt",
                          "constraints.yml",
                          False, # readonly
                          None, # author
                          "reification-table.txt"
                          )
    app = aes.app
    number_of_sentences = len(aes.aps)

    # other setup can go here

    yield app

    # clean up / reset resources here

# start server just for one test
@pytest.fixture()
def app_once():
    #app = create_app()
    #app.config.update({
    #    "TESTING": True,
    #})
    #print("zzzzzzzzzzzzzzzzzzzz")
    aes = AMR_Edit_Server(4568,
                          "testamr.txt",
                          "propbank-frames/frames/",
                          "relations.txt",
                          "constraints.yml",
                          False # readonly
                          )
    app = aes.app

    # other setup can go here

    yield app

    # clean up / reset resources here




@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def client_once(app_once):
    return app_once.test_client()





def test_request_example(client):
    response = client.get("/")
    #print("res", response.data, file=sys.stderr)
    assert b"<!DOCTYPE html>\n<html>\n\n<head>" in response.data

def test_read(client):
    response = client.get("/read", query_string = {"num": 9})
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert res["penman"] ==  '(h / have-org-role-91\n   :ARG0 (p / person\n            :name (n / name\n                     :op4 "Barack"\n                     :op2 "Hussein"\n                     :op3 "Obama"))\n   :ARG1 (c / country\n            :name (n2 / name\n                      :op2 "United"\n                      :op2 "States"))\n   :ARG2 (p2 / president\n             :ord (o / ordinal-entity\n                     :value 44)))'
    assert '<h2>have-org-role</h2>\n<h3>have-org-role.91:' in res["framedoc"]
    assert res['filename'] == 'testamr.txt'
    assert res['warning'] == ['more than one relation label « :op2 » start at instance « n2 »', 'incoherent :opNN numbering for instance « n »: 4, 2, 3', 'incoherent :opNN numbering for instance « n2 »: 2, 2']


def test_read_date(client):
    response = client.get("/read", query_string = {"num": 1})
    res = json.loads(response.data)
    #print("res", res["lastchanged"])
    assert res["lastchanged"] == "Mon Sep 06, 1976"

    response = client.get("/read", query_string = {"num": 2})
    res = json.loads(response.data)
    #print("res2", res["lastchanged"])
    assert res["lastchanged"] == None

def test_read_missing_num(client):
    response = client.get("/read")
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert res["error"] == "missing mandatory parameter 'num'"

def test_edit_first(client):
    #response = client.get("/read", query_string = {"num": })
    response = client.get("/next", query_string = {"num": 8, "direction": "first"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert "(m / multi-sentence\n   :snt1 (b / bear-02\n            :ARG1 (p / person\n" in res["penman"]

def test_edit_last(client):
    #response = client.get("/read", query_string = {"num": })
    response = client.get("/next", query_string = {"num": 8, "direction": "last"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(h / have-org-role-91\n   :ARG0 (p / person\n            :name (n / name\n                     :op1 \"Joe\"\n" in res["penman"]
    assert res["num"] == 23

def test_edit_next(client):
    #response = client.get("/read", query_string = {"num": })
    response = client.get("/next", query_string = {"num": 8, "direction": "next"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["num"] == 9

def test_edit_prec(client):
    #response = client.get("/read", query_string = {"num": })
    response = client.get("/next", query_string = {"num": 8, "direction": "preceding"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["num"] == 7



def test_edit_prec1(client):
    #response = client.get("/read", query_string = {"num": 4})
    response = client.get("/next", query_string = {"num": 1, "direction": "preceding"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["num"] == 1




def test_edit_addinstance(client):
    response = client.get("/read", query_string = {"num": 6})
    response = client.get("/edit", query_string = {"num": 6, "addconcept": "rise-01"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == None
    assert res["penman"] == "(r / rise-01)"
    #assert 1 == 2


def test_edit_addinstance_wrong_roleset(client):
    response = client.get("/read", query_string = {"num": 6})
    response = client.get("/edit", query_string = {"num": 6, "addconcept": "rise-06"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == ["«rise-06» is not a defined propbank roleset",
                              "the graph is disconnected (invalid)"]
    assert res["penman"] == "(r / rise-01)\n\n(r1 / rise-06)"


def test_edit_addedge_with_concepts(client):
    response = client.get("/read", query_string = {"num": 17})
    response = client.get("/edit", query_string = {"num": 17, "start": "//go-02", "label": "ARG0", "end": "//man" })
    response = client.get("/edit", query_string = {"num": 17, "start": "//go-02", "label": "ARG4", "end": "/work-01" })
    response = client.get("/edit", query_string = {"num": 17, "start": "w", "label": "ARG0", "end": "//man" })
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["warning"] == None
    assert res["penman"] == "(g / go-02\n   :ARG0 (m / man)\n   :ARG4 (w / work-01\n            :ARG0 m))"
    #assert 1 == 2


def test_edit_modconcept(client):
    response = client.get("/read", query_string = {"num": 4})
    response = client.get("/edit", query_string = {"num": 4, "modconcept": "b", "newconcept": "bark-02"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == ['«bark-02» is not a defined propbank roleset']
    assert res["penman"] == "(b / bark-02\n   :ARG0 (d / dog\n            :mod (l / little))\n   :ARG2 (d2 / dog\n             :mod (b2 / big)))"
    #assert 1 == 2

def test_edit_modconcept_wrong_concept(client):
    response = client.get("/read", query_string = {"num": 18})
    response = client.get("/edit", query_string = {"num": 18, "modconcept": "r", "newconcept": "cinema"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == ["invalid concept 'cinema'"]
    #assert 1 == 2
def test_edit_modedge_wrong_edge(client):
    response = client.get("/read", query_string = {"num": 18})
    response = client.get("/edit", query_string = {"num": 18, "modedge_start": "o", "modedge_end": "r", "newedge": ":ARG111"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == [ "invalid relation ':ARG111'",
                               "invalid concept 'cinema'",
                               'invalid argument «:ARG111» for concept «open-09»']
    #assert 1 == 2



def test_edit_modedge(client):
    response = client.get("/read", query_string = {"num": 2})
    response = client.get("/edit", query_string = {"num": 2, "modedge_start": "k","modedge_end": "m", "newedge": ":ARG2"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(k / kill-01\n   :ARG0 (c / cat)\n   :ARG2 (m / mouse))"

#def test_edit_deledge(client_once):
#    response = client_once.get("/read", query_string = {"num": 2})
#    response = client_once.get("/edit", query_string = {"num": 2, "deledge_start": "k","deledge_end": "m", "deledge": ":ARG1"})
#    res = json.loads(response.data)
#    #print("res", json.dumps(res, indent=2))
#    assert res["penman"] == "(k / kill-01\n   :ARG0 (c / cat))\n\n(m / mouse)"

def test_edit_deledge(client):
    response = client.get("/read", query_string = {"num": 7})
    response = client.get("/edit", query_string = {"num": 7, "deledge_start": "b","deledge_end": "a", "deledge": ":ARG1"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(a / apple\n   :quant 100)\n\n(b / buy-01\n   :ARG0 (c / child\n            :quant 100\n            :poss s)\n   :ARG4 (s / school\n            :quant 100)\n   :ARG3 (m / monetary-quantity\n            :quant 100\n            :unit (e / euro)))"

def test_edit_deledge2(client):
    response = client.get("/read", query_string = {"num": 20})
    response = client.get("/edit", query_string = {"num": 20, "deledge_start": "m","deledge_end": "a", "deledge": ":snt1"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(a / and\n   :op1 (g / guess-01\n           :ARG0 (i / i)\n           :ARG1 (o / overload-01\n                    :ARG1 (c / capacity\n                             :mod (c2 / carry-01)\n                             :poss (t2 / tower\n                                       :part-of (s / station\n                                                   :mod (b / base))))\n                    :degree (t / total)))\n   :op2 (g2 / get-through-12\n            :polarity -\n            :ARG0 i\n            :degree (a2 / at-all)))\n\n(m / multi-sentence\n   :snt2 (c3 / contrast-01\n             :ARG1 (p / possible-01\n                      :ARG1 (f / find-01\n                               :ARG0 (i3 / i)\n                               :ARG1 (s2 / signal))\n                      :mod (o2 / only))\n             :ARG2 (c4 / chance-02\n                       :polarity -\n                       :ARG1 (c5 / connect-01\n                                 :ARG0 i3\n                                 :ARG2 (i2 / internet)))))"

def test_edit_delinstance(client):
    response = client.get("/read", query_string = {"num": 1})
    response = client.get("/edit", query_string = {"num": 1, "delinstance": "p"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(m / multi-sentence\n   :snt1 (b / bear-02\n            :location (c / city\n                         :name (n2 / name\n                                   :op1 \"London\")\n                         :wiki \"Q84\"))\n   :snt2 (l / live-01\n            :location c\n            :mod (s / still)))\n\n(n / name\n   :op1 \"Naomie\"\n   :op2 \"Harris\")"

def test_edit_settop(client):
    response = client.get("/read", query_string = {"num": 10})
    response = client.get("/edit", query_string = {"num": 10, "newtop": "t"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(t / teach-01\n   :ARG0 (p / person)\n   :ARG1 (h / history))"

    response = client.get("/edit", query_string = {"num": 10, "newtop": "p"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] ==  "(p / person\n   :ARG0-of (t / teach-01\n               :ARG1 (h / history)))"


def test_edit_settop2(client):
    response = client.get("/read", query_string = {"num": 10})
    response = client.get("/edit", query_string = {"num": 10, "newtop": "xx"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(p / person\n   :ARG0-of (t / teach-01\n               :ARG1 (h / history)))"
    assert res["warning"] == [ "invalid instance variable xx"]

def test_edit_move_relation_start(client):
    response = client.get("/read", query_string = {"num": 5})
    response = client.get("/edit", query_string = {"num": 5, "modedge_start": "c2", "modedge_end": "n2", "modedge_newstart": "h", "newedge": "nod_used"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Cardiff")\n            :wiki "Q10690")\n   :ARG1 (c2 / country\n             :wiki "Q25")\n   :ARG2 (c3 / capital)\n   :nod_used (n2 / name\n                 :op1 "Wales"))'

def test_edit_delliteral(client):
    response = client.get("/read", query_string = {"num": 21})
    response = client.get("/edit", query_string = {"num": 21, "delliteral": "Q183", "literalid": "c2", "literaledge": ":wiki"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["penman"] == '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Berlin")\n            :wiki "Q64")\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Germany"))\n   :ARG2 (c3 / capital))'

#    '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Cardiff"))\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Wales")\n             :wiki "Q25")\n   :ARG2 (c3 / capital))'

# depends on success of preceding test
def test_edit_modliteral(client):
    response = client.get("/read", query_string = {"num": 21})
    response = client.get("/edit", query_string = {"num": 21, "literalid": "c","literaledge": ":wiki", "newliteral": "Q64AA"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["penman"] == '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Berlin")\n            :wiki "Q64AA")\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Germany"))\n   :ARG2 (c3 / capital))'

    #'(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Cardiff")\n            :wiki "Q10690")\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Wales")\n             :wiki "Q2AA")\n   :ARG2 (c3 / capital))'

def test_edit_addliteral(client):
    response = client.get("/read", query_string = {"num": 14})
    response = client.get("/edit", query_string = {"num": 14, "literalof": "b", "relationforliteral": "quant", "newliteral": 5})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(bbb / want-01\n     :polarity -\n     :ARG0 (m / man\n              :ARG0-of (r / repair-01\n                          :ARG1 (b / bike\n                                   :quant 5)))\n     :ARG1 (p / pay-01\n              :ARG2 m))"

    #"(k / kill-01\n   :ARG0 (c / cat\n            :quant 5)\n   :ARG1 (m / mouse))"

    response = client.get("/edit", query_string = {"num": 2, "literalof": "m", "relationforliteral": "tag", "newliteral": "My Mouse"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(k / kill-01\n   :ARG0 (c / cat)\n   :ARG2 (m / mouse\n            :tag \"My Mouse\"))"



def test_read_nointeger(client):
    response = client.get("/read", query_string = {"num": "anystring"})
    res = json.loads(response.data)
    print("res", res)
    assert res["error"] == "Parameter 'num' must be an integer."

def test_read_num_too_big(client):
    response = client.get("/read", query_string={"num": 100})
    res = json.loads(response.data)
    print("res", res)
    assert res["error"] == "invalid sentence number: must be between 1 and 23\n"

def test_search_text(client):
    #response = client.get("/read", query_string = {"num": 4})
    response = client.get("/search", query_string = {"num": 4, "what": "findtextprec", "regex": "the" })
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 3

    response = client.get("/search", query_string = {"num": 4, "what": "findtextnext", "regex": "in" })
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 6

def test_search_id(client):
    #response = client.get("/read", query_string = {"num": 4})
    response = client.get("/search", query_string = {"num": 4, "what": "findidnext", "regex": "incorrect" })
    res = json.loads(response.data)
    print("res", res)
    assert res["num"] == 8

    response = client.get("/search", query_string = {"num": 8, "what": "findidprec", "regex": "empty" })
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 6

def test_get_invalid_amr(client):
    response = client.get("/read", query_string = {"num": 13})
    res = json.loads(response.data)
    #print("res", res)
    assert res['warning'] == ['format error: Expected: ROLE in line 1:42 « (aaa / want-01 :polarity - :ARG0 (m / man <span class="syntaxerror">ARG0-of</span> (r / repair-01 :ARG1 (b / bike))) :ARG1 (p / pay-01 :ARG2 m)) », please correct file in a text editor first']

def test_get_invalid_triple(client):
    response = client.get("/read", query_string = {"num": 19})
    res = json.loads(response.data)
    #print("res", res)
    assert res['warning'] == ['instance «a» of «and» has an invalid relation «:snt1»']

def test_get_disconnected_amr(client):
    response = client.get("/read", query_string = {"num": 12})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    #assert res["num"] == 6
    assert res['warning'] == [ "the graph is disconnected (invalid)" ]

def test_edit_amr_undo_redo(client):
    response = client.get("/read", query_string = {"num": 6})
    response = client.get("/edit", query_string = {"num": 6, "modpenman": "( rr /   rise-01)"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(rr / rise-01)" == res["penman"]

    response = client.get("/edit", query_string = {"num": 6, "modpenman": "(r / rise-01  :location (e / east))"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert "(r / rise-01\n   :location (e / east))" == res["penman"]

    response = client.get("/edit", query_string = {"num": 6, "addconcept": "sun"})
    response = client.get("/edit", query_string = {"num": 6, "start": "r", "end": "s", "label": "ARG0"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(r / rise-01\n   :location (e / east)\n   :ARG0 (s / sun))" == res["penman"]

    response = client.get("/history", query_string = {"num": 6, "history": "undo"})
    response = client.get("/history", query_string = {"num": 6, "history": "undo"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(r / rise-01\n   :location (e / east))" == res["penman"]
    
def test_edit_comment(client):
    response = client.get("/read", query_string = {"num": 6})
    response = client.get("/edit", query_string = {"num": 6, "modcomment": "adding a comment\n\nwith an empty line in between\n\n"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["warning"] == None
    assert res["comments"] == "adding a comment\nwith an empty line in between"
    #assert 1 == 2

def test_read_date_aftermod(client):
    #response = client.get("/read", query_string = {"num": 1})
    #res = json.loads(response.data)
    currentdate = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
    response = client.get("/edit", query_string = {"num": 1, "newtop": "p"})
    res = json.loads(response.data)
    #print("res1", res["lastchanged"])
    assert res["lastchanged"] == currentdate

    currentdate = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
    response = client.get("/edit", query_string = {"num": 2, "newtop": "c"})
    res = json.loads(response.data)
    #print("res2", res["lastchanged"])
    assert res["lastchanged"] == currentdate

def test_edit_deledge_notexist(client):
    response = client.get("/read", query_string = {"num": 11})
    response = client.get("/edit", query_string = {"num": 11, "deledge_start": "k","deledge_end": "p", "deledge": ":ARG1111"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == '(k / murder-01\n   :ARG0 (a / amr-unknown)\n   :ARG1 (p / person\n            :name (n / name\n                     :op1 "JFK")\n            :wiki "Q9696"))'


def test_reify(client):
    response = client.get("/read", query_string = {"num": 3})
    response = client.get("/edit", query_string = {"num": 3, "reify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    #print("res", json.dumps(res["penman"], indent=2))
    assert res["penman"] == '(k / kill-01\n   :ARG0 (c / cat)\n   :ARG1 (m / mouse)\n   :ARG1-of (zzz0 / be-located-at-91\n                  :ARG2 (k2 / kitchen))\n   :time (d / date-entity\n            :dayperiod (n / night)))'

def test_dereify(client):
    response = client.get("/read", query_string = {"num": 3})
    response = client.get("/edit", query_string = {"num": 3, "dereify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    print("res2", json.dumps(res["penman"], indent=2))
    assert res["penman"] == '(k / kill-01\n   :ARG0 (c / cat)\n   :ARG1 (m / mouse)\n   :location (k2 / kitchen)\n   :time (d / date-entity\n            :dayperiod (n / night)))'


# depends on two preceding tests, fails if these fail too
def test_reify_dereify_additional_edge(client):
    response = client.get("/read", query_string = {"num": 3})
    response = client.get("/edit", query_string = {"num": 3, "reify": ":location <>  be-located-at-91"})
    response = client.get("/edit", query_string = {"num": 3, "addconcept": "fast"})
    response = client.get("/edit", query_string = {"num": 3, "start": "zzz0", "label": "manner", "end": "//fast" })
    response = client.get("/edit", query_string = {"num": 3, "dereify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))


    assert res["penman"] == '(k / kill-01\n   :ARG0 (c / cat)\n   :ARG1 (m / mouse)\n   :ARG1-of (zzz0 / be-located-at-91\n                  :ARG2 (k2 / kitchen)\n                  :manner (f / fast))\n   :time (d / date-entity\n            :dayperiod (n / night)))'
    assert res["warning"] == [ "information loss: cannot attache edge \u00ab zzz0 :manner f \u00bb after dereification. Please modify graph.",
                                ]



# depends on three preceding tests, fails if these fail too

def test_reify_dereify_missing_ARG(client):
    response = client.get("/read", query_string = {"num": 3})
    response = client.get("/edit", query_string = {"num": 3, "reify": ":location <>  be-located-at-91"})
    response = client.get("/edit", query_string = {"num": 3, "delinstance": "f" })
    response = client.get("/edit", query_string = {"num": 3,
                                                   "modedge_start": "zzz0",
                                                   "modedge_end": "k2",
                                                   "newedge": ":koARG2"})
    response = client.get("/edit", query_string = {"num": 3, "dereify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == [
        "information loss: cannot attache edge \u00ab zzz0 :koARG2 k2 \u00bb after dereification. Please modify graph.",
        "concept to derify does only have one :ARGn edge: :ARG1",
        "concept to dereify does not have :ARG2 edge.",
        "invalid relation ':koARG2'"
        ]


