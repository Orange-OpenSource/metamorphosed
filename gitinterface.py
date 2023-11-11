# This library is under the 3-Clause BSD License
#
# Copyright (c) 2023,  Orange
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

import os
import git


def is_git_controlled(fn, verbose=False):
    gitok = False
    repo = None
    absfn = os.path.abspath(fn)
    try:
        if verbose:
            print("check git for <%s>" % fn)
        repo = git.Repo(os.path.dirname(fn), search_parent_directories=True)
        #print("ZZZZ", fn, repo.untracked_files, repo.working_tree_dir)

        for utf in repo.untracked_files:
            absutf = os.path.join(repo.working_tree_dir, utf)
            #print(absfn, absutf)
            if absfn == absutf:
                raise FileNotGitControlled("%s not controlled by git" % fn)
        gitok = True

        # file versioned under git, we overwrite the input file
        if verbose:
            print("git conrolled", fn)

    except (git.exc.InvalidGitRepositoryError, FileNotGitControlled) as e:
        if verbose:
            print("no git controlled", e)
        pass
    if not verbose:
        return gitok
    else:
        return gitok, absfn, repo


def save(fn, version, writefunc, #contents,
         warnings, messages, do_add=True):
    # returns tuple: (repo, saveok, gitok)
    gitok, absfn, repo = is_git_controlled(fn, verbose=True)
    ofp = None
    if gitok:
        # file versioned under git, we overwrite the input file
        print("writing orig")
        ofp = open(fn, "w")
    else:
        try:
            ofp = open(fn + "." + version, "w")

        except Exception as e:
            print("cannot write %s" % fn, e)
            warnings.append("cannot write %s: %s. File not saved" % (fn, e))
            return repo, 0, gitok
    writefunc(ofp)
    print("%s written (git: %s)" % (ofp.name, gitok))
    messages.append("%s written (git: %s)" % (ofp.name, gitok))
    ofp.close()
    if gitok:
        if not do_add:
            return repo, 1, False
        #rtc = repo.git.status()
        try:
            #rtc = repo.git.diff(os.path.basename(fn))
            rtc = repo.git.diff(absfn)
            #print("RTC", rtc)
            if rtc:
                rtc = repo.git.add(absfn)
                #rtc = repo.git.add(fn)
                #atleastonegitok = True
                #rtc = repo.git.commit("-m", "metamorphosed coref editor: %s of '%s' saved" % (", ".join(modified), fn), author=self.author)
                #print("commited %s" % (fn), rtc)
                return repo, 1, True
            else:
                print("nothing to add for %s" % (fn), rtc)
                return repo, 1, False
        except Exception as e:
            print("COMMIT Error <%s> <%s> <%s>" % (e, fn, rtc))
            warnings.append("commit error <%s> <%s> <%s>" % (e, fn, rtc))
            return repo, 1, False
    return repo, 1, False


#def oosave(fn, version, writefunc, #contents,
#         warnings, messages, do_add=True):
#    # returns tuple: (repo, saveok, gitok)
#    gitok = False
#    repo = None
#    absfn = os.path.abspath(fn)
#    try:
#        print("check git for <%s>" % fn)
#        repo = git.Repo(os.path.dirname(fn), search_parent_directories=True)
#        #print("ZZZZ", fn, repo.untracked_files, repo.working_tree_dir)
#
#        for utf in repo.untracked_files:
#            absutf = os.path.join(repo.working_tree_dir, utf)
#            #print(absfn, absutf)
#            if absfn == absutf:
#                raise FileNotGitControlled("%s not controlled by git" % fn)
#        gitok = True
#
#        # file versioned under git, we overwrite the input file
#        print("writing orig")
#        ofp = open(fn, "w")
#    except (git.exc.InvalidGitRepositoryError, FileNotGitControlled) as e:
#        print("no git repo", e)
#        # file not versioned, we write a new file
#        try:
#            ofp = open(fn + "." + version, "w")
#        except Exception as e:
#            print("cannot write %s" % fn, e)
#            warnings.append("cannot write %s: %s. File not saved" % (fn, e))
#            return repo, 0, False
#
#    #print(contents, file=ofp)
#    writefunc(ofp)
#    print("%s written (git: %s)" % (ofp.name, gitok))
#    messages.append("%s written (git: %s)" % (ofp.name, gitok))
#    ofp.close()
#
#    if gitok:
#        if not do_add:
#            return repo, 1, False
#        #rtc = repo.git.status()
#        try:
#            #rtc = repo.git.diff(os.path.basename(fn))
#            rtc = repo.git.diff(absfn)
#            #print("RTC", rtc)
#            if rtc:
#                rtc = repo.git.add(absfn)
#                #rtc = repo.git.add(fn)
#                atleastonegitok = True
#                #rtc = repo.git.commit("-m", "metamorphosed coref editor: %s of '%s' saved" % (", ".join(modified), fn), author=self.author)
#                #print("commited %s" % (fn), rtc)
#                return repo, 1, True
#            else:
#                print("nothing to add for %s" % (fn), rtc)
#                return repo, 1, False
#        except Exception as e:
#            print("COMMIT Error <%s> <%s> <%s>" % (e, fn, rtc))
#            warnings.append("commit error <%s> <%s> <%s>" % (e, fn, rtc))
#            return repo, 1, False
#    return repo, 1, False


class FileNotGitControlled(Exception):
    def __init__(self, value=""):
        self.value = value

    def __str__(self):
        return repr(self.value)
