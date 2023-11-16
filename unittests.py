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


import glob
import json
import os
import shutil
import sys
import tempfile
import time

import git
import pytest

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
#@pytest.fixture()
#def app_once():
#    #app = create_app()
#    #app.config.update({
#    #    "TESTING": True,
#    #})
#    aes = AMR_Edit_Server(4568,
#                          "testamr.txt",
#                          "propbank-frames/frames/",
#                          "relations.txt",
#                          "concepts.txt",
#                          "constraints.yml",
#                          False # readonly
#                          )
#    app = aes.app
#
#    # other setup can go here
#    yield app
#
#    # clean up / reset resources here


# start server just for one test without any validating stuff to test git
@pytest.fixture()
def app_git():
    datadir = tempfile.TemporaryDirectory()
    print("temporary test directory", datadir)
    shutil.copyfile("testamr.txt", datadir.name + "/testamr.txt")
    repo = git.Repo.init(datadir.name)
    repo.git.add(datadir.name + "/testamr.txt")
    repo.git.commit("-m", "initial")

    aes = AMR_Edit_Server(4568,
                          datadir.name + "/testamr.txt",
                          None,
                          None,
                          None,
                          None,
                          False
                          )
    app = aes.app

    # other setup can go here

    yield app, repo

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


#@pytest.fixture()
#def client_once(app_once):
#    return app_once.test_client()


@pytest.fixture()
def client_git(app_git):
    app, repo = app_git
    #return app_git.test_client()
    return app.test_client(), repo


def test_request_example(client):
    response = client.get("/")
    #print("res", response.data, file=sys.stderr)
    assert b"<!DOCTYPE html>\n<html>\n\n<head>" in response.data


def test_info(client):
    response = client.get("/version")
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert res == {'name': 'AMR Editor', 'version': '2.7.0', 'apiversion': '1.3.0'}

    response = client.get("/info", query_string={"withdata": True})
    res = json.loads(response.data)
    #print("res", res)
    assert res['reifications'] == [':accompanier ↔ accompany-01',
                                   ':age ↔ age-01',
                                   ':cause ↔ cause-01',
                                   ':beneficiary ↔ benefit-01',
                                   ':concession ↔ have-concession-91',
                                   ':condition ↔ have-condition-91',
                                   ':degree ↔ have-degree-92',
                                   ':destination ↔ be-destined-for-91',
                                   ':duration ↔ last-01',
                                   ':example ↔ exemplify-01',
                                   ':extent ↔ have-extent-91',
                                   ':frequency ↔ have-frequency-91',
                                   ':instrument ↔ have-instrument-91',
                                   ':li ↔ have-li-91',
                                   ':location ↔ be-located-at-91',
                                   ':manner ↔ have-manner-91',
                                   ':mod ↔ have-mod-91',
                                   ':ord ↔ have-ord-91',
                                   ':part ↔ have-part-91',
                                   ':polarity ↔ have-polarity-91',
                                   ':poss ↔ own-01',
                                   ':purpose ↔ have-purpose-91',
                                   ':quant ↔ have-quant-91',
                                   ':source ↔ be-from-91',
                                   ':subevent ↔ have-subevent-91',
                                   ':time ↔ be-temporally-at-91',
                                   ':topic ↔ concern-02',
                                   ':value ↔ have-value-91',
                                   ':subset ↔ include-91']


def test_read(client):
    response = client.get("/read", query_string={"num": 9})
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert res["penman"] == '(h / have-org-role-91\n   :ARG0 (p / person\n            :name (n / name\n                     :op4 "Barack"\n                     :op2 "Hussein"\n                     :op3 "Obama"))\n   :ARG1 (c / country\n            :name (n2 / name\n                      :op2 "United"\n                      :op2 "States"))\n   :ARG2 (p2 / president\n             :ord (o / ordinal-entity\n                     :value 44)))'
    assert '<h2>have-org-role</h2>\n<h3>have-org-role.91:' in res["framedoc"]
    assert res['filename'] == 'testamr.txt'
    assert res['warning'] == ['more than one relation label « :op2 » start at instance « n2 »', 'incoherent :opNN numbering for instance « n »: 4, 2, 3', 'incoherent :opNN numbering for instance « n2 »: 2, 2']


