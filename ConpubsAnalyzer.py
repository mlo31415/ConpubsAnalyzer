from __future__ import annotations
from typing import Optional, List, Union

import json

from ConSeries import ConSeriesPage
from FTP import FTP
from ConpubsCounts import ConpubsCounts

from HelpersPackage import FindBracketedText
from Log import LogOpen, Log


class Convention:
    def __init__(self):
        self._name: str=""      # The name of the convention series


    def FromJson(self, val: str) -> Convention:
        d=json.loads(val)
        self._name=d["_name"]
        # self._URL=d["_URL"]

        return self


class ConList():
    _element=Convention

    def __init__(self):
        self._conlist: List[Convention]=[]

    # -----------------------------
    def FromJson(self, val: str) -> ConList:
        d=json.loads(val)
        self._conlist=[]
        i=0
        while str(i) in d.keys():       # Using str(i) is because json merges 1 and "1" as the same. (It appears to be a bug.)
            self._conlist.append(Convention().FromJson(d[str(i)]))
            i+=1
        return self


###############################################################################
###############################################################################

LogOpen("Log -- ConpubsAnalyzer.txt", "Log (Errors) -- ConpubsAnalyzer.txt")

f=FTP()
if not f.OpenConnection("FTP Credentials.json"):
    Log("Main: OpenConnection('FTP Credentials.json' failed")
    exit(0)

Log("Loading root/index.html")
file=FTP().GetFileAsString("", "index.html")
if file is None:
    assert (False)

# Get the JSON
j=FindBracketedText(file, "fanac-json")[0]
if j is None or j == "":
    Log("Can't find convention information json in conpubs' index.html")
    exit(0)

listOfConSeries=[]
try:
    d=json.loads(j)
    listOfConSeries=ConList().FromJson(d["_datasource"])
except (json.decoder.JSONDecodeError):
    Log("JSONDecodeError when loading convention information from conpubs' index.html")
    exit(0)

# Walk the list of ConSeries, loading each in turn
cpc=ConpubsCounts()
csplist: List[ConpubsCounts]=[]
for row in listOfConSeries._conlist:
    csp=ConSeriesPage(row._name)
    counts=csp.Counts()
    counts.title=row._name
    csplist.append(counts)
    cpc+=counts

Log("\n\n")
for csp in csplist:
    Log(str(csp))

Log(str(cpc))
Log("\nGrand Total: "+cpc.Debug(), isError=True)
