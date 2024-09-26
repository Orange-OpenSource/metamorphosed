#!/usr/bin/env python3

# needed only to install the jquery libraries
import os
import sys
import zipfile

import requests

FILES = [("https://code.jquery.com/jquery-3.6.0.min.js", "jquery-3.6.0.min.js", False),
         ("https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.js", "jquery.modal-0.9.2.min.js", False),
         ("https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.css", "jquery.modal-0.9.2.min.css", False),
         ("https://jqueryui.com/resources/download/jquery-ui-1.13.2.zip", "jquery-ui-1.13.2.zip", True)
         ]


def installjq(url, fn, force=False, onlycheck=False):
    ok = os.path.isfile(fn)
    if onlycheck:
        return ok

    if ok:
        print("** file %s exists" % fn, file=sys.stderr)

        if not force:
            print("** ignoring %s " % url, file=sys.stderr)
            return False
    print("** downloading %s into %s" % (url, fn), file=sys.stderr)
    r = requests.get(url)
    f = open(fn, "wb")
    f.write(r.content)
    f.close()
    return True


def extractzip(fn, outdir):
    print("** extracting %s into %s" % (fn, outdir), file=sys.stderr)
    with zipfile.ZipFile(fn, 'r') as zip_ref:
        zip_ref.extractall(outdir)


def checkLibraries():
    mydir = os.path.dirname(__file__)
    guipath = os.path.join(mydir, "gui", "lib")

    for (url, target, unzip) in FILES:
        rtc = installjq(url, os.path.join(guipath, target), onlycheck=True)
        if not rtc:
            return False
    return True


def install():
    mydir = os.path.dirname(__file__)
    guipath = os.path.join(mydir, "gui", "lib")
    os.makedirs(guipath, exist_ok=True)

    #installjq("https://code.jquery.com/jquery-3.6.0.min.js", os.path.join(guipath, "jquery-3.6.0.min.js"))
    #installjq("https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.js", os.path.join(guipath, "jquery.modal-0.9.2.min.js"))
    #installjq("https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.css", os.path.join(guipath, "jquery.modal-0.9.2.min.css"))
    #rtc = installjq("https://jqueryui.com/resources/download/jquery-ui-1.13.2.zip", os.path.join(guipath, "jquery-ui-1.13.2.zip"))
    #if rtc:
    #    extractzip(os.path.join(guipath, "jquery-ui-1.13.2.zip"), guipath)
    for (url, target, unzip) in FILES:
        rtc = installjq(url, os.path.join(guipath, target))
        if unzip and rtc:
            extractzip(os.path.join(guipath, target), guipath)


if __name__ == "__main__":
    install()