def test_read_date(client):
    response = client.get("/read", query_string={"num": 1})
    res = json.loads(response.data)
    #print("res", res["lastchanged"])
    assert res["lastchanged"] == "Mon Sep 06, 1976"

    response = client.get("/read", query_string={"num": 2})
    res = json.loads(response.data)
    #print("res2", res["lastchanged"])
    assert res["lastchanged"] is None


def test_read_missing_num(client):
    response = client.get("/read")
    res = json.loads(response.data)
    #print("res", res, file=sys.stderr)
    assert res["error"] == "missing mandatory parameter 'num'"


def test_edit_first(client):
    #response = client.get("/read", query_string={"num":})
    response = client.get("/next", query_string={"num": 8, "direction": "first"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(m / multi-sentence\n   :snt1 (b / bear-02\n            :ARG1 (p / person\n" in res["penman"]


def test_edit_last(client):
    #response = client.get("/read", query_string={"num":})
    response = client.get("/next", query_string={"num": 8, "direction": "last"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(h / have-org-role-91\n   :ARG0 (p / person\n            :name (n / name\n                     :op1 \"Joe\"\n" in res["penman"]
    assert res["num"] == 24


def test_edit_next(client):
    #response = client.get("/read", query_string={"num":})
    response = client.get("/next", query_string={"num": 8, "direction": "next"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["num"] == 9


def test_edit_prec(client):
    #response = client.get("/read", query_string={"num":})
    response = client.get("/next", query_string={"num": 8, "direction": "preceding"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["num"] == 7


def test_edit_prec1(client):
    #response = client.get("/read", query_string={"num": 4})
    response = client.get("/next", query_string={"num": 1, "direction": "preceding"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["num"] == 1


def test_edit_addinstance(client):
    response = client.get("/read", query_string={"num": 6})
    response = client.get("/edit", query_string={"num": 6, "addconcept": "rise-01"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] is None
    assert res["penman"] == "(r / rise-01)"
    #assert 1 == 2

    # needed for coverage test (count variables)
    response = client.get("/edit", query_string={"num": 8, "addconcept": "cry-01"})


def test_edit_addinstance_wrong_roleset(client):
    response = client.get("/read", query_string={"num": 6})
    response = client.get("/edit", query_string={"num": 6, "addconcept": "rise-06"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == ["«rise-06» is not a defined propbank roleset",
                              "the graph is disconnected (invalid)"]
    assert res["penman"] == "(r / rise-01)\n\n(r1 / rise-06)"


def test_edit_addedge_with_concepts(client):
    response = client.get("/read", query_string={"num": 17})
    response = client.get("/edit", query_string={"num": 17, "start": "//go-02", "label": "ARG0", "end": "//man"})
    response = client.get("/edit", query_string={"num": 17, "start": "//go-02", "label": "ARG4", "end": "/work-01"})
    response = client.get("/edit", query_string={"num": 17, "start": "w", "label": "ARG0", "end": "//man"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] is None
    assert res["penman"] == "(g / go-02\n   :ARG0 (m / man)\n   :ARG4 (w / work-01\n            :ARG0 m))"
    #assert 1 == 2


def test_edit_modconcept(client):
    response = client.get("/read", query_string={"num": 4})
    response = client.get("/edit", query_string={"num": 4, "modconcept": "b", "newconcept": "bark-02"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == ['«bark-02» is not a defined propbank roleset']
    assert res["penman"] == "(b / bark-02\n   :ARG0 (d / dog\n            :mod (l / little))\n   :ARG2 (d2 / dog\n             :mod (b2 / big)))"
    #assert 1 == 2


def test_edit_addname(client):
    response = client.get("/edit", query_string={"num": 4, "addname": "Little Dog", "nameof": "d"})
    res = json.loads(response.data)
    print("res", json.dumps(res["penman"], indent=2))
    assert res["penman"] == "(b / bark-02\n   :ARG0 (d / dog\n            :mod (l / little)\n            :name (n / name\n                     :op1 \"Little\"\n                     :op2 \"Dog\"))\n   :ARG2 (d2 / dog\n             :mod (b2 / big)))"


def test_edit_modconcept_wrong_concept(client):
    response = client.get("/read", query_string={"num": 18})
    response = client.get("/edit", query_string={"num": 18, "modconcept": "r", "newconcept": "cinema"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == ["invalid concept 'cinema'"]
    #assert 1 == 2


def test_edit_modedge_wrong_edge(client):
    response = client.get("/read", query_string={"num": 18})
    response = client.get("/edit", query_string={"num": 18, "modedge_start": "o", "modedge_end": "r", "newedge": ":ARG111"})
    res = json.loads(response.data)

    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == ["invalid relation ':ARG111'",
                              "invalid concept 'cinema'",
                              'invalid argument «:ARG111» for concept «open-09»']
    #assert 1 == 2


def test_edit_modedge(client):
    response = client.get("/read", query_string={"num": 2})
    response = client.get("/edit", query_string={"num": 2, "modedge_start": "k", "modedge_end": "m", "newedge": ":ARG2"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(k / kill-01\n   :ARG0 (c / cat)\n   :ARG2 (m / mouse))"

#def test_edit_deledge(client_once):
#    response = client_once.get("/read", query_string={"num": 2})
#    response = client_once.get("/edit", query_string={"num": 2, "deledge_start": "k","deledge_end": "m", "deledge": ":ARG1"})
#    res = json.loads(response.data)
#    #print("res", json.dumps(res, indent=2))
#    assert res["penman"] == "(k / kill-01\n   :ARG0 (c / cat))\n\n(m / mouse)"


def test_edit_deledge(client):
    response = client.get("/read", query_string={"num": 7})
    response = client.get("/edit", query_string={"num": 7, "deledge_start": "b", "deledge_end": "a", "deledge": ":ARG1"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(a / apple\n   :quant 100)\n\n(b / buy-01\n   :ARG0 (c / child\n            :quant 100\n            :poss s)\n   :ARG4 (s / school\n            :quant 100)\n   :ARG3 (m / monetary-quantity\n            :quant 100\n            :unit (e / euro)))"


def test_edit_deledge2(client):
    response = client.get("/read", query_string={"num": 20})
    response = client.get("/edit", query_string={"num": 20, "deledge_start": "m", "deledge_end": "a", "deledge": ":snt1"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(a / and\n   :op1 (g / guess-01\n           :ARG0 (i / i)\n           :ARG1 (o / overload-01\n                    :ARG1 (c / capacity\n                             :mod (c2 / carry-01)\n                             :poss (t2 / tower\n                                       :part-of (s / station\n                                                   :mod (b / base))))\n                    :degree (t / total)))\n   :op2 (g2 / get-through-12\n            :polarity -\n            :ARG0 i\n            :degree (a2 / at-all)))\n\n(m / multi-sentence\n   :snt2 (c3 / contrast-01\n             :ARG1 (p / possible-01\n                      :ARG1 (f / find-01\n                               :ARG0 (i3 / i)\n                               :ARG1 (s2 / signal))\n                      :mod (o2 / only))\n             :ARG2 (c4 / chance-02\n                       :polarity -\n                       :ARG1 (c5 / connect-01\n                                 :ARG0 i3\n                                 :ARG2 (i2 / internet)))))"


def test_edit_delinstance(client):
    response = client.get("/read", query_string={"num": 1})
    response = client.get("/edit", query_string={"num": 1, "delinstance": "p"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(m / multi-sentence\n   :snt1 (b / bear-02\n            :location (c / city\n                         :name (n2 / name\n                                   :op1 \"London\")\n                         :wiki \"Q84\"))\n   :snt2 (l / live-01\n            :location c\n            :mod (s / still)))\n\n(n / name\n   :op1 \"Naomie\"\n   :op2 \"Harris\")"


def test_edit_settop(client):
    response = client.get("/read", query_string={"num": 10})
    response = client.get("/edit", query_string={"num": 10, "newtop": "t"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(t / teach-01\n   :ARG0 (p / person)\n   :ARG1 (h / history))"

    response = client.get("/edit", query_string={"num": 10, "newtop": "p"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(p / person\n   :ARG0-of (t / teach-01\n               :ARG1 (h / history)))"


def test_edit_settop2(client):
    response = client.get("/read", query_string={"num": 10})
    response = client.get("/edit", query_string={"num": 10, "newtop": "xx"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(p / person\n   :ARG0-of (t / teach-01\n               :ARG1 (h / history)))"
    assert res["warning"] == ["invalid instance variable xx"]


def test_edit_move_relation_start(client):
    response = client.get("/read", query_string={"num": 5})
    response = client.get("/edit", query_string={"num": 5, "modedge_start": "c2", "modedge_end": "n2", "modedge_newstart": "h", "newedge": "not_used"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Cardiff")\n            :wiki "Q10690")\n   :ARG1 (c2 / country\n             :wiki "Q25")\n   :ARG2 (c3 / capital)\n   :not_used (n2 / name\n                 :op1 "Wales"))'


def test_edit_move_relation_wrong_start(client):
    response = client.get("/edit", query_string={"num": 5, "modedge_start": "c2", "modedge_end": "n2", "modedge_newstart": "hhh", "newedge": "also_not_used"})
    res = json.loads(response.data)
    print("res", json.dumps(res["warning"], indent=2))
    assert res["warning"] == ["new source instance « hhh » does not exist",
                              "invalid relation ':not_used'"]


def test_edit_delliteral(client):
    response = client.get("/read", query_string={"num": 21})
    response = client.get("/edit", query_string={"num": 21, "delliteral": "Q183", "literalid": "c2", "literaledge": ":wiki"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["penman"] == '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Berlin")\n            :wiki "Q64")\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Germany"))\n   :ARG2 (c3 / capital))'

#    '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Cardiff"))\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Wales")\n             :wiki "Q25")\n   :ARG2 (c3 / capital))'

# depends on success of preceding test


def test_edit_modliteral(client):
    response = client.get("/read", query_string={"num": 21})
    response = client.get("/edit", query_string={"num": 21, "literalid": "c", "literaledge": ":wiki", "newliteral": "Q64AA"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == '(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Berlin")\n            :wiki "Q64AA")\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Germany"))\n   :ARG2 (c3 / capital))'

    #'(h / have-org-role-91\n   :ARG0 (c / city\n            :name (n / name\n                     :op1 "Cardiff")\n            :wiki "Q10690")\n   :ARG1 (c2 / country\n             :name (n2 / name\n                       :op1 "Wales")\n             :wiki "Q2AA")\n   :ARG2 (c3 / capital))'


def test_edit_addliteral(client):
    response = client.get("/read", query_string={"num": 14})
    response = client.get("/edit", query_string={"num": 14, "literalof": "b", "relationforliteral": "quant", "newliteral": 5})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(bbb / want-01\n     :polarity -\n     :ARG0 (m / man\n              :ARG0-of (r / repair-01\n                          :ARG1 (b / bike\n                                   :quant 5)))\n     :ARG1 (p / pay-01\n              :ARG2 m))"

    #"(k / kill-01\n   :ARG0 (c / cat\n            :quant 5)\n   :ARG1 (m / mouse))"

    response = client.get("/edit", query_string={"num": 2, "literalof": "m", "relationforliteral": "tag", "newliteral": "My Mouse"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == "(k / kill-01\n   :ARG0 (c / cat)\n   :ARG2 (m / mouse\n            :tag \"My Mouse\"))"


def test_read_nointeger(client):
    response = client.get("/read", query_string={"num": "anystring"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["error"] == "Parameter 'num' must be an integer."


def test_read_num_too_big(client):
    response = client.get("/read", query_string={"num": 100})
    res = json.loads(response.data)
    #print("res", res)
    assert res["error"] == "invalid sentence number: must be between 1 and 24"


def test_duplicate_edge(client):
    response = client.get("/edit", query_string={"num": 23, "start": "k", "label": "ARG0", "end": "a"})
    response = client.get("/edit", query_string={"num": 23, "start": "a", "label": "ARG0", "end": "k"})
    res = json.loads(response.data)
    #print("res", res["warning"])
    assert res["warning"] == ['more than one relation between « k » and « a » (inverted) (:ARG0)',
                              'more than one relation label « :ARG0 » start at instance « k »',
                              'more than one relation between « a » and « k » (:ARG0)']


def test_search_text(client):
    #response = client.get("/read", query_string={"num": 4})
    response = client.get("/search", query_string={"num": 4, "what": "findtextprec", "regex": "the"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 3

    response = client.get("/search", query_string={"num": 4, "what": "findtextnext", "regex": "in"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 6

    response = client.get("/search", query_string={"num": 4, "what": "findtextnext", "regex": "not existing text"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 4


def test_search_id(client):
    #response = client.get("/read", query_string={"num": 4})
    response = client.get("/search", query_string={"num": 4, "what": "findidnext", "regex": "incorrect"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 8

    response = client.get("/search", query_string={"num": 8, "what": "findidprec", "regex": "empty"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 6


def test_search_amr(client):
    #response = client.get("/read", query_string={"num": 4})
    response = client.get("/search", query_string={"num": 4, "what": "findamrnext", "regex": "p / pay-01"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 12

    response = client.get("/search", query_string={"num": 12, "what": "findamrprec", "regex": "Harris"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 1

    response = client.get("/search", query_string={"num": 12, "what": "findamrprec", "regex": ":not_there"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 12


def test_search_comment(client):
    #response = client.get("/read", query_string={"num": 4})
    response = client.get("/search", query_string={"num": 1, "what": "findcommentnext", "regex": "h.re"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 15

    response = client.get("/search", query_string={"num": 4, "what": "findcommentprec", "regex": "s[aeiou]cond"})
    res = json.loads(response.data)
    #print("res", res)
    assert res["num"] == 2


def test_get_invalid_amr(client):
    response = client.get("/read", query_string={"num": 13})
    res = json.loads(response.data)
    #print("res", res)
    assert res['warning'] == ['format error: Expected: ROLE in line 1:42 « (aaa / want-01 :polarity - :ARG0 (m / man <span class="syntaxerror">ARG0-of</span> (r / repair-01 :ARG1 (b / bike))) :ARG1 (p / pay-01 :ARG2 m)) », please correct file in a text editor first']


def test_get_invalid_triple(client):
    response = client.get("/read", query_string={"num": 19})
    res = json.loads(response.data)
    #print("res", res)
    assert res['warning'] == ['instance «a» of «and» has an invalid relation «:snt1»']


def test_get_disconnected_amr(client):
    response = client.get("/read", query_string={"num": 12})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    #assert res["num"] == 6
    assert res['warning'] == ["the graph is disconnected (invalid)"]


def test_edit_amr_undo_redo(client):
    response = client.get("/read", query_string={"num": 6})
    response = client.get("/edit", query_string={"num": 6, "modpenman": "( rr /   rise-01)"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(rr / rise-01)" == res["penman"]

    response = client.get("/edit", query_string={"num": 6, "modpenman": "(r / rise-01  :location (e / east))"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(r / rise-01\n   :location (e / east))" == res["penman"]

    response = client.get("/edit", query_string={"num": 6, "addconcept": "sun"})
    response = client.get("/edit", query_string={"num": 6, "start": "r", "end": "s", "label": "ARG0"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(r / rise-01\n   :location (e / east)\n   :ARG0 (s / sun))" == res["penman"]

    response = client.get("/history", query_string={"num": 6, "history": "undo"})
    response = client.get("/history", query_string={"num": 6, "history": "undo"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert "(r / rise-01\n   :location (e / east))" == res["penman"]

    response = client.get("/history", query_string={"num": 6, "history": "redo"})
    response = client.get("/history", query_string={"num": 6, "history": "redo"})
    res = json.loads(response.data)
    #print("res", json.dumps(res["penman"], indent=2))
    assert "(r / rise-01\n   :location (e / east)\n   :ARG0 (s / sun))" == res["penman"]


def test_edit_comment(client):
    #response = client.get("/read", query_string={"num": 6})
    response = client.get("/edit", query_string={"num": 6, "modcomment": "adding a comment\n\nwith an empty line in between\n\n"})
    res = json.loads(response.data)
    print("res", json.dumps(res, indent=2))
    assert res["warning"] is None
    assert res["comments"] == "adding a comment\nwith an empty line in between"
    #assert 1 == 2


def test_delete_comment(client):
    response = client.get("/read", query_string={"num": 15})
    response = client.get("/edit", query_string={"num": 15, "modcomment": ""})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] is None
    assert res["comments"] == ""
    #assert 1 == 2


def test_read_date_aftermod(client):
    #response = client.get("/read", query_string={"num": 1})
    #res = json.loads(response.data)
    currentdate = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
    response = client.get("/edit", query_string={"num": 1, "newtop": "p"})
    res = json.loads(response.data)
    #print("res1", res["lastchanged"])
    assert res["lastchanged"] == currentdate

    currentdate = time.strftime("%a %b %d, %Y %H:%M", time.localtime(time.time()))
    response = client.get("/edit", query_string={"num": 2, "newtop": "c"})
    res = json.loads(response.data)
    #print("res2", res["lastchanged"])
    assert res["lastchanged"] == currentdate


def test_edit_deledge_notexist(client):
    response = client.get("/read", query_string={"num": 11})
    response = client.get("/edit", query_string={"num": 11, "deledge_start": "k", "deledge_end": "p", "deledge": ":ARG1111"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["penman"] == '(k / murder-01\n   :ARG0 (a / amr-unknown)\n   :ARG1 (p / person\n            :name (n / name\n                     :op1 "JFK")\n            :wiki "Q9696"))'


def test_bad_api_usage(client):
    response = client.get("/reads", query_string={"num": 11})
    #res = json.loads(response.data)
    #print("ZZZZZ",response.status_code, "zzzzz")
    assert response.status_code == 404

    response = client.get("/read", query_string={"numx": 11})
    assert response.status_code == 400
    res = json.loads(response.text)
    assert res == {"error": "missing mandatory parameter 'num'"}

    response = client.get("/read", query_string={"num": 0})
    assert response.status_code == 400
    res = json.loads(response.text)
    assert res == {'error': 'invalid sentence number: must be between 1 and 24'}

    response = client.get("/edit", query_string={"num": 3, "reifyxx": ":location <>  be-located-at-91"})
    assert response.status_code == 400
    res = json.loads(response.text)
    assert res == {"error": "invalid parameter 'reifyxx'"}

    response = client.get("/edit", query_string={"num": 333, "reify": ":location <>  be-located-at-91"})
    assert response.status_code == 400
    res = json.loads(response.text)
    assert res == {'error': 'invalid sentence number: must be between 1 and 24'}

    response = client.get("/edit", query_string={"num": 3})
    assert response.status_code == 400
    res = json.loads(response.text)
    assert res == {'error': 'No edit valid operation given'}

    response = client.get("/search", query_string={"num": 4, "what": "findcommentprec"})
    assert response.status_code == 400
    res = json.loads(response.text)
    assert res == {"error": "missing mandatory parameter 'regex'"}

    response = client.get("/search", query_string={"num": 0, "what": "findanyerror", "regex": "s[aeiou]cond"})
    assert response.status_code == 400
    res = json.loads(response.text)
    assert res == {"error": "invalid search parameter 'findanyerror'"}


def test_reify(client):
    response = client.get("/read", query_string={"num": 3})
    response = client.get("/edit", query_string={"num": 3, "reify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    #print("res", json.dumps(res["penman"], indent=2))
    assert res["penman"] == '(k / kill-01\n   :ARG0 (c / cat)\n   :ARG1 (m / mouse)\n   :ARG1-of (zzz0 / be-located-at-91\n                  :ARG2 (k2 / kitchen))\n   :time (d / date-entity\n            :dayperiod (n / night)))'


def test_dereify(client):
    response = client.get("/read", query_string={"num": 3})
    response = client.get("/edit", query_string={"num": 3, "dereify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    #print("res2", json.dumps(res["penman"], indent=2))
    assert res["penman"] == '(k / kill-01\n   :ARG0 (c / cat)\n   :ARG1 (m / mouse)\n   :location (k2 / kitchen)\n   :time (d / date-entity\n            :dayperiod (n / night)))'


# depends on two preceding tests, fails if these fail too
def test_reify_dereify_additional_edge(client):
    response = client.get("/read", query_string={"num": 3})
    response = client.get("/edit", query_string={"num": 3, "reify": ":location <>  be-located-at-91"})
    response = client.get("/edit", query_string={"num": 3, "addconcept": "fast"})
    response = client.get("/edit", query_string={"num": 3, "start": "zzz0", "label": "manner", "end": "//fast"})
    response = client.get("/edit", query_string={"num": 3, "dereify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))

    assert res["penman"] == '(k / kill-01\n   :ARG0 (c / cat)\n   :ARG1 (m / mouse)\n   :ARG1-of (zzz0 / be-located-at-91\n                  :ARG2 (k2 / kitchen)\n                  :manner (f / fast))\n   :time (d / date-entity\n            :dayperiod (n / night)))'
    assert res["warning"] == ["information loss: cannot attache edge \u00ab zzz0 :manner f \u00bb after dereification. Please modify graph.",
                              ]


# depends on three preceding tests, fails if these fail too

def test_reify_dereify_missing_ARG(client):
    response = client.get("/read", query_string={"num": 3})
    response = client.get("/edit", query_string={"num": 3, "reify": ":location <>  be-located-at-91"})
    response = client.get("/edit", query_string={"num": 3, "delinstance": "f"})
    response = client.get("/edit", query_string={"num": 3,
                                                 "modedge_start": "zzz0",
                                                 "modedge_end": "k2",
                                                 "newedge": ":koARG2"})
    response = client.get("/edit", query_string={"num": 3, "dereify": ":location <>  be-located-at-91"})
    res = json.loads(response.data)
    #print("res", json.dumps(res, indent=2))
    assert res["warning"] == [
        "information loss: cannot attache edge \u00ab zzz0 :koARG2 k2 \u00bb after dereification. Please modify graph.",
        "concept to derify does only have one :ARGn edge: :ARG1",
        "concept to dereify does not have :ARG2 edge.",
        "invalid relation ':koARG2'"
        ]


def ls(dn):
    for x in glob.glob(dn + "/*"):
        print("%-50s\t%7d" % (x, os.path.getsize(x)))


# test whether server stops if backup file exists
def test_nogit_back_exists():
    datadir = tempfile.TemporaryDirectory()
    print("temporary test directory", datadir)
    shutil.copyfile("testamr.txt", datadir.name + "/testamr.txt")
    shutil.copyfile("testamr.txt", datadir.name + "/testamr.txt.2")

    ls(datadir.name)

    # should crahs here, since we are in no-git mode and the backup file is already there
    try:
        aes = AMR_Edit_Server(4568,
                              datadir.name + "/testamr.txt",
                              None,
                              None,
                              None,
                              None,
                              False
                              )
    except Exception as e:
        assert str(e) == "Edited file <%s/testamr.txt> not under git version control. Backup file <%s/testamr.txt.2> exists already.\nPlease rename Backup file first" % (datadir.name, datadir.name)


# test git add/commit
def test_edit_addinstance_git(client_git):
    client, repo = client_git
    response = client.get("/read", query_string={"num": 6})
    response = client.get("/edit", query_string={"num": 6, "addconcept": "rise-01"})
    response = client.get("/save", query_string={"num": 6})

    ls(repo.working_dir)

    #res = json.loads(response.data)
    #print(res)
    assert "commit: metamorphosed AMR editor: 6 of " in repo.head.log()[-1].message


def test_amrdoc():
    #app = create_app()
    #app.config.update({
    #    "TESTING": True,
    #})

    import amrdoc
    import AMR_relations
    import propbank_frames
    import relations_constraints

    validators = []
    validators.append(AMR_relations.Relations("relations.txt"))
    validators.append(propbank_frames.PropBankFrames("propbank-frames/frames/"))
    validators.append(relations_constraints.Constraints("constraints.yml"))

    ad = amrdoc.AMRdoc("coverageamr.txt")
    msgs = ad.validate(validators)
    assert msgs == ["invalid relation ':ARG10'",
                    '«want-11» is not a defined propbank roleset',
                    'invalid argument «:ARG10» for concept «repair-01»',
                    'instance «d» of «date-entity» has an invalid relation «:time»',
                    'instance «a» of «and» has an invalid relation «:snt1»'
                    ]

    #ads.append(ad)
    tsv = ad.tsv()
    #print(len(tsv))
    assert len(tsv) == 22

    # oo = ad.oneline()
    #    if args.stats:
    #        stats(ads, args.conceptlist)
    output = amrdoc.relations_between_concepts([ad], depth=1)
    assert len(output) == 45
    output = amrdoc.relations_between_concepts([ad], depth=2)
    assert len(output) == 152
    output = amrdoc.relations_between_concepts([ad], depth=3)
    assert len(output) == 289
    # other setup can go here

    cl = ad.sentences[0].getconceptlist()
    assert sorted(cl) == sorted({'m': 'multi-sentence', 'b': 'bear-02', 'p': 'person', 'n': 'name', 'c': 'city', 'n2': 'name', 'l': 'live-01', 's': 'still'})

    wl = ad.sentences[0].getwikilink("a")
    assert wl is None
    wl = ad.sentences[0].getwikilink("p")
    assert wl == "Q156586"

    sl = ad.getsentencelist()
    assert sl == [('sentence 1', 'Naomie Harris was born in London. Naomie Harris still lives in London.'),
                  ('test', 'The cat killed the mouse'),
                  ('sentence 3', 'The cat killed the mouse in the kitchen during the night'),
                  ('sentence 4', 'the little dog barks at the big dog'),
                  ('sentence 5', 'Cardiff is the Welsh capital'),
                  ('sentence 7', '100 children bought 100 apples for their school for 100 Euros'),
                  ('sentence 8 (incorrect)', '50 children bought 100 apples for their school for 100 Euros'),
                  ('sentence 9 (incorrect)', 'Barack Hussein Obama was the 44th president of the United States'),
                  ('sentence 10', 'history teacher'),
                  ('sentence 11', 'Who murdered JFK?'),
                  ('sentence 12 disconnected', 'The man who repaired the bike did not want to be paid'),
                  ('sentence 13 bad format', 'The man who repaired the bike did not want to be paid'),
                  ('sentence 14 OK', 'The man who repaired the bike did not want to be paid'),
                  ('sentence 15 OK', 'For more information, click <a href="http://www.hollywoodbowl.com">here</a>.'),
                  ('sentence 16 OK', 'Wednesday, February 29, 2012, at 4:30pm PST'),
                  ('sentence 18', 'I did not know that the restaurant is not open'),
                  ('sentence 19', None),
                  ('sentence 20', "I guessed the carrying capacity of the base station towers was totally overloaded, and I couldn't get through at all. I was only able to find a signal, not a chance of connecting to the Internet."),
                  ('sentence 21', 'Berlin is the German capital'),
                  ('sentence 22', 'London is larger than Dublin'),
                  ('sentence 23', 'Who assassinated JFK?'),
                  ('sentence last (must be last)', 'Is Joe Biden the US president?')]


def test_amreditor():
    import amreditor
    import io
    aa = amreditor.AMRProcessor()
    #for l in tr:
    #    aa.process(l)
    aa.readpenman("(c / cat)")
    aa.process("mouse")
    aa.show()
    s = io.StringIO()
    aa.write(ofp=s)
    print("<%s>" % s.getvalue())
    assert s.getvalue() == "(mmmm / multigraph\n      :snt1 (c / cat)\n      :snt2 (m / mouse))\n\n"
