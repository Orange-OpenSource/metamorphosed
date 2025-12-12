#!/usr/bin/env python3

# This library is under the 3-Clause BSD License
#
# Copyright (c) 2025,  Orange
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

# Predicts edges between two instances or an instance and a literal
# subclass this class to add your own predictor

import json

from metamorphosed.edge_predictor import Basic_EdgePredictor

class Frequency_EdgePredictor(Basic_EdgePredictor):
    def __init__(self, arglist):
        print("initialising my Frequency_EdgePredictor with %s " % arglist[0])
        with open(arglist[0]) as ifp:
             self.edges = json.load(ifp)

    def predict(self, source_concept, target_concept):
        as_subject = None
        as_object = None
        predicted_label = ":todo"
        if source_concept in self.edges["subjects"]:
            # get most frequent relation with an instance of this concept as subject
            as_subject = self.edges["subjects"][source_concept]
        if target_concept in self.edges["objects"]:
            # get most frequent relation with an instance of this concept as object
            as_object = self.edges["objects"][target_concept]
        freq_s = 0
        freq_o = 0
        if as_subject:
            freq_s = as_subject[0][1]
            predicted_label = as_subject[0][0]
        elif as_object:
            freq_o = as_object[0][1]
            predicted_label = as_object[0][0]

        print("predicted label <<<%s>>> as_subject %s, as_object %s" % (predicted_label, as_subject, as_object))
        return predicted_label
